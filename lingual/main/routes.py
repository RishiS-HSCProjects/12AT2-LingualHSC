from flask import jsonify, redirect, render_template, request, session, current_app, flash, url_for
from flask.blueprints import Blueprint
from flask_login import current_user, login_required
from lingual.utils.languages import Languages, get_translatable
from lingual.core.auth.utils.user_auth import RegUser, deserialize_RegUser

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

@main_bp.route('/login', methods=['GET', 'POST'], strict_slashes=False)
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.app'))

    from lingual.main.forms import LoginForm
    form = LoginForm()

    if request.method == 'GET':
        # Pre-fill form if data exists in session
        form_data = session.pop('form_data', None)
        if form_data: form.email.data = form_data.get('email', '')

        return render_template('login.html', form=form)
    
    elif request.method == 'POST':
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data
            
            from lingual.models import User
            user: User | None = User.query.filter_by(email=email.lower()).first() # type: ignore
            if not user or not user.check_password(password):
                flash("Invalid email or password.", "error")
                return redirect(url_for('main.login'))

            from flask_login import login_user
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('main.app'))
        else:
            for error in form.errors.values():
                flash(error[1], "error") # type: ignore

            session['form_data'] = {
                "email": form.email.data,
            }

        return redirect(url_for('main.login'))

    return render_template('login.html', form=form)

@main_bp.route('/register', strict_slashes=False)
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.app'))


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
        # Get user data from the session
        user_data = session.get('reg_user', None)
        if not user_data:
            return jsonify({"error": "No user data found in session"}), 400

        # Parse JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON payload provided"}), 400

        user: RegUser = deserialize_RegUser(user_data)

        if step == "welcome_text":
            language = data.get("language")
            result = user.set_language(language)

            if result:
                return jsonify({"error": result})

            translated = get_translatable(language, "signup_welcome_text")
            session['reg_user'] = user.serialize()

            return jsonify({"text": translated})

        elif step == "verify_name":
            name = data.get("name", "").strip().title()
            if not name:
                return jsonify({'error': "Missing name"}), 400

            name_type = data.get("type")
            if name_type == 'first-name':
                result = user.set_fname(name)
                if result:
                    return jsonify({"f_error": result})
            else:
                result = user.set_lname(name)
                if result:
                    return jsonify({"l_error": result})
            
            return jsonify({"error": None}) # Cancels the error

        elif step == "user_hello":
            first_name = data.get("first_name", "").strip().title()
            last_name = data.get("last_name", "").strip().title()

            result = user.set_fname(first_name)
            if result:
                return jsonify({"error": result})

            if last_name:
                result = user.set_lname(last_name)
                if result:
                    return jsonify({"error": result})

            translated = get_translatable(user.language or 'en', "signup_user_hello")
            txt = translated.replace("{first_name}", first_name)

            session['reg_user'] = user.serialize()
            return jsonify({"text": txt})

        elif step == "send_verification_code":
            email = data.get("email", "").strip()
            if not email:
                return jsonify({"error": "Missing 'email'"}), 400

            result = user.set_email(email)
            if result:
                return jsonify({"error": result})

            session['reg_user'] = user.serialize()

            try:
                from lingual.core.auth.routes import verify_email
                verify_email()  # Send email verification
            except Exception as e:
                current_app.logger.error(f"Error in verify_email: {e}")
                return jsonify({"error": "Error during email verification"}), 400

            local, domain = email.split('@')
            redacted_local = local[:3] + '*****' + local[-2:] if len(local) > 5 else local[0] + '***' + local[-1]
            redacted_email = f"{redacted_local}@{domain}"

            return jsonify({"email": redacted_email})

        elif step == "verify_otp":
            code = data.get("code", "").strip()
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
        # Log the error and stack trace
        current_app.logger.error(f"Error processing request: {e}")
        return jsonify({"error": "Internal server error"}), 500

@login_required
@main_bp.route('/app', strict_slashes=False)
def app():
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))
    
    last_lang = current_user.get_last_language()
    
    if last_lang is None:  # No last language set
        if current_user.get_languages():
            # Set the first language as the last language if not set
            current_user.set_last_language(current_user.languages[0])
            last_lang = current_user.get_last_language()  # Retrieve the updated last language
    
    if last_lang:
        # Now that we know last_lang is not None, perform the redirect
        return redirect(url_for(last_lang.app_name + '.home'))
    
    return f"<h1>Hello {current_user.first_name}</h1>\nNo languages available for your profile."