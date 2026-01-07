from flask import jsonify, redirect, render_template, request, session, current_app, flash
from flask.blueprints import Blueprint
from flask_login import current_user, login_required
from lingual.utils.languages import Languages, get_translatable
from lingual.core.auth.utils.user_auth import RegUser, deserialize_RegUser
import traceback

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
    session.pop('reg_user', None)  # Clear any existing registration data

    # if current_user.is_authenticated:
    #     flash("You are already logged in.", "info")
    #     return redirect('main.app')

    user = RegUser()

    session['reg_user'] = user.serialize() # Initialize registration session data

    return render_template('register.html', languages=list(Languages))

@main_bp.route('/register/u/<step>', methods=['POST'], strict_slashes=False)
def register_util(step):
    try:
        user_data = session.get('reg_user', None)
        if not user_data:
            return jsonify({"error": "No user data found in session"}), 400

        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON payload provided"}), 400
        user: RegUser = deserialize_RegUser(user_data)

        if step == "welcome_text":
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON payload provided"}), 400

            language = data.get("language")
            result = user.set_language(language)

            if result:
                return jsonify({"error": result})
            

            translated = get_translatable(language, "signup_welcome_text")
            session['reg_user'] = user.serialize()

            return jsonify({"text": translated})

        elif step == "verify_name":
            name = data.get("name").strip().title()

            if not name:
                return jsonify({'error': "Missing name"}), 400
            
            if data.get("type") == 'first-name':
                result = user.set_fname(name)
                if result:
                    return jsonify({"f_error": result})
            else:
                result = user.set_lname(name)
                if result:
                    return jsonify({"l_error": result})
            
            return jsonify({"error": None}) # Cancels the error

        elif step == "user_hello":

            first_name: str = data.get("first_name", "").strip().title()
            last_name: str = data.get("last_name", "").strip().title()
            
            result = user.set_fname(first_name)
            if result:
                return jsonify({"error": result})

            result = user.set_lname(last_name)
            if result:
                return jsonify({"error": result})

            translated = get_translatable(user.language or 'en', "signup_user_hello")
            txt = translated.replace("{first_name}", first_name)

            session['reg_user'] = user.serialize()
            return jsonify({"text": txt})

        elif step == "send_verification_code":
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON payload provided"}), 400

            email: str = data.get("email", "").strip()
            if not email:
                return jsonify({"error": "Missing 'email'"})

            result = user.set_email(email)
            if result:
                return jsonify({"error": result})

            session['reg_user'] = user.serialize()

            try:
                from lingual.core.auth.routes import verify_email
                verify_email()
            except Exception as e:
                current_app.logger.error(f"Error in verify_email: {e}")
                return jsonify({"error": "Error during email verification"}), 400

            local, domain = email.split('@')
            redacted_local = local[:3] + '*****' + local[-2:] if len(local) > 5 else local[0] + '***' + local[-1]
            redacted_email = f"{redacted_local}@{domain}"

            return jsonify({"email": redacted_email})

        elif step == "verify_otp":
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON payload provided"}), 400

            code: str = data.get("code", "").strip()
            if not code:
                return jsonify({"error": "Missing 'code'"}), 400

            try:
                from lingual.core.auth.routes import verify_otp
                response = verify_otp(code)
            except Exception as e:
                current_app.logger.error(f"Error in verify_otp: {e}")
                return jsonify({"error": "Error during OTP verification"}), 400

            if response:
                return jsonify({"error": response})

            secret_text = get_translatable(user.language or 'en', "signup_password_title")
            return jsonify({"error": None, "secret_text": secret_text})

        return jsonify({"error": "Invalid step"}), 500

    except Exception as e:
        # Log the detailed error and stack trace
        current_app.logger.error(f"Error processing request: {e}")
        current_app.logger.error(traceback.format_exc())  # This will log the full stack trace
        return jsonify({"error": "Internal server error"}), 500

@login_required
@main_bp.route('/app', strict_slashes=False)
def app():
    return "This is the main app page for Lingual HSC."
