from flask import Blueprint, current_app, redirect, session, request, jsonify, url_for, flash
from time import time
from lingual.core.auth.utils.exceptions import (
    EmailSendingDisabledException,
    VerificationEmailError,
)
from lingual.core.auth.utils.user_auth import RegUserValueException, deserialize_RegUser
from lingual.models import User
from threading import Thread
from queue import Empty, Queue
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
        queue_verification_email(reg)
    except EmailSendingDisabledException as e:
        return jsonify({"error": str(e)}), 200
    except VerificationEmailError.Base as e:
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Unexpected error when sending verification code: {e}")
        return jsonify({"error": "Something went wrong when sending the verification code."}), 400

    return jsonify({"error": None}), 200

def prepare_otp(reg: dict | None) -> tuple[str, str, bool]:
    """Validate registration state and prepare OTP data for verification email."""
    if not reg:
        raise VerificationEmailError.NoReg()

    try:
        email = deserialize_RegUser(reg).email # Deserialize session data to get RegUser object and access email
    except RegUserValueException as e:
        raise VerificationEmailError.NoReg(str(e)) from e
    except Exception as e:
        current_app.logger.error(f"Error deserializing RegUser for email verification: {e}\nReg: {reg}") # Log detailed error
        raise VerificationEmailError.NoReg("Registration information corrupted. Please try again.") from e # Raise dedicated exception, chaining the original 'e'

    from bcrypt import hashpw, gensalt
    # Generate OTP
    VERIFY_REQ = current_app.config.get('ALLOW_SEND_EMAILS', True) # Default to true for security reasons
    if not VERIFY_REQ: # For testing, ALLOW_SEND_EMAILS may be disabled.
        otp = "123456"
    else:
        # Validate required config before attempting to send OTP emails.
        if not current_app.config.get('MAIL_DEFAULT_SENDER'):
            raise VerificationEmailError.SMTPConfig("Email service is not configured correctly. Missing default sender.")

        # Create secure, random OTP generation.
        # secrets module is used since it is designed for cryptographic security.
        # Overkill for this task? yes. But, this is the best practice if this were production code.
        # Using secrets.choice has minor performance implications compared to random().
        from secrets import choice
        otp = ''.join(choice('0123456789') for _ in range(6)) # 6-digit numeric OTP

    # D-AE01
    # Store the OTP in the session (hashed)
    session['otp'] = [hashpw(otp.encode(), gensalt()), time()] # Using same hashing system for OTPs as passwords.

    return email, otp, VERIFY_REQ # Return packaged tuple of required data

def queue_verification_email(reg: dict | None) -> None:
    """Queue OTP email sending.

    Raises typed exceptions for validation/config/send failures so callers can
    handle errors consistently in routes/utilities.
    """
    email, otp, VERIFY_REQ = prepare_otp(reg)

    # Exit early if email verification is not required
    if not VERIFY_REQ:
        raise EmailSendingDisabledException("Mail Service Disabled. OTP defaulted to 123456.")

    # If email verification is required, send the OTP email
    send_result_queue: Queue[VerificationEmailError.SendFailure | None] = Queue(maxsize=1) # Capture one async result/error.

    def send_otp_email(app, email, otp, result_queue: Queue[VerificationEmailError.SendFailure | None]):
        """Prepare and send an OTP email in a background thread."""
        try:
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
                result_queue.put_nowait(None)
        except Exception as e:
            app.logger.error(f"Threaded email send failed for {email}: {e}")
            try:
                result_queue.put_nowait(VerificationEmailError.SendFailure("Unable to send verification email. Check your internet connection and try again."))
            except Exception:
                pass

    try:
        Thread(
            target=send_otp_email, # Anonymously call send_otp_email
            args=(current_app._get_current_object(), email, otp, send_result_queue), # type: ignore -> Pass required values into async worker.
            daemon=True # Makes asynchronous to not halt application flow while sending email
        ).start()
    except Exception as e:
        current_app.logger.error(f"Error when starting verification email thread: {e}")
        raise VerificationEmailError.SendFailure("Something went wrong when sending the verification code.") from e

    # Briefly wait for fast failures; otherwise continue asynchronously.
    wait_seconds = current_app.config.get('ASYNC_EMAIL_ERROR_WAIT_SECONDS', 1.5)
    if wait_seconds > 0: # Only attempt to wait if configured to do so. (set in Config.)
        try:
            thread_error = send_result_queue.get(timeout=wait_seconds)
            if thread_error:
                raise thread_error
        except Empty: # Exception raised when no result is available within wait time.
            # No result from thread within wait time.
            # This is not necessarily an error, as email sending can be slow.

            # Log this occurrence for monitoring but proceed without raising an exception, allowing the email sending to continue asynchronously.
            current_app.logger.warning(f"No result from email thread after {wait_seconds} seconds for {email}. Proceeding without confirmation of email send success.")
            pass

    return None # Explicitly return None on success for clarity

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
    if checkpw(otp_code.encode(), otp_data[0]):
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
    if current_app.config.get('ALLOW_SEND_EMAILS', True) is False:
        raise EmailSendingDisabledException() # Email sending is disabled in config

    def send_verification_email(app, email, token):
        with app.app_context():
            from lingual import mail
            reset_link = build_external_url('main.reset_token', token=token)
            mail.send_message(
                subject="Password Reset Request",
                recipients=[email],
                body=(
                    f"To reset your password, visit the following link: {reset_link}\n\n"
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
