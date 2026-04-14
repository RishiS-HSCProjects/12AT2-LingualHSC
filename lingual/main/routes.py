import traceback
from werkzeug.exceptions import HTTPException
from flask import jsonify, redirect, render_template, request, session, current_app, flash, url_for
from flask.blueprints import Blueprint
from flask_login import current_user, login_required
from lingual import db
from lingual.utils.mail_utils import EmailError
from lingual.main.utils import AccountActionTypes
from lingual.utils.modals import ModalForm
from lingual.utils.languages import Languages, get_translatable
from lingual.core.auth.utils.user_auth import RegNotFoundException, RegUser, RegUserValueException, deserialize_RegUser
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
    return render_template('landing.html', get_translatable=get_translatable)

@main_bp.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html', title="Welcome to Lingual HSC")

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
            if user is None or not user.check_password(password):
                form.password.data = ''  # Clear password field

                flash("Invalid email or password.", "error")
                save_form_to_session(form, session)  # Save for retry
                return redirect(url_for('main.login', next=request.args.get('next')))  # type: ignore

            # Login successful
            user.login()
            flash("Login successful!", "success")
            clear_form_session(session) # Clear saved data on success

            # Redirect to next page or default to app

            if session.pop('new_user', False):
                resp = redirect(url_for('main.welcome'))   # Show welcome page if user just registered
            elif 'next' in request.args:
                resp = redirect(request.args.get('next'))  # type: ignore
            else:
                resp = redirect(url_for('main.app'))

            resp.set_cookie('has_account', 'true', max_age=400*24*60*60) # Add persistent cookie to indicate user has an account
            return resp # Return response with cookie set
        else:
            # Validation failed: save and display errors
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

    return render_template(
        'register.html',
        languages=Languages.get_languages(), # Exclude tutorial from language options
        form=csrf_form
    )

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
                return jsonify({"error": "Language is required"}), 400 # 400 Bad Request
            
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
                return jsonify({"error": error}), 400

            user.set_email(email) # Validate and set email. Raises RegUserValueException on error.

            session['reg_user'] = user.serialize() # Update session data

            # If the user is yet to submit the form, just return empty success.
            # This happens since this function is called every time the email field changes.
            # This is done to allow real-time validation feedback.

            if not data.get("submit", False):
                # Since we haven't yet submitted the form, just return success.
                return jsonify({})

            email_error = None
            try:
                from lingual.core.auth.routes import send_verification_email
                send_verification_email(session.get('reg_user'))
            except EmailError.EmailSendingDisabled as e:
                # Disabled email mode still allows OTP verification with fallback code.
                current_app.logger.info(f"Email sending disabled for OTP flow: {e}")
                email_error = None
            except RegNotFoundException as e:
                # Likely a session timeout issue, but still logged just in case
                current_app.logger.warning(f"Registration Info Missing: {e}")
                email_error = "Your registration session has timed-out. Please refresh and try again."
            except EmailError.SMTPConfig as e:
                current_app.logger.warning(f"SMTP Misconfigured: {e}")
                email_error = str(e)
            except EmailError.SendFailure as e:
                current_app.logger.error(f"Verification email send failed: {e}")
                email_error = str(e)
            except Exception as e:
                # Log unexpected errors
                current_app.logger.error(f"Error in verify_email: {e}") # Attach detailed error log for debugging
                current_app.logger.error(traceback.format_exc()) # Attach traceback
                email_error = "A fatal error occurred while sending the verification email." # For Flash

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

            return jsonify({
                "allowSendEmails": current_app.config.get('ALLOW_SEND_EMAILS', True), # Send config value for client-side warning
                "email": redacted_email,
                "error": email_error
            })

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
                return jsonify({"error": error}), 400

            try:
                from lingual.core.auth.routes import verify_otp
                response = verify_otp(code) # Attempt to verify OTP. Returns str error message on failure, None on success.
            except Exception as e:
                current_app.logger.error(f"Error in verify_otp: {e}") # Attach detailed error log for debugging
                current_app.logger.error(traceback.format_exc()) # Attach traceback
                return jsonify({"error": "Error during OTP verification"}), 400

            if response: # OTP verification failed
                return jsonify({"error": response}), 400

            secret_text = get_translatable(user.language or 'en', "signup_password_title") # Get translatable text for password prompt
            return jsonify({"error": None, "secret_text": secret_text}) # Return success with password prompt text

        # If the step is unrecognised, the following is executed.
        flash("Tried to perform an unknown action during registration.", "error")
        return redirect(url_for('main.register'))
    except RegUserValueException as e:
        # If a RegUserValueException is raised, return the error message.
        # This is an expected error type for validation issues, thus not logged as server error.
        # Having this here avoids repetitive try-except blocks in each step.
        return jsonify({"error": str(e)})
    except FormValidationError as e:
        # This is an expected exception raised by validate_ajax_form utility.
        # Thus, we do not log it as a server error.
        return jsonify({"error": str(e.message)})
    except Exception as e:
        # All expected error types are custom built.
        # All Flask or Python default errors are unexpected and thus logged.
        current_app.logger.error(f"Error processing request: {e}") # Detailed error log for debugging
        current_app.logger.error(traceback.format_exc()) # Attach traceback
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
                except EmailError.EmailSendingDisabled:
                    # Email sending is disabled in config
                    # While this is expected, we log it for awareness.
                    current_app.logger.warning("Password reset attempted but email sending is disabled in configuration.")
                    flash("Email sending is currently disabled in the application configuration.", "warning")
                    return redirect(url_for('main.reset'))
                except Exception as e:
                    # Expected errors are handled by custom exceptions
                    current_app.logger.error(f"Error sending password reset email: {e}") # Log unexpected errors
                    current_app.logger.error(traceback.format_exc()) # Attach traceback
                    flash("An error occurred while attempting to send the reset email. Please try again later.", "error")
                    return redirect(url_for('main.reset'))
                else:
                    # Generic success message (don't reveal if user exists)
                    # This prevents "email enumeration" attacks.
                    flash("If an account with that email exists, a reset link has been sent.", "info")
                    return redirect(url_for('main.login'))

        else:
            # Validation failed: flash errors
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
                    db.session.commit() # Save changes to database
                    flash("Your password has been updated! You can now log in.", "success")
                    return redirect(url_for('main.login'))
            except ValueError as e:
                # Log password validation errors
                flash(str(e), "error")
            except Exception as e:
                # Log unexpected errors during password update
                current_app.logger.error(f"Error updating password: {e}")
                current_app.logger.error(traceback.format_exc())
                flash("An error occurred while updating your password. Please try again.", "error")
        else:
            # Validation failed: flash errors
            flash_all_form_errors(form)

    return render_template('reset-token.html', user=user, token=token, form=form) # Render password reset form template

@main_bp.route('/app', strict_slashes=False)
def app():
    if not current_user.is_authenticated:
        # T-FE04 -> Cookie set up in this file in the login route.
        if request.cookies.get('has_account', 'false') == 'true':
            return redirect(url_for('main.login'))
        else:
            return redirect(url_for('main.register'))
    
    last_lang = current_user.get_last_language()
    if last_lang is None: # No last language set
        if (len((user_langs := current_user.get_languages())) == 1):
            # If only one language, redirect to that language's app directly for convenience
            return redirect(url_for('main.app_redirect', code=user_langs[0].code)) # Redirect to the only language they have
        return redirect(url_for('main.app_directory')) # Redirect to app directory to choose a language

    if last_lang:
        # Now that we know last_lang is not None, perform the redirect
        return redirect(url_for(last_lang.app_code + '.home')) # Redirect to last language's app (standard naming conventions)

    return f"<h1>Hello {current_user.first_name}</h1>\nNo languages available for your profile."

@main_bp.route('/app/directory', strict_slashes=False)
@login_required
def app_directory():
    # Get all languages (except tutorial) and user's languages to display in app directory
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

    current_user.set_last_language(code) # Update last language to the one just accessed
    db.session.commit() # Save changes to database

    return redirect(url_for('main.app'))

def _resolve_modal_id(form) -> str | None:
    """ Utility to resolve the HTML id attribute for a given modal form.
        This is used to determine which modal to auto-open on page load based on URL parameters.
    """
    if not form: return None # If no form provided, return None
    return getattr(form, 'id', None) or f"{form.__class__.__name__}Modal"

@main_bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    # Get metadata from URL
    action = request.args.get('action') or None
    action_language_code = request.args.get('lang') or None
    action_type: AccountActionTypes | None = None
    action_form: ModalForm | None = None
    account_modals: dict[str, ModalForm] = {}
    user_lang = current_user.get_languages()

    from lingual.main.forms import DeleteAppConfirmation, UpdateInfoForm
    for modal_action in AccountActionTypes:
        try:
            form = modal_action.get_modal()

            # Handle custom setup modals
            if modal_action == AccountActionTypes.DELETE_APP:
                for lang in user_lang:
                    # Create a separate DeleteAppConfirmation form for each language app the user has, with custom app name and form action URL.
                    if isinstance(form, DeleteAppConfirmation):
                        form.set_app_name(lang.app_name)
                        setattr(form, 'id', f"DeleteAppConfirmation-{lang.code}Modal")
                        form.set_action(
                            url_for('main.account', action=modal_action.value, lang=lang.code)
                        )
                        account_modals[f"{modal_action.value}:{lang.code}"] = form
                continue

            if modal_action == AccountActionTypes.UPDATE_INFO:
                if isinstance(form, UpdateInfoForm):
                    if request.method == 'GET':
                        form.set_first_name(current_user.first_name)
                    account_modals[modal_action.value] = form
                continue

            # Handle regular modals
            if form: account_modals[modal_action.value] = form
        except NotImplementedError:
            continue # Skip unimplemented modals

    if action:
        # If an action is specified in the URL, attempt to resolve it to a modal form.
        try:
            action_type = AccountActionTypes(action) # Find matching action type from enum
        except ValueError as e:
            # If no type found, cancel the action and log.
            flash(f"Something went wrong.", "error") # General user error
            current_app.logger.warning(f"Unrecognized account action attempted: {action}")
            current_app.logger.warning(f"Error details: {e}")
            current_app.logger.warning(traceback.format_exc()) # Log the error details for debugging
            action_type = None # Cancel type

        if action_type == AccountActionTypes.DELETE_APP:
            # Configure delete app form
            if action_language_code:
                action_form = account_modals.get(f"{action_type.value}:{action_language_code}")
            if action_form is None:
                # If form not found, alert
                flash("App removal action is unavailable.", "warning")
                action_type = None
        elif action_type:
            # Get form
            action_form = account_modals.get(action_type.value)
            if action_form is None:
                # If form not found, alert
                flash(f"{action_type.name.title()} action not implemented.", "warning")
                action_type = None

    # Handle form submissions for each action type (granted a valid type and form)
    if request.method == 'POST' and action_type and action_form:
        if action_form.validate_on_submit(): # Handle submit
            if action_type == AccountActionTypes.DELETE_APP:
                if not action_language_code:
                    flash("No app was selected for removal.", "error")
                else:
                    # Check if user has an app
                    target_language = Languages.get_language_by_code(action_language_code)
                    if target_language is None or action_language_code not in current_user.get_language_codes():
                        flash("You do not have access to that app.", "error")
                    else:
                        # Remove language and commit to db
                        current_user.remove_language(action_language_code)
                        db.session.commit()
                        flash(f"{target_language.app_name} removed from your account.", "success")

                        # If deleted current language, redirect to app directory
                        if current_user.last_language == action_language_code:
                            return redirect(url_for('main.app_directory'))
                        else: # Otherwise, redirect to account
                            return redirect(url_for('main.account'))

            elif action_type == AccountActionTypes.DELETE:
                password = action_form.password.data # type: ignore
                if not current_user.check_password(password):
                    # Ensure password is correct
                    flash("Password incorrect. Please try again.", "error")
                else:
                    # Delete account
                    from lingual.models import User
                    user: User = User.query.get(current_user.id) # type: ignore -> get user instance
                    from flask_login import logout_user
                    logout_user() # First logout to prevent any issues
                    user.delete() # Delete
                    db.session.commit() # Update DB
                    flash("Successfully deleted account.", "success") # Send success msg

                    # Create response, redirecting to the landing page and removing has_account cookie to reset flow
                    resp = redirect(url_for('main.landing'))
                    resp.delete_cookie('has_account')
                    return resp # Return response

            elif action_type == AccountActionTypes.CHANGE_PASSWORD:
                current_password = action_form.current_password.data # type: ignore
                if not current_user.check_password(current_password):
                    flash("Current password is incorrect.", "error")
                else:
                    new_password = action_form.new_password.data # type: ignore
                    try:
                        # Method handles encryption and strength verification
                        current_user.set_password(new_password) # Set password
                    except ValueError as e:
                        flash(str(e), "error")
                        return redirect(url_for('main.account', _anchor='your-account'))

                    db.session.commit() # Update db
                    flash("Password updated successfully.", "success")
                    return redirect(url_for('main.account', _anchor='your-account')) # Refresh page and anchor to the account section

            elif action_type == AccountActionTypes.UPDATE_INFO:
                new_first_name = action_form.first_name.data.strip().title() # type: ignore -> Get first name from form

                try:
                    if new_first_name: current_user.set_first_name(new_first_name) # Update first name
                except ValueError as e:
                    flash(str(e), "error")
                    return redirect(url_for('main.account', _anchor='your-account'))

                db.session.commit() # Commit to db

                # Send success message and refresh page to display changes
                flash("Information updated successfully.", "success")
                return redirect(url_for('main.account', _anchor='your-account'))

            # Japanese-specific settings
            elif action_type in {
                AccountActionTypes.JP_RESET_GRAMMAR,
                AccountActionTypes.JP_CLEAR_PRACTISED_KANJI,
                AccountActionTypes.JP_CLEAR_KANJI_DATA,
            }:
                jp_stats = current_user.get_language_stats('jp')
                if not jp_stats: # Ensure jp_stats exists for the user, create if not
                    current_user.create_language_stats('jp')
                    db.session.commit()
                    jp_stats = current_user.get_language_stats('jp') # Attempt fetching again

                if not jp_stats:
                    # If jp_stats still can't be retrieved, something went wrong with the creation process. Alert the user.
                    flash("Unable to load Japanese stats for your account.", "error")
                else:
                    # Perform the relevant action and commit to db. Each action type corresponds to a different method on the jp_stats object.
                    success_message = None # Initialise success message
                    if action_type == AccountActionTypes.JP_RESET_GRAMMAR:
                        jp_stats.clear_grammar_practised()
                        success_message = "Grammar progress reset."

                    elif action_type == AccountActionTypes.JP_CLEAR_PRACTISED_KANJI:
                        jp_stats.clear_practised_kanji()
                        success_message = "Practised kanji cleared."

                    elif action_type == AccountActionTypes.JP_CLEAR_KANJI_DATA:
                        jp_stats.clear_kanji()
                        success_message = "All kanji data cleared."

                    db.session.commit() # Commit to db
                    if success_message: flash(success_message, "success") # Flash success (if exists)
                    return redirect(url_for('main.account', _anchor='jp-settings')) # Refresh
        else:
            # Flash any and all form errors
            flash_all_form_errors(action_form)

    last_lang = current_user.get_last_language() # Get last language

    # Render template passing through all required elements
    return render_template(
        'account.html',
        lang_obj=last_lang,
        user_lang=user_lang,
        action_form=action_form,
        auto_open_modal=bool(action_form), # Force truthy/falsy value to bool
        auto_open_modal_id=_resolve_modal_id(action_form),
        account_modals=list(account_modals.values())
    )

# Add error handlers website-wide
@main_bp.app_errorhandler(Exception)
def handle_exception(e):
    # Pass 500 as default if it's not a standard HTTP error
    code = 500
    if isinstance(e, HTTPException):
        code = e.code or 500

    # Find module from url (e.g. nihongo) for error form styling
    module = request.path.split('/')[1] if len(request.path.split('/')) > 1 else None
    
    # Get language code for error message translatables if error came from a language module,
    # otherwise default to English.
    lang_obj = Languages.get_language_by_app_code(module) if module else None
    lang_code = 'en' # Default to English if we can't determine a language from the URL
    if module and lang_obj: lang_code = lang_obj.code # If module valid and language found, get lang code
    
    # Get translatables headers and set error messages
    if code == 403:
        err_head = get_translatable(lang_code, "err_403_head")
        err_msg = "You do not have permission to access this page."
    elif code == 404:
        err_head = get_translatable(lang_code, "err_404_head")
        err_msg = "The page you are looking for does not exist!"
    elif code == 500:
        current_app.logger.error(f"Internal server error 500: {e}") # Log the error details for debugging
        current_app.logger.error(traceback.format_exc())
        err_head = "Internal Server Error"
        err_msg = "An internal server error occurred."
    else:
        current_app.logger.error(f"Unexpected error ({code}): {e}") # Log unexpected errors for debugging
        err_head = f"Error {code}"
        err_msg = "An unexpected error occurred."

    # Render error template, passing through custom information and the status code
    return render_template("error.html", lang_obj=lang_obj, err_head=err_head, err_msg=err_msg), code
