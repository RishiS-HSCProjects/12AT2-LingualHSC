import re
from enum import Enum

class AuthValidationError(Enum):
    """ Custom exception for authentication validation errors. """
    INVALID_EMAIL = 0
    EMAIL_ALREADY_EXISTS = 1
    EMAIL_NOT_FOUND = 2
    INVALID_PASSWORD = 3
    WEAK_PASSWORD = 4
    INVALID_NAME = 5
    INVALID_OTP = 6

    def __str__(self):
        """ Return user-friendly error message by validation error type. """
        if self == AuthValidationError.INVALID_EMAIL:
            return "Invalid email format"
        elif self == AuthValidationError.EMAIL_ALREADY_EXISTS:
            return "Email already registered"
        elif self == AuthValidationError.INVALID_PASSWORD:
            return "Invalid password"
        elif self == AuthValidationError.WEAK_PASSWORD:
            return "Password does not meet strength requirements"
        elif self == AuthValidationError.INVALID_NAME:
            return "Name contains invalid characters"
        elif self == AuthValidationError.INVALID_OTP:
            return "Invalid OTP code"
        raise ValueError("Unknown AuthValidationError: {}".format(self.value))

# RegEx consts for validation
RE_UPPERCASE = r'[A-Z]' # at least one uppercase letter
RE_LOWERCASE = r'[a-z]' # at least one lowercase letter
RE_DIGIT = r'\d' # at least one digit
RE_SPECIAL = r'[!@#$%^&*(),.?":{}|<>]' # at least one special character within: !@#$%^&*(),.?":{}|<>
RE_EMAIL = r"^(?!\.)(?!.*?\.\.)[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$" # domain must contain at least one dot and end with a valid TLD (at least 2 letters), local part cannot start with dot or contain consecutive dots
RE_NAME = r"^[a-zA-Z\s\-']+$" # name contains only letters, spaces, hyphens, and apostrophes

def validate_password_strength(password) -> AuthValidationError | None:
    """ Validate required password strength:
        - at least 8 characters
        - including uppercase letter
        - including lowercase letter
        - including digit
        - including special character.
        Returns None if valid, else AuthValidationError. """
    if (
        # Validate password is not empty and meets strength requirements via regex checks
        not password
        or len(password) < 8
        or re.search(RE_UPPERCASE, password) is None
        or re.search(RE_LOWERCASE, password) is None
        or re.search(RE_DIGIT, password) is None
        or re.search(RE_SPECIAL, password) is None
    ):
        return AuthValidationError.WEAK_PASSWORD # Return WEAK_PASSWORD error if any of the strength requirements are not met

    return None # Return None if password is valid and meets all strength requirements

def validate_email(email: str, exists: None | bool = None) -> AuthValidationError | None:
    """ Validate email format.
        If 'exists' is specified (not **None**):
        - If exists is True, checks that email exists in DB.
        - If exists is False, checks that email does not exist in DB.

        Returns None if valid, else AuthValidationError.
    """
    if not email or not re.match(RE_EMAIL, email): # Validate email is not empty and matches regex pattern for valid email format
        return AuthValidationError.INVALID_EMAIL # Return INVALID_EMAIL error if email format is invalid
    
    # If exists is specified, perform existence check against DB 
    if exists is not None:
        from lingual.models import User
        user = User.query.filter_by(email=email.lower()).first() # Query DB for user with matching email
        if exists and not user: # email should exist but not found
            return AuthValidationError.EMAIL_NOT_FOUND 
        if exists is False and user: # email should not exist but found
            return AuthValidationError.EMAIL_ALREADY_EXISTS

    return None # Return None if email is valid and passes existence check (if specified)

def validate_name(name: str) -> AuthValidationError | None:
    """ Validate name contains only letters, spaces, hyphens, and apostrophes. Returns None if valid, else AuthValidationError. """
    if not name or not re.match(RE_NAME, name): # Validate name is not empty and matches regex pattern for valid name format
        return AuthValidationError.INVALID_NAME # Return INVALID_NAME error if name format is invalid
    return None # Return None if name is valid and matches required format
