from lingual.models import User

class RegUser:
    """
        Class to represent a user during the registration process.
        This class is used to collect and validate user information before creating a User instance in the database.
    """

    first_name: str
    email: str
    language: str # Language code

    def __init__(self):
        self.first_name = ""
        self.email = ""
        self.language = ""

    def serialize(self) -> dict[str, str | None]:
        """
            Serialize the RegUser instance into a dictionary format.
            Default to None for any falsy fields
        """
        return {
            'first_name': self.first_name or None,
            'email': self.email or None,
            'language': self.language or None
        }

    def set_fname(self, first_name: str) -> None:
        """
            Set the first name for the user.
            Returns None if successful, else error message string.
        """
        first_name = first_name.strip().title() # Standardise name to remove whitespace and capitalise first letter

        from lingual.core.auth.utils.utils import validate_name # Get validation function
        err = validate_name(first_name) # Validate the name and get any error message (or None if valid)
        if err: raise RegUserValueException(str(err)) # Raise exception if validation fails
        
        self.first_name = first_name # Set first name of reg user
    
    def set_email(self, email: str) -> None:
        """
            Set the email for the user.
            Returns None if successful, else error message string.
        """
        email = email.strip().lower() # Standardise email to remove whitespace and lowercase
        
        from lingual.core.auth.utils.utils import validate_email # Get validation function
        err = validate_email(email, exists=False) # Validate the email and get any error message (or None if valid). Ignore existence check here.
        if err: raise RegUserValueException(str(err))

        self.email = email # Set email of reg user
    
    def set_language(self, language: str) -> None:
        import lingual.utils.languages as lang_utils # Get language utils
        if language not in [lang.value.code for lang in lang_utils.Languages]: # Check if language code is valid
            raise RegUserValueException("Invalid language selection.") # Raise exception if invalid language code

        self.language = language # Set language code of reg user
    
    def build_user(self) -> 'User':
        """
            Build a User instance from the RegUser data.
            Raises RegUserValueException if required fields are missing or invalid.
        """

        if not self.email: # Check if email is set
            raise RegUserValueException("Cannot build user: email is not set") # Email is required to create a user

        # Create User instance with validated and standardised data
        user = User(
            first_name=self.first_name.strip().title(), # type: ignore -> Standardise again just in case
            email=self.email.strip().lower() # type: ignore -> Standardise again just in case
        )

        if self.language:
            # Set language list without creating stats yet (user has no id until flush/commit).
            user.languages = [self.language] # Set language code in user's languages list

        return user # Return the built User instance

def deserialize_RegUser(data: dict) -> RegUser:
    """
        This function takes a dictionary `data` and returns an instance of RegUser.
        The dictionary should have the following keys: 'first_name', 'email', 'language'.
    """
    user = RegUser() # Initialise empty RegUser instance

    # Set the fields if they exist in the input dictionary
    if 'first_name' in data and data['first_name']:
        user.set_fname(data['first_name'])
    if 'email' in data and data['email']:
        user.set_email(data['email'])
    if 'language' in data and data['language']:
        user.set_language(data['language'])

    return user # Return the populated RegUser instance

class RegUserValueException(Exception):
    """ Custom exception for invalid RegUser values. """
    def __init__(self, message: str):
        super().__init__(message) # Pass the error message to the base Exception class

class RegNotFoundException(Exception):
    """ Custom exception for when registration information is not found. """
    def __init__(self, message: str = "Registration information not found. Please try again."):
        super().__init__(message) # Pass the error message to the base Exception class
