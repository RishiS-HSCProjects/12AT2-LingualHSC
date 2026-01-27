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
        raise ValueError("Unknown AuthValidationError")

RE_UPPERCASE = r'[A-Z]'
RE_LOWERCASE = r'[a-z]'
RE_DIGIT = r'\d'
RE_SPECIAL = r'[!@#$%^&*(),.?":{}|<>]'
RE_EMAIL = r"^(?!\.)(?!.*?\.\.)[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
RE_NAME = r"^[a-zA-Z\s\-']+$"

def validate_password_strength(password) -> AuthValidationError | None:
    if (
        not password
        or len(password) < 8
        or re.search(RE_UPPERCASE, password) is None
        or re.search(RE_LOWERCASE, password) is None
        or re.search(RE_DIGIT, password) is None
        or re.search(RE_SPECIAL, password) is None
    ):
        return AuthValidationError.WEAK_PASSWORD

    return None

def validate_email(email: str, exists: None | bool = None) -> AuthValidationError | None:
    """ Validate email format.
        If 'exist' is specified:
        - If exist is True, checks that email exists in DB.
        - If exist is False, checks that email does not exist in DB.

        Returns None if valid, else error message string.
    """
    if not email or not re.match(RE_EMAIL, email):
        return AuthValidationError.INVALID_EMAIL
    
    if exists is not None:
        from lingual.models import User
        user = User.query.filter_by(email=email.lower()).first()
        if exists and not user: # email should exist but not found
            return AuthValidationError.EMAIL_NOT_FOUND
        if exists is False and user: # email should not exist but found
            return AuthValidationError.EMAIL_ALREADY_EXISTS

    return None

def validate_name(name: str) -> AuthValidationError | None:
    """ Validate name contains only letters, spaces, hyphens, and apostrophes. Returns None if valid, else error message string. """
    if not name or not re.match(RE_NAME, name):
        return AuthValidationError.INVALID_NAME
    return None
