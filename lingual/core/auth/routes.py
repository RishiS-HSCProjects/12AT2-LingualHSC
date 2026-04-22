from flask import Blueprint, current_app, redirect, session, request, jsonify, url_for, flash
from time import time
from lingual.utils.mail_utils import EmailError
from lingual.core.auth.utils.user_auth import RegNotFoundException, RegUserValueException, deserialize_RegUser
from lingual.models import User
from lingual.utils.form_manager import validate_ajax_form, FormValidationError
from lingual.utils.url_builder import build_external_url
from functools import wraps

# Blueprint for auth routes
auth_bp = Blueprint(
    'auth',
    __name__,
    url_prefix='/auth'
)

def validate_reg_user():
    """ Decorator function to validate presence of 'reg_user' in session
        when required. Passes through deserialized RegUser object to route to avoid re-fetching
        within the decorated route.
    """
    def wrapper(func):
        @wraps(func) # Preserve original function metadata for better debugging and introspection.
        def decorated_function(*args, **kwargs):
            reg = session.get('reg_user') # Attempt to retrieve 'reg_user' from session. This should have been set during the registration process.
            # A missing 'reg_user' indicates a problem in the registration flow, such as session expiration or a user trying to access the route directly without going through registration.
            # In either case, we need to handle this gracefully by informing the user and redirecting them back to the registration page.
            if not reg:
                flash(
                    "Registration information not found. Please try registering again.",
                    "error"
                )
                return redirect(url_for('main.register')) # Redirect to registration page to restart the registration process and obtain valid session and 'reg_user' data.

            kwargs['reg'] = reg # Attach reg data to kwargs for use in the decorated route to avoid redundant session access and deserialization in the route itself.
            return func(*args, **kwargs) # Call original route
        return decorated_function # Return decorated function to wrapper
    return wrapper # Return wrapper to be used as a decorator

@auth_bp.route('/verify_email', methods=['POST'], strict_slashes=False)
@validate_reg_user()
def verify_email(reg = None):
    """ Route to send verification email with OTP code. """
    # Decorator ensures reg is present
    try:
        send_verification_email(reg) # Attempt to send verification email
    except EmailError.EmailSendingDisabled as e: # Handle email sending disabled error
        return jsonify({"error": str(e)}), 200 # Expected error due to config, 200 OK
    except RegNotFoundException as e: # Handle registration not found error
        return jsonify({"error": str(e)}), 400 # Bad Request, informs user of issue with their registration state
    except EmailError.Base as e:
        return jsonify({"error": str(e)}), e.status_code # Handle other email-related errors with appropriate status code
    except Exception as e:
        # Log unexpected errors with detailed information for debugging, but return a generic error message to the user to avoid exposing internal details.
        current_app.logger.error(f"Unexpected error when sending verification code: {e}") # Log detailed error for debugging
        return jsonify({"error": "Something went wrong when sending the verification code. If the problem continues, please refresh your page and try again."}), 400 # Return generic error message to user. Encourages user to try again.

    return jsonify({"error": None}), 200

def prepare_otp(reg: dict | None) -> tuple[str, str]:
    """Validate registration state and prepare OTP data for verification email."""
    if not reg:
        raise RegNotFoundException()

    try:
        email = deserialize_RegUser(reg).email # Deserialize session data to get RegUser object and access email
    except RegUserValueException as e:
        raise RegNotFoundException(str(e)) from e # Extend original exception for traceback, but raise RegNotFoundException to maintain consistent error handling for registration issues.
    except Exception as e:
        # Log unexpected deserialization errors with detailed information for debugging, but raise a generic error to be handled by the caller to avoid exposing internal details.
        current_app.logger.error(f"Error deserializing RegUser for email verification: {e}\nReg: {reg}")
        raise RegNotFoundException("Registration information corrupted. Please try again.") from e # Extend original exception for traceback
    
    # Generate OTP
    from bcrypt import hashpw, gensalt # Use bcrypt for secure storage of OTPs in session
    ALLOW_SEND_EMAILS = current_app.config.get('ALLOW_SEND_EMAILS', True) # Default to true for security reasons
    if not ALLOW_SEND_EMAILS: # For testing, ALLOW_SEND_EMAILS may be disabled.
        otp = "123456" # Default OTP for testing when email sending is disabled
    else:
        # Create secure, random OTP generation.
        from secrets import choice # Generate cryptographically secure OTP
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

    from lingual.utils.mail_utils import queue_email # Get email queuing function to send OTP email asynchronously
    queue_email( # Add email to queue
        recipients=[email],
        subject=f"Your Lingual HSC Verification Code",
        body=(
            f"Your verification code is: {otp}.\n\n"
            "This code will expire in 5 minutes. "
            "If you did not request this code, please ignore this email."
        )
    )

def verify_otp(otp_code: str) -> str | None:
    """
    :return: User friendly error message if verification fails, None if successful
    :rtype: str | None
    """

    # T-FE02

    # Retrieve OTP data from session
    otp_data = session.get('otp', None)

    if not otp_data: # No OTP data found in session. 
        return "OTP data not found"

    OTP_EXPIRY_SECONDS = 5 * 60 # 5 minutes
    
    if time() - otp_data[1] > OTP_EXPIRY_SECONDS:
        return "OTP has expired. Please request a new one."

    from bcrypt import checkpw # Use bcrypt's checkpw to compare hashed OTPs
    if checkpw(otp_code.encode(), otp_data[0].encode('utf-8')): # Encode user input and stored hash for comparison (safer than decoding stored hash)
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
            # Check not necessary, since this should be caught by form validation, but we include this just in case.
            return jsonify({"error": "Missing password"}), 400 # Bad Request, informs user of missing required field. 

        # Validate password using UserCreationForm
        success, error, form = validate_ajax_form(UserCreationForm, {'password': password, 'confirm_password': confirm_password})
        if not success:
            # No need to repopulate form for AJAX request
            return jsonify({"error": error}), 400

        reg_user = deserialize_RegUser(reg) # Deserialize session data to get RegUser object for user creation. This should not fail since we validated reg_user presence with the decorator, but we include error handling just in case.

        # Check for duplicate accounts
        existing = User.query.filter_by(email=reg_user.email.lower()).first() # Find if any accounts under the same email exist
        if existing:
            # In theory, this should never happen due to earlier validation.
            # If this does occur, it indicates a serious issue in the registration flow.
            # As a result, we need to log this event for further investigation.
            current_app.logger.error(f"Duplicate account creation attempt for email: {reg_user.email}")

            # We also need to inform the user that their attempt failed.
            return jsonify({"error": "An account with that email already exists."}), 400

        user = reg_user.build_user() # Build User object and set password
        try:
            user.set_password(password)  # Set password (password encryption handled in model method)
        except ValueError as e:
            # This should not happen since we validated password strength in the form, but we include error handling just in case.
            return jsonify({"error": str(e)}), 400
        # Add new user to the database and commit
        db.session.add(user)

        # If user selected a language during registration, create initial stats for that language.
        if reg_user.language:
            db.session.flush() # Ensure user.id is available before creating stats
            user.create_language_stats(reg_user.language)

        db.session.commit() # Commit all changes to the database

        current_app.logger.info(f"User created: {user.email}") # Log user creation event
        flash("Account created successfully! You can now log in.", "success") # Flash success message to user

        session['new_user'] = True # Flag to indicate a new user has been created, used to trigger welcome flow after login

        return jsonify({"error": None}), 200 # Success
    except FormValidationError as e: # Handle form validation errors with detailed logging for debugging, but return user-friendly error messages to the client.
        current_app.logger.error(f"Form validation error creating user: {e}\nReg: {reg}")
        return jsonify({"error": str(e.message)}), 400
    except Exception as e: # Return generic error message for unexpected exceptions, but log detailed information for debugging. This prevents exposing internal details to the user while still allowing developers to investigate issues.
        db.session.rollback() # Rollback in case of error during DB operations. This prevents partial commits and maintains database integrity.
        current_app.logger.error(f"Unexpected error creating user: {e}\nReg: {reg}") # Log detailed error
        return jsonify({"error": f"An unexpected error occurred."}), 500 # 500 Internal Server Error

def send_password_reset_email(user: 'User'):
    """ Send a password reset email to the specified user. """
    from lingual.utils.mail_utils import queue_email # Import email queuing function to send password reset email asynchronously

    reset_link = build_external_url('main.reset_token', token=user.get_reset_token()) # Build external password reset link with token generated from user method.
    queue_email(
        recipients=[user.email],
        subject="Password Reset Request",
        body=(
            f"To reset your password, visit the following link: {reset_link}\n\n"
            "This link will expire in 30 minutes.\n\n"
            "If you did not make this request, simply ignore this email."
        )
    )
