from flask import current_app, flash
from lingual.models import User

class RegUser:
    first_name: str
    email: str
    language: str

    def __init__(self):
        self.first_name = ""
        self.email = ""
        self.language = ""

    def serialize(self) -> dict:
        return {
            'first_name': self.first_name or None,
            'email': self.email or None,
            'language': self.language or None
        }

    def verify_name(self, name: str) -> int | None:
        if not name:
            return NameValidationError.EMPTY_NAME
        
        if len(name) > 50:
            return NameValidationError.TOO_LONG
        
        if not all(c.isalpha() or c in " -'" for c in name):
            return NameValidationError.INVALID_CHARACTERS
        
        return None

    def set_fname(self, first_name: str) -> str | None:
        """
            Returns None if successful, else error message string.
        """
        first_name = first_name.strip().title()
        
        if (err := self.verify_name(first_name)) is None:
            self.first_name = first_name
            return None
        elif err == NameValidationError.EMPTY_NAME:
            return "First name cannot be empty."
        elif err == NameValidationError.TOO_LONG:
            return "First name cannot exceed 50 characters."
        elif err == NameValidationError.INVALID_CHARACTERS:
            return "First name can only contain letters, spaces, apostrophes, and hyphens."
        
        return "Unknown error." # Fallback, should never reach here
    
    def set_email(self, email: str) -> str | None:
        """
            Returns None if successful, else error message string.
        """
        email = email.strip()
        if not email:
            return "Email cannot be empty."
        
        from lingual.models import User
        if User.query.filter_by(email=email.lower()).first():
            return "Email already registered. Please use a different email address or log in."

        # Following (AI generated) regex line ensures the:
        #  -  Local part is alphanumeric + [._%+-], no leading/trailing dots, no consecutive dots
        #  -  Domain part is alphanumeric + [-], must have a dot and 2+ char TLD

        email_regex = r"^(?!\.)(?!.*?\.\.)[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if email.count('@') != 1:
            return "Invalid format: Email must contain exactly one '@' symbol."

        import re
        if not re.fullmatch(email_regex, email, re.IGNORECASE):
            return "Invalid format: Please recheck your email."

        local_part, domain_part = email.split('@')
        if len(local_part) > 64:
            return "Email prefix too long (max 64 characters)."
        if len(email) > 254:
            return "Total email address length exceeds limit (254 characters)."

        self.email = email.lower()
        return None
    
    def set_language(self, language: str) -> str | None:
        import lingual.utils.languages as lang_utils
        if language not in [lang.value.code for lang in lang_utils.Languages]:
            return "Invalid language selection."

        self.language = language
        return None
    
    def build_user(self) -> 'User':
        # Create the user instance
        # Ensure required fields are present
        if not self.email:
            raise ValueError("Cannot build user: email is not set")

        user = User(
            first_name=self.first_name,  # type: ignore
            email=self.email  # type: ignore
        )

        try:
            # Attempt to add language to the user
            user.add_language(self.language)
        except Exception as e:
            # Log the error and raise an exception to stop further processing
            flash(f"Error adding language to user: {str(e)}", "error")
            current_app.logger.error(f"Error adding language to user: {e}")

        return user

def deserialize_RegUser(data: dict) -> RegUser:
    """
    This function takes a dictionary `data` and returns an instance of RegUser.
    The dictionary should have the following keys: 'first_name', 'email', 'language'.
    """
    user = RegUser()
    error = None

    # Set the fields if they exist in the input dictionary
    if 'first_name' in data and data['first_name']:
        error = user.set_fname(data['first_name'])
    if 'email' in data and data['email']:
        error = user.set_email(data['email'])
    if 'language' in data and data['language']:
        error = user.set_language(data['language'])

    if error:
        flash(f"Error deserializing RegUser: {error}", "error")
        current_app.logger.error(f"Error deserializing RegUser: {error}")
        raise ValueError(error)        

    return user

class NameValidationError():
    EMPTY_NAME = 0
    TOO_LONG = 1
    INVALID_CHARACTERS = 2
