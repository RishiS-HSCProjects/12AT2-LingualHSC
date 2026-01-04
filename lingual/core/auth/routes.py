from flask import Blueprint, current_app, session, request, jsonify
from time import time
from werkzeug.security import generate_password_hash

auth_bp = Blueprint(
    'auth',
    __name__,
    url_prefix='/auth'
)

@auth_bp.route('/verify_email')
def verify_email():
    reg = session.get('reg')
    if not reg:
        return "Registration information not found", 400

    email = reg.get('email')
    if not email:
        return "Email not found in registration information", 400

    from secrets import choice
    from bcrypt import hashpw, gensalt
    from lingual import mail

    # Generate OTP
    # otp = ''.join(choice('0123456789') for _ in range(6))
    otp = '123456'  # For testing purposes, use a fixed OTP. Replace with the above line in production.

    session['otp'] = [hashpw(otp.encode(), gensalt()), time()]

    # mail.send_message(
    #     subject=f"Your Verification Code is {otp}",
    #     recipients=[session.get('reg', {}).get('email')],
    #     body=f"Your verification code is: {otp}. This code will expire in 5 minutes. If you did not request this, please ignore this email."
    # )

    return jsonify(success=True)

@auth_bp.route('/verify_otp', methods=['POST'])
def verify_otp():
    from bcrypt import checkpw
    data = request.get_json()
    if not data or 'code' not in data:
        return jsonify(success=False), 400
    
    otp_data = session.get('otp')

    if not otp_data:
        return jsonify(success=False), 400
    
    if time() - otp_data[1] > 300:
        return jsonify(success=False), 400

    input_otp = data['code']

    if checkpw(input_otp.encode(), otp_data[0]):
        return jsonify(success=True)

    return jsonify(success=False)

@auth_bp.route('/create', methods=['POST'])
def create_user():
    reg = session.pop('reg', None)
    
    if not reg:
        return jsonify(error="Registration information not found"), 400
    
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

    return jsonify(error=None), 200
