from flask import Blueprint, current_app, redirect, session, request, jsonify, url_for, flash
from time import time
from lingual.core.auth.utils.user_auth import deserialize_RegUser
from lingual.models import User
from threading import Thread

auth_bp = Blueprint(
    'auth',
    __name__,
    url_prefix='/auth'
)

@auth_bp.route('/verify_email', methods=['POST'], strict_slashes=False)
def verify_email():
    reg = session.get('reg_user')
    if not reg:
        return jsonify({"error": "Registration information not found"}), 400

    try:
        email = deserialize_RegUser(reg).email
    except Exception as e:
        current_app.logger.error(f"Error deserializing RegUser for email verification: {e}")
        flash("Registration information corrupted. Please try registering again.", "error")
        return redirect(url_for('main.register'))

    if not email:
        return jsonify({"error": "Email not found in registration information"}), 400

    from bcrypt import hashpw, gensalt
    # Generate OTP
    VERIFY_REQ = current_app.config.get('ALLOW_SEND_EMAILS', True)
    if not VERIFY_REQ:
        otp = "123456"
    else:
        from secrets import choice
        otp = ''.join(choice('0123456789') for _ in range(6))

    # Store the OTP in the session (hashed)
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
        Thread(
            target=send_verification_email,
            args=(current_app._get_current_object(), email, otp),  # type: ignore
            daemon=True # Makes asyncronous to not halt application flow while sending email
        ).start()
    except Exception as e:
        current_app.logger.error(f"Error when sending verification email: {e}")
        return jsonify({"error": "Something went wrong when sending the verification code."}), 400

    return jsonify({"error": None}), 200

def verify_otp(otp_code: str) -> str | None:
    """    
    :return: Error message if verification fails, None if successful
    :rtype: str | None
    """
    from bcrypt import checkpw

    otp_data = session.get('otp', None)

    if not otp_data:
        return "OTP data not found"
    
    if time() - otp_data[1] > 300:
        return "OTP has expired. Please request a new one."

    if checkpw(otp_code.encode(), otp_data[0]):
        return None

    return "Invalid verification code"

@auth_bp.route('/create', methods=['POST'])
def create_user():
    reg = session.pop('reg_user', None)
    if not reg:
        return jsonify({"error": "Registration information not found"}), 400
    
    from lingual import db
    from lingual.models import User

    try:
        new_user = deserialize_RegUser(reg).build_user()

        password = request.json.get('password')
        if not password:
            return jsonify({"error": "Missing password"}), 400

        # Prevent creating duplicate accounts
        existing = User.query.filter_by(email=new_user.email.lower()).first()
        if existing:
            return jsonify({"error": "An account with that email already exists."}), 400

        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        current_app.logger.info(f"User created: {new_user.email}")
        return jsonify({"error": None}), 200
    except Exception as e:
        current_app.logger.error(f"Unexpected error creating user: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

def send_password_reset_email(user: 'User'):

    if current_app.config.get('ALLOW_SEND_EMAILS', True) is False:
        flash("Email sending is disabled.", "warning")
        return

    def send_verification_email(app, email, token):
        with app.app_context():
            from lingual import mail
            mail.send_message(
                subject="Password Reset Request",
                recipients=[email],
                body=(
                    f"To reset your password, visit the following link: {url_for('main.reset_token', token=token, _external=True)}\n\n"
                    "This link will expire in 5 minutes.\n\n"
                    "If you did not make this request, simply ignore this email."
                )
            )

    try:
        Thread(
            target=send_verification_email,
            args=(current_app._get_current_object(), user.email, user.get_reset_token()),  # type: ignore
            daemon=True # Makes asyncronous to not halt application flow while sending email
        ).start()
    except Exception as e:
        current_app.logger.error(f"Error when sending password reset email: {e}")
        return jsonify({"error": "Something went wrong when sending the password reset email."}), 400