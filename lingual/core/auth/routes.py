from threading import Thread
from flask import Blueprint, current_app, session, request, jsonify
from time import time
from werkzeug.security import generate_password_hash

auth_bp = Blueprint(
    'auth',
    __name__,
    url_prefix='/auth'
)

@auth_bp.route('/verify_email', methods=['POST'], strict_slashes=False)
def verify_email():
    reg = session.get('reg')
    if not reg:
        return jsonify({"error": "Registration information not found"}), 400

    email = reg.get('email')
    if not email:
        return jsonify({"error": "Email not found in registration information"}), 400
    from secrets import choice
    from bcrypt import hashpw, gensalt
    from lingual import mail

    # Generate OTP
    otp = ''.join(choice('0123456789') for _ in range(6))

    session['otp'] = [hashpw(otp.encode(), gensalt()), time()]

    def send_verification_email(app, email, otp):
        with app.app_context():
            from lingual import mail
            mail.send_message(
                subject=f"Your Verification Code is {otp}",
                recipients=[email],
                body=(
                    f"Your verification code is: {otp}.\n\n"
                    "This code will expire in 5 minutes."
                )
            )

    Thread(
        target=send_verification_email,
        args=(current_app._get_current_object(), email, otp),
        daemon=True
    ).start()

    return jsonify({"error": None}), 200

def verify_otp(otp_code: str) -> str | None:
    """    
    :return: Error message if verification fails, None if successful
    :rtype: str | None
    """
    from bcrypt import checkpw

    otp_data = session.get('otp')

    if not otp_data:
        return "OTP data not found"
    
    if time() - otp_data[1] > 300:
        return "OTP has expired. Please request a new one."

    if checkpw(otp_code.encode(), otp_data[0]):
        return None

    return "Invalid verification code"

@auth_bp.route('/create', methods=['POST'])
def create_user():
    reg = session.pop('reg', None)
    
    if not reg:
        return jsonify({"error": "Registration information not found"}), 400
    
    from lingual import db
    from lingual.models import User

    new_user = User(
        first_name=reg['first_name'],
        last_name=reg['last_name'],
        email=reg['email'],
        password_hash=generate_password_hash(request.get_json().get('password'))
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"error": None}), 200
