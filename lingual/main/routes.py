from flask import jsonify, make_response, redirect, render_template, request, session, current_app, flash, url_for
from flask.blueprints import Blueprint
from flask_login import current_user, login_required
from lingual.core.auth.utils.exceptions import EmailSendingDisabledException
from lingual.utils.languages import Languages, get_translatable
from lingual.core.auth.utils.user_auth import RegUser, RegUserValueException, deserialize_RegUser
from lingual.utils.form_manager import (
    save_form_to_session, restore_form_from_session, clear_form_session,
    validate_ajax_form, flash_all_form_errors, FormValidationError
)

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
    # Redirect if already authenticated
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return redirect(url_for('main.app'))

    from lingual.main.forms import LoginForm
    form = LoginForm()

    if request.method == 'GET':
        # Restore form from previous failed attempt (if any)
        restore_form_from_session(form, session, flash_errors=True)
    
    elif request.method == 'POST':
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data
            
            # Attempt to find and authenticate user
            from lingual.models import User
            user: User | None = User.query.filter_by(email=email.lower()).first() # type: ignore
            if not user or not user.check_password(password):
                form.password.data = ''  # Clear password field

                flash("Invalid email or password.", "error")
                save_form_to_session(form, session)  # Save for retry
                return redirect(url_for('main.login', next=request.args.get('next')))  # type: ignore

            # Login successful
            from flask_login import login_user
            login_user(user)
            flash("Login successful!", "success")
            clear_form_session(session) # Clear saved data on success

            # Redirect to next page or default to app
            if 'next' in request.args:
                resp = redirect(request.args.get('next'))  # type: ignore
            else:
                resp = redirect(url_for('main.app'))

            resp.set_cookie('has_account', 'true') # Add session cookie to indicate user has an account
            return resp
        else:
            # Validation failed - save and display errors
            save_form_to_session(form, session)
            flash_all_form_errors(form)

    return render_template('login.html', form=form)

@main_bp.route('/logout', strict_slashes=False)
def logout():
    if not current_user.is_authenticated:
        return redirect(url_for('main.landing'))

    from flask_login import logout_user
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('main.landing'))

@main_bp.route('/register', strict_slashes=False)
def register():
    # Redirect if already authenticated
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return redirect(url_for('main.app'))

    session.pop('reg_user', None) # Clear any existing registration session data

    # Initialize registration session
    user = RegUser()
    session['reg_user'] = user.serialize() # Serializes registration user in session
    
    # Create form for CSRF protection in AJAX calls
    from flask_wtf import FlaskForm
    csrf_form = FlaskForm() # Form is only for FlaskWTF's inbuilt CSRF token protection

    return render_template('register.html', languages=list(Languages), form=csrf_form)

@main_bp.route('/register/u/<step>', methods=['POST'], strict_slashes=False)
def register_util(step):
    try:
        # Get user data from session
        user_data = session.get('reg_user', None) # Get serialized RegUser
        if not user_data:
            return jsonify({"error": "No user data found in session"}), 400

        data = request.get_json() # Get AJAX JSON payload from request 
        if not data:
            return jsonify({"error": "No JSON payload provided"}), 400

        user: RegUser = deserialize_RegUser(user_data) # Deserialize to RegUser object

        if step == "welcome_text": # Handles language selection and welcome text retrieval
            from lingual.main.forms import RegistrationLanguageForm
            
            # Populate language choices dynamically
            form = RegistrationLanguageForm(data=data)
            form.language.choices = [(lang.value, lang.name) for lang in Languages]
            
            language = data.get("language", None)
            if not language:
                # If language is missing, exit.
                # This can happen if the user tampers with the request.
                return jsonify({"error": "Language is required"}), 400
            
            user.set_language(language) # Validate and set language. Raises RegUserValueException on error.

            translated = get_translatable(language, "signup_welcome_text") # Get welcome text in selected language
            session['reg_user'] = user.serialize() # Update session data
            return jsonify({"text": translated}) # Return welcome text if all other processes are successful

        elif step == "verify_name": # Handles name verification
            # Strip is called here again to allow the next falsy test to work.
            name = data.get("name", "").strip()
            if not name:
                return jsonify({'error': "Missing name"}), 400

            user.set_fname(name) # Validate and set first name. Raises RegUserValueException on error.
            
            session['reg_user'] = user.serialize() # Update session data
            return jsonify({}) # No error

        elif step == "user_hello": # Handles greeting text after name entry
            from lingual.main.forms import RegistrationNameForm
            
            # Validate using utility
            success, error, form = validate_ajax_form(
                RegistrationNameForm, 
                data, 
                field_mappings={'first_name': 'first_name'}
            )

            if not success:
                # Validation failed
                return jsonify({"error": error}), 400

            first_name = data.get("first_name", None) # Should be present due to earlier validation

            if not first_name:
                # This should not happen due to earlier validation
                return jsonify({"error": "Missing 'first_name'"}), 400

            user.set_fname(first_name) # Validate and set first name. Raises RegUserValueException on error.

            translated = get_translatable(user.language or 'en', "signup_user_hello") # Get greeting text
            txt = translated.replace("{first_name}", first_name) # Personalise greeting
            session['reg_user'] = user.serialize() # Update session data
            return jsonify({"text": txt}) # Return greeting text if all other processes are successful

        elif step == "send_verification_code": # Handles email verification request and returns redacted email      
            email = data.get("email", "").strip() # Strip to allow following falsy test
            if not email:
                return jsonify({"error": "Missing 'email'"}), 400

            from lingual.main.forms import RegistrationEmailForm
            # Validate using utility
            success, error, form = validate_ajax_form(
                RegistrationEmailForm,
                {'email': email}
            )
            if not success:
                return jsonify({"error": error})

            user.set_email(email) # Validate and set email. Raises RegUserValueException on error.

            session['reg_user'] = user.serialize() # Update session data

            # If the user is yet to submit the form, just return empty success.
            # This happens since this function is called every time the email field changes.
            # This is done to allow real-time validation feedback.

            if not data.get("submit", False):
                # Since we haven't yet submitted the form, just return success.
                return jsonify({})

            try:
                from lingual.core.auth.routes import verify_email
                verify_email() # Send verification email
            except Exception as e:
                current_app.logger.error(f"Error in verify_email: {e}")
                return jsonify({"error": "Error while sending verification email"}), 400

            # The following code is responsible for returning a redacted version of the email for display.
            # Sending unredacted emails back to the client could be at risk of interception.
            # As a result, we redact part of the email before sending it back.
            local, domain = email.split('@') # Split email into local and domain parts
            if len(local) > 5:
                # Redact middle characters for longer local parts
                redacted_local = local[:3] + '*****' + local[-2:]
            else:
                # Redact all but first and last character for shorter local parts
                redacted_local = local[0] + '***' + local[-1] if len(local) > 2 else local[0] + '***'

            redacted_email = f"{redacted_local}@{domain}" # Reconstruct redacted email

            return jsonify({"email": redacted_email}) # Return redacted email if all other processes are successful

        elif step == "verify_otp": # Handles OTP verification and password prompt
            code = data.get("code", "").strip() # Strip to allow following falsy test
            if not code: # If code is missing
                return jsonify({"error": "Missing 'code'"}), 400
            
            from lingual.core.auth.forms import OTPVerificationForm
            # Validate form using utility
            success, error, form = validate_ajax_form(
                OTPVerificationForm,
                {'code': code}
            )
            if not success:
                return jsonify({"error": error})

            try:
                from lingual.core.auth.routes import verify_otp
                response = verify_otp(code) # Attempt to verify OTP. Returns str error message on failure, None on success.
            except Exception as e:
                current_app.logger.error(f"Error in verify_otp: {e}")
                return jsonify({"error": "Error during OTP verification"}), 400

            if response: # OTP verification failed
                return jsonify({"error": response})

            secret_text = get_translatable(user.language or 'en', "signup_password_title") # Get translatable text for password prompt
            return jsonify({"error": None, "secret_text": secret_text}) # Return success with password prompt text

        # If the step is unrecognised, the following is executed.
        flash("Tried to perform an unknown action during registration.", "error")
        return redirect(url_for('main.register'))
    except RegUserValueException as e:
        # If a RegUserValueException is raised, return the error message.
        # This is an expected error type for validation issues, thus not logged as server error.
        # Having this here avoids repetitive try-except blocks in each step.
        # That is also why I rewrote this function to use exceptions for validation errors on 27 Jan 2026.
        return jsonify({"error": str(e)})
    except FormValidationError as e:
        # This is an expected exception raised by validate_ajax_form utility.
        # Thus, we do not log it as a server error.
        return jsonify({"error": str(e.message)})
    except Exception as e:
        # All expected error types are custom built.
        # All Flask or Python default errors are unexpected and thus logged.
        current_app.logger.error(f"Error processing request: {e}") # Detailed error log for debugging
        return jsonify({"error": "Internal server error"}), 500 # Generic error message for unexpected errors

@main_bp.route('/login/reset', methods=['GET', 'POST'], strict_slashes=False)
def reset():
    # Redirect if already authenticated
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return redirect(url_for('main.app')) # Redirect to 'app' route
    
    from lingual.main.forms import RequestForm 
    form = RequestForm() # Form for requesting password reset

    if request.method == 'POST': # Handle form submission
        if form.validate_on_submit():
            email = (form.email.data or '').strip()
            
            # Look up user by email
            from lingual.models import User
            user: User | None = User.query.filter_by(email=email.lower()).first() # type: ignore

            if user: # Only attempt to send email if user exists
                try:
                    # Send password reset email
                    from lingual.core.auth.routes import send_password_reset_email
                    send_password_reset_email(user)
                except EmailSendingDisabledException:
                    # Email sending is disabled in config
                    # While this is expected, we log it for awareness.
                    current_app.logger.warning("Password reset email sending attempted but is disabled in configuration.")
                    flash("Email sending is currently disabled in the application configuration.", "warning")
                    return redirect(url_for('main.reset'))
                except Exception as e:
                    # Expected errors are handled by custom exceptions
                    current_app.logger.error(f"Error sending password reset email: {e}") # Log unexpected errors
                    flash("An error occurred while attempting to send the reset email. Please try again later.", "error")
                    return redirect(url_for('main.reset'))
            
            # Generic success message (don't reveal if user exists)
            # This prevents "email enumeration" attacks.
            flash("If an account with that email exists, a reset link has been sent.", "info")
            return redirect(url_for('main.login'))
        else:
            # Validation failed - flash errors
            flash_all_form_errors(form)

    return render_template('reset.html', form=form) # Render password reset request template

@main_bp.route('/login/reset_request/<token>', methods=['GET', 'POST'], strict_slashes=False)
def reset_token(token):
    # Redirect if already authenticated
    if current_user.is_authenticated:
        flash("To change your password, head to your account settings.", "info")
        return redirect(url_for('main.app')) # Redirect to 'app' route

    # Verify reset token is valid
    from lingual.models import User
    user = User.verify_reset_token(token) # Verify token and get user

    if not user:
        # Invalid or expired token
        flash("Invalid or expired token. Please request a new password reset.", "error")
        return redirect(url_for('main.reset')) # Redirect to reset request page

    # If we reach here, the token is valid.
    # The following code handles password reset form submission.

    from lingual.main.forms import PasswordResetForm
    form = PasswordResetForm() 
    
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # Update user password
                password = form.password.data
                if password:  # Type guard
                    user.set_password(password)
                    from lingual import db
                    db.session.commit() # Save changes to database
                    flash("Your password has been updated! You can now log in.", "success")
                    return redirect(url_for('main.login'))
            except Exception as e:
                current_app.logger.error(f"Error updating password: {e}")
                flash("An error occurred while updating your password. Please try again.", "error")
        else:
            # Validation failed - flash errors
            flash_all_form_errors(form)

    return render_template('reset-token.html', user=user, token=token, form=form) # Render password reset form template

@main_bp.route('/app', strict_slashes=False)
def app():
    if not current_user.is_authenticated:
        # For simplicity, I only have one button on the landing page
        # for sign in and sign up titled "Get Started". Initially,
        # this button redirected the user to the login page since I
        # believed that most users would already have an account, and
        # those who don't would be able to easily navigate to the 
        # registration page from there.
        # However, upon user testing, I found that most testing users
        # automatically attempted signing up from the login page,
        # requiring me to steer them down to the registration page
        # almost every time. I realised that the "Get Started" button
        # likely gave users the subconscious expectation that it would
        # take them to the registration page, resulting in them starting
        # the sign up process without realising they were on the login page.
        # I didn't want to change the landing page at this stage since I
        # prefered having one button instead of two ("Login" and "Register")
        # on the nav bar for simplicity and cleaner UI. As a result, I decided
        # to make the "Get Started" button's (and, subsequently, all
        # unauthenticated accesses to the app route) behaviour dynamic based
        # on whether or not the device user has an account or not.
        # This way, new years will be taken to the registration page, while
        # returning users will be taken to the login page, which is the most
        # likely page both user types will want to go to when they click "Get Started".
        # Furthermore, existing users who are presented with the registration page
        # are less likely to be confused since they'll remember the registration
        # process from when they initially signed up.
        # I am tracking user logins with a simple cookie that is set to "true" upon 
        # a successful login. I am using a static cookie instead of a server-side
        # session variable since I want this data to persist even after the session ends,
        # allowing returning users to be recognised even if they haven't logged in for a while.
        # Furthermore, since this cookie doesn't contain any sensitive data and is only used
        # for improving UX by remembering if the user has an account, storing it encrypted 
        # in a server-side session would be very unnecessary. Thus, a simple cookie is
        # the best solution for this use case.

        # Documented on 18 Feb 2026
        if request.cookies.get('has_account', 'false') == 'true':
            return redirect(url_for('main.login'))
        else:
            return redirect(url_for('main.register'))
    
    last_lang = current_user.get_last_language()
    
    if last_lang is None:  # No last language set
        if current_user.get_languages():
            # Set the first language as the last language if not set
            current_user.set_last_language(current_user.languages[0])
            from lingual import db
            db.session.commit() # Save changes to database
            last_lang = current_user.get_last_language()  # Retrieve the updated last language
    
    if last_lang:
        # Now that we know last_lang is not None, perform the redirect
        return redirect(url_for(last_lang.app_code + '.home'))
    
    return f"<h1>Hello {current_user.first_name}</h1>\nNo languages available for your profile."

@main_bp.route('/app/directory', strict_slashes=False)
@login_required
def app_directory():
    languages = [lang.obj() for lang in Languages if lang.obj().code != Languages.TUTORIAL.obj().code] # Exclude tutorial from app directory
    user_languages = current_user.get_languages()

    return render_template(
        'app-directory.html',
        user_languages=user_languages,
        languages=[lang for lang in languages if lang not in user_languages]
    )

@main_bp.route('/app/<string:code>', strict_slashes=False)
@login_required
def app_redirect(code: str):
    try:
        current_user.add_language(code) # type: ignore -> If language is already added, this does nothing
    except ValueError:
        flash("The requested language app does not exist.", "error")
        return redirect(url_for('main.app_directory'))

    current_user.set_last_language(code)
    from lingual import db
    db.session.commit() # Save changes to database

    return redirect(url_for('main.app'))
