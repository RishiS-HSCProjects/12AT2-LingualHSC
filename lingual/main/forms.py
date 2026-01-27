from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, ValidationError
from wtforms.validators import DataRequired, Email, Length, EqualTo
import re

from lingual.core.auth.utils.utils import validate_email, validate_name, validate_password_strength

class LoginForm(FlaskForm):
    """ Form for user login. """
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

    # Email and password validation is handled in the route logic.
    pass

class RequestForm(FlaskForm):
    """ Form for requesting password reset. """
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    # Email validation is handled in the route logic.
    pass

class PasswordResetForm(FlaskForm):
    """ Form for resetting password with token. """
    password = PasswordField(
        'New Password',
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
    submit = SubmitField('Reset Password')
    
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

class RegistrationLanguageForm(FlaskForm):
    """Form for selecting language during registration."""
    language = SelectField(
        'Preferred Language',
        validators=[DataRequired()],
        choices=[]  # Will be populated dynamically
    )

class RegistrationNameForm(FlaskForm):
    """Form for entering name during registration."""
    first_name = StringField(
        'First Name',
        validators=[
            DataRequired(),
            Length(min=1, max=50, message="First name must be between 1 and 50 characters")
        ]
    )
    
    def validate_first_name(self, field):
        """Validate name contains only letters, spaces, hyphens, and apostrophes."""
        err = validate_name(field.data)
        if err: raise ValidationError(str(err))

class RegistrationEmailForm(FlaskForm):
    """Form for entering email during registration."""
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(),
            Length(max=120, message="Email must be less than 120 characters")
        ]
    )
    
    def validate_email(self, field):
        """Custom email validation with regex."""
        err = validate_email(field.data, exists=False)
        if err: raise ValidationError(str(err))

class RegistrationPasswordForm(FlaskForm):
    """Form for setting password during registration."""
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
