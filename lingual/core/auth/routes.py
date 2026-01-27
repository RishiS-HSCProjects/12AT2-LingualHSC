from flask import Blueprint, current_app, redirect, session, request, jsonify, url_for, flash
from time import time
from lingual.core.auth.utils.exceptions import EmailSendingDisabledException
from lingual.core.auth.utils.user_auth import RegUserValueException, deserialize_RegUser
from lingual.models import User
from threading import Thread
from lingual.utils.form_manager import validate_ajax_form, FormValidationError

auth_bp = Blueprint(
    'auth',
    __name__,
    url_prefix='/auth'
)

def validate_reg_user():
    def wrapper(func):
        """Decorator to ensure registration info is in session."""
        def decorated_function(*args, **kwargs):
            reg = session.get('reg_user')
            if not reg:
                # Reg info not found in session
                flash("Registration information not found. Please try registering again.", "error")
                return redirect(url_for('main.register'))

            kwargs['reg'] = reg # Pass reg to the decorated function
            return func(*args, **kwargs) # Call initial function with reg kwarg
        return decorated_function
    return wrapper

@validate_reg_user()
@auth_bp.route('/verify_email', methods=['POST'], strict_slashes=False)
def verify_email(reg = None):
    # Decorator ensures reg is present
    if not reg:
        flash("Registration information not found. Please try registering again.", "error")
        return redirect(url_for('main.register'))

    try:
        email = deserialize_RegUser(reg).email # Deserialize session data to get RegUser object and access email
    except RegUserValueException as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error deserializing RegUser for email verification: {e}\nReg: {reg}") # Log detailed error
        flash("Registration information corrupted. Please try registering again.", "error") # Send user friendly message
        return redirect(url_for('main.register')) # Redirect to registration page

    from bcrypt import hashpw, gensalt
    # Generate OTP
    VERIFY_REQ = current_app.config.get('ALLOW_SEND_EMAILS', True)
    if not VERIFY_REQ: # For testing, ALLOW_SEND_EMAILS may be disabled.
        otp = "123456"
    else:
        # Create secure, random OTP generation. 
        # secrets module is used since it is designed for cryptographic security.
        # Overkill for this task? yes. But, this is the best practice if this were production code.
        # Using secrets.choice has minor performance implications compared to random().
        from secrets import choice 
        otp = ''.join(choice('0123456789') for _ in range(6)) # 6-digit numeric OTP

    # Store the OTP in the session (hashed)
    # Session is not the most secure place to store sensitive data like this, which is why we hash it.
    # Session also stores time of generation to enforce expiry.
    # However, that value can easily be tampered with by the user.
    # In production, a more secure storage mechanism should be used (e.g., server-side database with proper security measures).
    # That approach may be considered later on, however, this is sufficient for the current application's scope.
    # Note will be made if this system is improved.

    # Documented on 27 Jan 2026

    session['otp'] = [hashpw(otp.encode(), gensalt()), time()]

    # Exit early if email verification is not required
    if not VERIFY_REQ:
        return jsonify({"error": None}), 200

    # If email verification is required, send the OTP email
    def send_verification_email(app, email, otp):
        with app.app_context():
            from lingual import mail
            mail.send_message(
                subject=f"Your Verification Code is {otp}",
                recipients=[email],
                body=(
                    f"Your verification code is: {otp}.\n\n"
                    "This code will expire in 5 minutes. "
                    "If you did not request this code, please ignore this email."
                )
            )

    try:
        # Initially, send_verification_email was called without all of this threading logic.
        # However, sending emails synchronously led to the entire application halting while waiting for the email to send.
        # This can be confusing for users, as they may think the application is unresponsive (even though it is just waiting for the email to send).
        # As a result, I explored async options that allow for the email to be sent in the background.
        # While this approach will result in the email potentially arriving slightly later, users will know an email will arrive eventually and not think the application is broken.

        Thread(
            target=send_verification_email, # Anonymously call send_verification_email
            args=(current_app._get_current_object(), email, otp), # type: ignore
            daemon=True # Makes asynchronous to not halt application flow while sending email
        ).start()
    except Exception as e:
        current_app.logger.error(f"Error when sending verification email: {e}") # Log detailed error in server logs to prevent sensitive information being leaked to the browser's console.
        return jsonify({"error": "Something went wrong when sending the verification code."}), 400 # Return generic error

    return jsonify({"error": None}), 200 # Success 200 OK ("I always wanted to use that spell" - Prof. McGonagall 2011)

def verify_otp(otp_code: str) -> str | None:
    """    
    :return: Error message if verification fails, None if successful
    :rtype: str | None
    """

    from bcrypt import checkpw # Use bcrypt's checkpw to compare hashed OTPs

    # Retrieve OTP data from session
    # This function initially popped the OTP data from the session.
    # However, this caused issues if the user mistakenly entered an incorrect OTP, as they would have to request a new OTP each time.
    # Now, the OTP data is only removed from the session upon successful verification.
    # While this may have minor security implications (e.g., if someone else gains access to the session), it greatly improves user experience.
    # In the event OTP logic is moved to a separate database, this security concern can be better addressed.
    # As mentioned previously, documentation will be added if this system is improved.

    # Documented on 27 Jan 2026
    otp_data = session.get('otp', None)

    if not otp_data: # No OTP data found in session. 
        return "OTP data not found"
        
    # Separate const created for clarity.    
    OTP_EXPIRY_SECONDS = 5 * 60 # 5 minutes
    
    if time() - otp_data[1] > OTP_EXPIRY_SECONDS:
        return "OTP has expired. Please request a new one."

    if checkpw(otp_code.encode(), otp_data[0]):
        session.pop('otp', None) # Remove OTP from session upon successful verification
        return None # None indicates success

    return "Invalid verification code" # Return error message if verification fails. 

@validate_reg_user()
@auth_bp.route('/create', methods=['POST'])
def create_user(reg = None):
    if not reg: # Decorator ensures reg is present
        return jsonify({"error": "Registration information not found."}), 400

    from lingual import db
    from lingual.models import User
    from lingual.core.auth.forms import UserCreationForm

    try:
        new_user = deserialize_RegUser(reg)

        password = request.json.get('password') # Get password from AJAX request
        confirm_password = request.json.get('confirm_password')
        if not password or not confirm_password: # Exit early if no password provided. User can not be created without a password.
            return jsonify({"error": "Missing password"}), 400

        # Validate password using UserCreationForm
        success, error, form = validate_ajax_form(UserCreationForm, {'password': password, 'confirm_password': confirm_password})
        if not success:
            # No need to repopulate form for AJAX request
            return jsonify({"error": error}), 400

        # Check for duplicate accounts
        existing = User.query.filter_by(email=new_user.email.lower()).first()
        if existing:
            # In theory, this should never happen due to earlier validation.
            # If this does occur, it indicates a serious issue in the registration flow.
            # As a result, we need to log this event for further investigation.
            current_app.logger.error(f"Duplicate account creation attempt for email: {new_user.email}")

            # We also need to inform the user that their attempt failed.
            return jsonify({"error": "An account with that email already exists."}), 400

        new_user.set_password(password)
        # Add new user to the database and commit
        db.session.add(new_user)
        db.session.commit()

        current_app.logger.info(f"User created: {new_user.email}") # Log user creation event
        return jsonify({"error": None}), 200 # Success
    except FormValidationError as e:
        current_app.logger.error(f"Form validation error creating user: {e}\nReg: {reg}")
        return jsonify({"error": str(e.message)}), 400
    except Exception as e:
        db.session.rollback() # Rollback in case of error during DB operations. This prevents partial commits and maintains database integrity.
        current_app.logger.error(f"Unexpected error creating user: {e}\nReg: {reg}") # Log detailed error
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500 # 500 Internal Server Error

def send_password_reset_email(user: 'User'):
    """Send a password reset email to the specified user."""
    if current_app.config.get('ALLOW_SEND_EMAILS', True) is False:
        raise EmailSendingDisabledException() # Email sending is disabled in config

    def send_verification_email(app, email, token):
        with app.app_context():
            from lingual import mail
            mail.send_message(
                subject="Password Reset Request",
                recipients=[email],
                body=(
                    f"To reset your password, visit the following link: {url_for('main.reset_token', token=token, _external=True)}\n\n"
                    "This link will expire in 30 minutes.\n\n"
                    "If you did not make this request, simply ignore this email."
                )
            )

    try:
        # Send password reset email asynchronously
        # Refer to comments in verify_email for reasoning behind asynchronous email sending.
        Thread(
            target=send_verification_email,
            args=(current_app._get_current_object(), user.email, user.get_reset_token()),  # type: ignore
            daemon=True # Makes asynchronous to not halt application flow while sending email
        ).start()
    except EmailSendingDisabledException: # Handle case where email sending is disabled
        current_app.logger.warning(f"Email sending is disabled. Skipping password reset email for user: {user.email}")
        return jsonify({"error": "Email sending is currently disabled."}), 400
    except Exception as e: # Catch all other exceptions
        current_app.logger.error(f"Error when sending password reset email: {e}\nUser: {user.email}")
        return jsonify({"error": "Something went wrong when sending the password reset email."}), 400
