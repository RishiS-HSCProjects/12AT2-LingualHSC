from flask import Blueprint, current_app, redirect, session, request, jsonify, url_for, flash
from time import time
from lingual.utils.mail_utils import EmailError
from lingual.core.auth.utils.user_auth import RegNotFoundException, RegUserValueException, deserialize_RegUser
from lingual.models import User
from lingual.utils.form_manager import validate_ajax_form, FormValidationError
from lingual.utils.url_builder import build_external_url
from functools import wraps

auth_bp = Blueprint(
    'auth',
    __name__,
    url_prefix='/auth'
)

def validate_reg_user():
    def wrapper(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            reg = session.get('reg_user')
            if not reg:
                flash(
                    "Registration information not found. Please try registering again.",
                    "error"
                )
                return redirect(url_for('main.register'))

            kwargs['reg'] = reg
            return func(*args, **kwargs)
        return decorated_function
    return wrapper

@auth_bp.route('/verify_email', methods=['POST'], strict_slashes=False)
@validate_reg_user()
def verify_email(reg = None):
    # Decorator ensures reg is present
    try:
        send_verification_email(reg)
    except EmailError.EmailSendingDisabled as e:
        return jsonify({"error": str(e)}), 200
    except RegNotFoundException as e:
        return jsonify({"error": str(e)}), 400
    except EmailError.Base as e:
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Unexpected error when sending verification code: {e}")
        return jsonify({"error": "Something went wrong when sending the verification code."}), 400

    return jsonify({"error": None}), 200

def prepare_otp(reg: dict | None) -> tuple[str, str]:
    """Validate registration state and prepare OTP data for verification email."""
    if not reg:
        raise RegNotFoundException()

    try:
        email = deserialize_RegUser(reg).email # Deserialize session data to get RegUser object and access email
    except RegUserValueException as e:
        raise RegNotFoundException(str(e)) from e
    except Exception as e:
        current_app.logger.error(f"Error deserializing RegUser for email verification: {e}\nReg: {reg}")
        raise RegNotFoundException("Registration information corrupted. Please try again.") from e
    
    # Generate OTP
    from bcrypt import hashpw, gensalt #
    ALLOW_SEND_EMAILS = current_app.config.get('ALLOW_SEND_EMAILS', True) # Default to true for security reasons
    if not ALLOW_SEND_EMAILS: # For testing, ALLOW_SEND_EMAILS may be disabled.
        otp = "123456"
    else:
        # Create secure, random OTP generation.
        # secrets module is used since it is designed for cryptographic security.
        # Overkill for this task? yes. But, this is the best practice if this were production code.
        # Using secrets.choice has minor performance implications compared to random().
        from secrets import choice
        otp = ''.join(choice('0123456789') for _ in range(6)) # 6-digit numeric OTP

    # D-AE01
    # Store the OTP in the session (hashed)
    session['otp'] = [hashpw(otp.encode(), gensalt()).decode('utf-8'), time()] # Using same hashing system for OTPs as passwords.

    return email, otp # Return packaged tuple of required data

def send_verification_email(reg: dict | None) -> None:
    """Queue OTP email sending.

    Raises typed exceptions for validation/config/send failures so callers can
    handle errors consistently in routes/utilities.
    """

    email, otp = prepare_otp(reg) # May raise RegNotFoundException or EmailError.SMTPConfig

    from lingual.utils.mail_utils import queue_email
    queue_email(
        recipients=[email],
        subject=f"Your Verification Code is {otp}",
        body=(
            f"Your verification code is: {otp}.\n\n"
            "This code will expire in 5 minutes. "
            "If you did not request this code, please ignore this email."
        )
    )

def verify_otp(otp_code: str) -> str | None:
    """    
    :return: Error message if verification fails, None if successful
    :rtype: str | None
    """

    # T-FE02

    # Retrieve OTP data from session
    otp_data = session.get('otp', None)

    if not otp_data: # No OTP data found in session. 
        return "OTP data not found"
        
    # Separate const created for clarity.    
    OTP_EXPIRY_SECONDS = 5 * 60 # 5 minutes
    
    if time() - otp_data[1] > OTP_EXPIRY_SECONDS:
        return "OTP has expired. Please request a new one."

    from bcrypt import checkpw # Use bcrypt's checkpw to compare hashed OTPs
    if checkpw(otp_code.encode(), otp_data[0].encode('utf-8')):
        session.pop('otp', None) # Remove OTP from session upon successful verification
        return None # None indicates success

    return "Invalid verification code" # Return error message if verification fails. 

@auth_bp.route('/create', methods=['POST'])
@validate_reg_user()
def create_user(reg = None):
    if not reg: # Decorator ensures reg is present
        return jsonify({"error": "Registration information not found."}), 400

    from lingual import db
    from lingual.core.auth.forms import UserCreationForm

    try:

        password = request.json.get('password') # Get password from AJAX request
        confirm_password = request.json.get('confirm_password')
        if not password or not confirm_password: # Exit early if no password provided. User can not be created without a password.
            return jsonify({"error": "Missing password"}), 400

        # Validate password using UserCreationForm
        success, error, form = validate_ajax_form(UserCreationForm, {'password': password, 'confirm_password': confirm_password})
        if not success:
            # No need to repopulate form for AJAX request
            return jsonify({"error": error}), 400

        reg_user = deserialize_RegUser(reg)

        # Check for duplicate accounts
        existing = User.query.filter_by(email=reg_user.email.lower()).first()
        if existing:
            # In theory, this should never happen due to earlier validation.
            # If this does occur, it indicates a serious issue in the registration flow.
            # As a result, we need to log this event for further investigation.
            current_app.logger.error(f"Duplicate account creation attempt for email: {reg_user.email}")

            # We also need to inform the user that their attempt failed.
            return jsonify({"error": "An account with that email already exists."}), 400

        user = reg_user.build_user() # Build User object and set password
        user.set_password(password)  # Set password
        # Add new user to the database and commit
        db.session.add(user)

        if reg_user.language:
            db.session.flush() # Ensure user.id is available before creating stats
            user.create_language_stats(reg_user.language)

        db.session.commit()

        current_app.logger.info(f"User created: {user.email}") # Log user creation event
        flash("Account created successfully! You can now log in.", "success")

        session['new_user'] = True

        return jsonify({"error": None}), 200 # Success
    except FormValidationError as e:
        current_app.logger.error(f"Form validation error creating user: {e}\nReg: {reg}")
        return jsonify({"error": str(e.message)}), 400
    except Exception as e:
        db.session.rollback() # Rollback in case of error during DB operations. This prevents partial commits and maintains database integrity.
        current_app.logger.error(f"Unexpected error creating user: {e}\nReg: {reg}") # Log detailed error
        return jsonify({"error": f"An unexpected error occurred."}), 500 # 500 Internal Server Error

def send_password_reset_email(user: 'User'):
    """Send a password reset email to the specified user."""
    from lingual.utils.mail_utils import queue_email

    reset_link = build_external_url('main.reset_token', token=user.get_reset_token())
    queue_email(
        recipients=[user.email],
        subject="Password Reset Request",
        body=(
            f"To reset your password, visit the following link: {reset_link}\n\n"
            "This link will expire in 30 minutes.\n\n"
            "If you did not make this request, simply ignore this email."
        )
    )
