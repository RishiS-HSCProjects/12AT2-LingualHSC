from flask import jsonify, render_template, request, session, current_app, flash
from flask.blueprints import Blueprint
from flask_login import login_required
from lingual.utils.languages import Languages, get_translatable
from lingual.models import User

main_bp = Blueprint(
    'main',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/modules/main/static'
)

@main_bp.route('/')
def landing():
    return render_template('landing.html')

@main_bp.route('/login')
def login():
    return "This is the login page for Lingual HSC."

@main_bp.route('/register', strict_slashes=False)
def register():
    current_app.logger.info("Clearing registration session data.")
    session.pop('reg', None)  # Clear any existing registration data
    return render_template('register.html', languages=list(Languages))

@main_bp.route('/register/u/<step>', methods=['POST'], strict_slashes=False)
def register_util(step):

    def save_to_session(key: str, value) -> None:
        reg = session.get('reg', {})
        reg[key] = value
        session['reg'] = reg
    
    def get_from_session(key: str) -> str | None:
        return session.get('reg', {}).get(key) or None

    if step == "welcome_text":
        try:
            data = request.get_json()

            if not data:
                return jsonify({"error": "No JSON payload provided"}), 400

            language = data.get("language")

            if not language:
                return jsonify({"error": "Missing 'language'"}), 400

            save_to_session('language', language)

            translated = get_translatable(language, "signup_welcome_text")

            return jsonify({"text": translated})

        except Exception as e:
            print(f"Error processing request: {e}")
            return jsonify({"error": "Internal server error"}), 500

    elif step == "user_hello":
        try:
            data = request.get_json()

            if not data:
                return jsonify({"error": "No JSON payload provided"}), 400

            first_name: str = data.get("first_name").strip().title()
            last_name: str = data.get("last_name").strip().title()

            if not first_name:
                return jsonify({"error": "Missing 'first_name'"}), 400
            translated = get_translatable(get_from_session('language') or 'en', "signup_user_hello")
            txt = translated.replace("{first_name}", first_name)

            save_to_session('first_name', first_name)
            save_to_session('last_name', last_name)

            return jsonify({"text": txt})
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500
        
    elif step == "send_verification_code":
        try:
            data = request.get_json()

            if not data:
                return jsonify({"error": "No JSON payload provided"}), 400

            email: str = data.get("email").strip()

            if not email:
                return jsonify({"error": "Missing 'email'"}), 400

            if User.query.filter_by(email=email).first():
                return jsonify({"error": "Email already registered. Please use a different email address or log in."}), 400

            save_to_session('email', email)

            from lingual.core.auth.routes import verify_email
            verify_email()

            # Redact part of the email for privacy
            local, domain = email.split('@')
            # first 3 characters of local part + ***** + last 2 characters of local part
            redacted_local = local[:3] + '*****' + local[-2:] if len(local) > 5 else local[0] + '***' + local[-1]
            redacted_email = f"{redacted_local}@{domain}"

            return jsonify({"email": redacted_email})
        except Exception as e:
            print(f"Error processing request: {e}")
            return jsonify({"error": "Internal server error"}), 500

    elif step == "verify_otp":
        try:
            data = request.get_json()

            if not data:
                return jsonify({"error": "No JSON payload provided"}), 400

            code: str = data.get("code").strip()

            if not code:
                return jsonify({"error": "Missing 'code'"}), 400

            # TODO : Verify OTP code here
            from lingual.core.auth.routes import verify_otp
            response = verify_otp(code)

            if response:
                return jsonify({"error": response}), 400

            secret_text = get_translatable(get_from_session('language') or 'en', "signup_password_title")
            return jsonify({"error": None, "secret_text": secret_text})
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({"error": "Internal server error"}), 500

    return jsonify({"error": "Invalid step"}), 400

@login_required
@main_bp.route('/app', strict_slashes=False)
def app():
    return "This is the main app page for Lingual HSC."
