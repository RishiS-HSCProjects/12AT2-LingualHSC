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
    code = StringField(
        'Verification Code',
        validators=[
            DataRequired(),
            Length(min=6, max=6, message="Verification code must be exactly 6 digits"),
            Regexp(r'^\d{6}$', message="Verification code must contain only digits")
        ]
    )

    submit = SubmitField('Verify')
    
    def validate_code(self, field):
        """Ensure code is exactly 6 digits."""
        if not field.data.isdigit():
            raise ValidationError("Verification code must contain only numbers")

class UserCreationForm(FlaskForm):
    """Form for final user account creation."""
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters long")
        ]
    )

    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match')
        ]
    )

    def validate_password(self, field):
        """Validate password strength."""
        password = field.data
        
        err = validate_password_strength(password)
        if err: raise ValidationError(str(err))

    def validate_confirm_password(self, field):
        """Validate confirm password strength."""
        confirm_password = field.data

        err = validate_password_strength(confirm_password)
        if err: raise ValidationError(str(err))        

class EmailVerificationRequestForm(FlaskForm):
    """Form for requesting email verification."""
    # No fields needed, just CSRF protection
    submit = SubmitField('Send Verification Code')

