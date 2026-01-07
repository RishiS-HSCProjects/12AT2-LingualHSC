from threading import Thread
from flask import Blueprint, current_app, session, request, jsonify
from time import time
from werkzeug.security import generate_password_hash
from lingual.core.auth.utils.user_auth import deserialize_RegUser

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

    email = deserialize_RegUser(reg).email
    if not email:
        return jsonify({"error": "Email not found in registration information"}), 400
    from secrets import choice
    from bcrypt import hashpw, gensalt

    # Generate OTP
    # otp = ''.join(choice('0123456789') for _ in range(6))
    otp = "123456"  # For testing purposes

    session['otp'] = [hashpw(otp.encode(), gensalt()), time()]

    # def send_verification_email(app, email, otp):
    #     with app.app_context():
    #         from lingual import mail
    #         mail.send_message(
    #             subject=f"Your Verification Code is {otp}",
    #             recipients=[email],
    #             body=(
    #                 f"Your verification code is: {otp}.\n\n" \
    #                 "This code will expire in 5 minutes. " \
    #                 "If you did not request this code, please ignore this email."
    #             )
    #         )

    # try:
    #     Thread(
    #         target=send_verification_email,
    #         args=(current_app._get_current_object(), email, otp), # type: ignore
    #         daemon=True
    #     ).start()
    # except Exception as e:
    #     current_app.logger.error(f"Error when sending verification email: {e}")
    #     return jsonify({"error": "Something went wrong when sending the verification code."}), 400

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
    reg = session.pop('reg_user', None)
    if not reg:
        return jsonify({"error": "Registration information not found"}), 400
    
    from lingual import db

    try:
        new_user = deserialize_RegUser(reg).build_user()
        new_user.set_password(request.json.get('password'))
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"error": None}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
