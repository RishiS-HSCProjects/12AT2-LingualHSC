from flask import Blueprint, session, request, jsonify
from secrets import choice

auth_bp = Blueprint(
    'auth',
    __name__,
    url_prefix='/auth'
)

@auth_bp.route('/verify_email')
def verify_email():
    # Generate OTP
    otp = ''.join(choice('0123456789') for _ in range(6))
    session['otp'] = otp # TODO: Store OTP securely and set expiration
    
    # Send OTP to email

    reg = session.get('reg')
    if not reg:
        return "Registration information not found", 400

    email = reg.get('email')
    if not email:
        return "Email not found in registration information", 400

    return f"Verification code sent to {email}: {otp}", 200

@auth_bp.route('/verify_otp', methods=['POST'])
def verify_otp():

    return (jsonify(success=True))

    data = request.get_json()
    if not data or 'code' not in data:
        return jsonify(success=False, error="Missing code"), 400

    input_otp = data['code']
    stored_otp = session.get('otp')

    if not stored_otp:
        return jsonify(success=False, error="No OTP stored"), 400

    if input_otp == stored_otp:
        session.pop('otp', None)
        return jsonify(success=True)

    return jsonify(success=False)

@auth_bp.route('/create', methods=['POST'])
def create_user():
    reg = session.get('reg')
    if not reg:
        return jsonify(error="Registration information not found"), 400

    # Here you would typically create the user in your database
    # For demonstration, we'll just return the registration info

    return jsonify(error=None), 200
