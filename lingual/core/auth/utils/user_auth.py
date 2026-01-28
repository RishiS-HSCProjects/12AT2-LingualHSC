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

    def set_fname(self, first_name: str) -> None:
        """
            Returns None if successful, else error message string.
        """
        first_name = first_name.strip().title()

        from lingual.core.auth.utils.utils import validate_name
        err = validate_name(first_name)
        if err: raise RegUserValueException(str(err))
        
        self.first_name = first_name
    
    def set_email(self, email: str) -> None:
        """
            Returns None if successful, else error message string.
        """
        
        from lingual.core.auth.utils.utils import validate_email
        err = validate_email(email, exists=False)
        if err: raise RegUserValueException(str(err))

        self.email = email.strip().lower()
        return None
    
    def set_language(self, language: str) -> None:
        import lingual.utils.languages as lang_utils
        if language not in [lang.value.code for lang in lang_utils.Languages]:
            raise RegUserValueException("Invalid language selection.")

        self.language = language
        return None
    
    def build_user(self) -> 'User':
        # Create the user instance
        # Ensure required fields are present
        if not self.email:
            raise RegUserValueException("Cannot build user: email is not set")

        user = User(
            first_name=self.first_name.strip().title(),  # type: ignore
            email=self.email.strip().lower()  # type: ignore
        )

        try:
            # Attempt to add language to the user
            user.add_language(self.language)
        except Exception as e:
            # Log the error and raise an exception to stop further processing
            flash(f"Error adding language to user: {str(e)}", "error")
            current_app.logger.error(f"Error adding language {self.language} to user.")

        return user

def deserialize_RegUser(data: dict) -> RegUser:
    """
    This function takes a dictionary `data` and returns an instance of RegUser.
    The dictionary should have the following keys: 'first_name', 'email', 'language'.
    """
    user = RegUser()

    # Set the fields if they exist in the input dictionary
    if 'first_name' in data and data['first_name']:
        user.set_fname(data['first_name'])
    if 'email' in data and data['email']:
        user.set_email(data['email'])
    if 'language' in data and data['language']:
        user.set_language(data['language'])    

    return user

class RegUserValueException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
