"""
Forms for the auth blueprint.
Handles email verification, OTP validation, and user creation forms.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Regexp, EqualTo
from lingual.core.auth.utils.utils import validate_password_strength

class OTPVerificationForm(FlaskForm):
    """Form for verifying OTP code."""
    # String field for the 6-digit verification code
    code = StringField(
        'Verification Code',
        validators=[
            DataRequired(),
            Length(min=6, max=6, message="Verification code must be exactly 6 digits"),
            Regexp(r'^\d{6}$', message="Verification code must contain only digits")
        ]
    )

    submit = SubmitField('Verify') # Submit button for the form (created for the text)
    
    def validate_code(self, field):
        """ Ensure code is exactly 6 digits. """
        if not field.data.isdigit():
            raise ValidationError("Verification code must contain only numbers")
        if len(field.data) != 6:
            raise ValidationError("Verification code must be exactly 6 digits long")

class UserCreationForm(FlaskForm):
    """ Form for final user account creation. Includes password and confirm password fields with validation. """
    password = PasswordField(
        'Password',
        validators=[ # Validaton not required since the password strength is checked in the validate_password method, but it is good to have a minimum requirements here as well
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters long")
        ]
    )

    confirm_password = PasswordField(
        'Confirm Password',
        validators=[ # Password strength not required here since it is checked in the validate_confirm_password method, which this field must match to 
            DataRequired(),
            EqualTo('password', message='Passwords must match')
        ]
    )

    def validate_password(self, field):
        """Validate password strength."""
        password = field.data
        
        err = validate_password_strength(password) # Validate password strength using utility function, which checks for length, uppercase, lowercase, digit, and special character requirements
        if err: raise ValidationError(str(err))

class EmailVerificationRequestForm(FlaskForm):
    """Form for requesting email verification."""
    # No fields needed, just CSRF protection
    submit = SubmitField('Send Verification Code')
