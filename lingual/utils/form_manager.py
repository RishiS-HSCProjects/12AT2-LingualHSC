from flask import flash, request
from datetime import date, datetime, time
from typing import Any, Dict, List, Optional
import re
import html

class FormError(Exception):
    """
    Custom exception class for form-related errors.
    Provides detailed information about what went wrong with form operations.
    """
    
    def __init__(self, message: str, field_name: Optional[str] = None, 
                 error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Initialize FormError with detailed error information.
        
        Args:
            message: Human-readable error message
            field_name: The field that caused the error (if applicable)
            error_code: Machine-readable error code for programmatic handling
            details: Additional context about the error
        """
        self.message = message
        self.field_name = field_name
        self.error_code = error_code
        self.details = details or {}
        
        # Construct full error message
        full_message = f"FormError: {message}"
        if field_name:
            full_message += f" (Field: {field_name})"
        if error_code:
            full_message += f" [Code: {error_code}]"
        
        super().__init__(full_message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON serialization."""
        return {
            'message': self.message,
            'field_name': self.field_name,
            'error_code': self.error_code,
            'details': self.details
        }

class FormSecurityError(FormError):
    """Specific exception for security-related form errors."""
    
    def __init__(self, message: str, field_name: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, field_name, error_code="SECURITY_ERROR", details=details)

class FormValidationError(FormError):
    """Specific exception for validation-related form errors."""
    
    def __init__(self, message: str, field_name: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, field_name, error_code="VALIDATION_ERROR", details=details)

class Form:
    """
    A secure form data container with validation and error handling.
    Provides protection against common security vulnerabilities.
    """
    
    # Security constants
    MAX_FIELD_NAME_LENGTH = 100
    MAX_STRING_VALUE_LENGTH = 10000
    MAX_FIELDS = 100
    FORBIDDEN_FIELD_PATTERNS = [
        r'^__.*__$',  # Dunder methods
        r'^_.*',      # Private attributes
        r'.*\.\.',    # Path traversal
        r'.*[<>].*',  # HTML tags
    ]
    
    def __init__(self, **data):
        """
        Initialize form with data, applying security checks.
        
        Args:
            **data: Form field data
            
        Raises:
            FormSecurityError: If security validation fails
            FormValidationError: If data validation fails
        """
        # Check number of fields
        if len(data) > self.MAX_FIELDS:
            raise FormSecurityError(
                f"Too many fields provided (max: {self.MAX_FIELDS})",
                details={'field_count': len(data)}
            )
        
        for field, value in data.items():
            self._validate_and_set_field(field, value)
    
    def _validate_field_name(self, field_name: str) -> None:
        """
        Validate field name for security concerns.
        
        Args:
            field_name: The field name to validate
            
        Raises:
            FormSecurityError: If field name is invalid or unsafe
        """
        if not isinstance(field_name, str):
            raise FormSecurityError(
                "Field name must be a string",
                field_name=str(field_name),
                details={'type': type(field_name).__name__}
            )
        
        if not field_name:
            raise FormSecurityError("Field name cannot be empty")
        
        if len(field_name) > self.MAX_FIELD_NAME_LENGTH:
            raise FormSecurityError(
                f"Field name too long (max: {self.MAX_FIELD_NAME_LENGTH})",
                field_name=field_name[:50] + "...",
                details={'length': len(field_name)}
            )
        
        # Check against forbidden patterns
        for pattern in self.FORBIDDEN_FIELD_PATTERNS:
            if re.match(pattern, field_name):
                raise FormSecurityError(
                    f"Field name matches forbidden pattern: {pattern}",
                    field_name=field_name,
                    details={'pattern': pattern}
                )
        
        # Only allow alphanumeric and underscores
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', field_name):
            raise FormSecurityError(
                "Field name must start with a letter and contain only alphanumeric characters and underscores",
                field_name=field_name
            )
    
    def _sanitize_value(self, value: Any) -> Any:
        """
        Sanitize field values to prevent injection attacks.
        
        Args:
            value: The value to sanitize
            
        Returns:
            Sanitized value
        """
        if isinstance(value, str):
            # Check string length
            if len(value) > self.MAX_STRING_VALUE_LENGTH:
                raise FormValidationError(
                    f"String value too long (max: {self.MAX_STRING_VALUE_LENGTH})",
                    details={'length': len(value)}
                )
            # Escape HTML entities to prevent XSS
            return html.escape(value)
        elif isinstance(value, (list, tuple)):
            return type(value)(self._sanitize_value(item) for item in value)
        elif isinstance(value, dict):
            return {k: self._sanitize_value(v) for k, v in value.items()}
        else:
            # For other types (int, float, bool, date, etc.), return as-is
            return value
    
    def _validate_and_set_field(self, field_name: str, value: Any) -> None:
        """
        Validate and set a field with security checks.
        
        Args:
            field_name: Name of the field
            value: Value to set
            
        Raises:
            FormSecurityError: If validation fails
        """
        self._validate_field_name(field_name)
        sanitized_value = self._sanitize_value(value)
        setattr(self, field_name, sanitized_value)

    def validate(self, data: dict) -> bool:
        """
        Validate form data against current form state.
        
        Args:
            data: Dictionary of field names and expected values
            
        Returns:
            True if all fields match, False otherwise
            
        Raises:
            FormValidationError: If validation encounters an error
        """
        try:
            for field, value in data.items():
                self._validate_field_name(field)
                if not hasattr(self, field) or getattr(self, field) != value:
                    return False
            return True
        except FormError:
            raise
        except Exception as e:
            raise FormValidationError(
                f"Unexpected error during validation: {str(e)}",
                details={'exception': type(e).__name__}
            )

    def get_data(self) -> dict:
        """
        Get all form data as a dictionary.
        
        Returns:
            Dictionary of field names and values
        """
        try:
            return {field: getattr(self, field) for field in self.__dict__}
        except Exception as e:
            raise FormError(
                f"Error retrieving form data: {str(e)}",
                error_code="DATA_RETRIEVAL_ERROR"
            )
    
    def set_field(self, field_name: str, value: Any) -> None:
        """
        Safely set a field value with validation.
        
        Args:
            field_name: Name of the field
            value: Value to set
            
        Raises:
            FormSecurityError: If field name is invalid
        """
        self._validate_and_set_field(field_name, value)
    
    def get_field(self, field_name: str, default: Any = None) -> Any:
        """
        Safely get a field value.
        
        Args:
            field_name: Name of the field
            default: Default value if field doesn't exist
            
        Returns:
            Field value or default
            
        Raises:
            FormSecurityError: If field name is invalid
        """
        self._validate_field_name(field_name)
        return getattr(self, field_name, default)
            
    @classmethod
    def from_flaskform(cls, flask_form):
        """
        Create Form instance from Flask-WTF form.
        
        Args:
            flask_form: Flask-WTF form instance
            
        Returns:
            Form instance
            
        Raises:
            FormError: If conversion fails
        """
        try:
            data = {field.name: field.data for field in flask_form}
            return cls(**data)
        except FormError:
            raise
        except Exception as e:
            raise FormError(
                f"Failed to create form from Flask form: {str(e)}",
                error_code="FLASK_FORM_CONVERSION_ERROR",
                details={'exception': type(e).__name__}
            )

    def clear_errors(self):
        """
        Clear all errors from form fields.
        Safe method that handles missing error attributes.
        """
        try:
            for field in self.__dict__:
                if hasattr(self, field) and hasattr(getattr(self, field), 'errors'):
                    getattr(self, field).errors.clear()
        except Exception as e:
            raise FormError(
                f"Error clearing form errors: {str(e)}",
                error_code="ERROR_CLEAR_FAILED"
            )

    def reset_form(self):
        """
        Reset all form data to None.
        Preserves field structure but clears values.
        """
        try:
            for field in list(self.__dict__.keys()):
                if hasattr(self, field):
                    setattr(self, field, None)
        except Exception as e:
            raise FormError(
                f"Error resetting form: {str(e)}",
                error_code="FORM_RESET_FAILED"
            )

    def validate_field(self, field_name: str, value: Any) -> bool:
        """
        Validate a specific field against a value.
        
        Args:
            field_name: Name of the field to validate
            value: Value to validate against
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            FormValidationError: If field doesn't exist or validation fails
        """
        self._validate_field_name(field_name)
        
        if not hasattr(self, field_name):
            raise FormValidationError(
                f"Field '{field_name}' does not exist in the form",
                field_name=field_name
            )
        
        try:
            field = getattr(self, field_name)
            return field.validate(value) if hasattr(field, 'validate') else True
        except Exception as e:
            raise FormValidationError(
                f"Error validating field: {str(e)}",
                field_name=field_name,
                details={'exception': type(e).__name__}
            )

    @classmethod
    def from_dict(cls, data: dict):
        """
        Create Form instance from dictionary.
        
        Args:
            data: Dictionary of field data
            
        Returns:
            Form instance
            
        Raises:
            FormError: If data is invalid
        """
        if not isinstance(data, dict):
            raise FormValidationError(
                "Data must be a dictionary",
                details={'type': type(data).__name__}
            )
        
        try:
            return cls(**data)
        except FormError:
            raise
        except Exception as e:
            raise FormError(
                f"Failed to create form from dictionary: {str(e)}",
                error_code="DICT_CONVERSION_ERROR",
                details={'exception': type(e).__name__}
            )

# Utility functions for Flask-WTF integration

def serialize_form_errors(form) -> Dict[str, List[str]]:
    """
    Serialize form errors to a dictionary for session storage.
    
    Args:
        form: Flask-WTF form instance
        
    Returns:
        Dictionary of field names to error lists
        
    Raises:
        FormError: If serialization fails
    """
    try:
        error_dict = {}
        for field, error_list in form.errors.items():
            error_dict[field] = error_list
        return error_dict
    except Exception as e:
        raise FormError(
            f"Failed to serialize form errors: {str(e)}",
            error_code="ERROR_SERIALIZATION_FAILED"
        )

def serialize_form_data(form) -> Dict[str, Any]:
    """
    Serialize form data to a dictionary for session storage.
    
    Args:
        form: Flask-WTF form instance
        
    Returns:
        Dictionary of field names to values
        
    Raises:
        FormError: If serialization fails
    """
    try:
        data = {}
        for field in form:
            if hasattr(field, 'data'):
                value = field.data
                if isinstance(value, (time, date)):
                    data[field.name] = value.isoformat()
                else:
                    data[field.name] = value
        return data
    except Exception as e:
        raise FormError(
            f"Failed to serialize form data: {str(e)}",
            error_code="DATA_SERIALIZATION_FAILED"
        )

def repopulate_form(form, form_data: Optional[Dict[str, Any]] = None, form_errors: Optional[Dict[str, List[str]]] = None):
    """
    Repopulate a WTForm with serialized data and errors.
    
    Args:
        form: Flask-WTF form instance
        form_data: Dictionary of field data to populate
        form_errors: Dictionary of field errors to attach
        
    Returns:
        Repopulated form
        
    Raises:
        FormError: If repopulation fails
    """
    form_data = form_data or {}
    form_errors = form_errors or {}
    
    def parse_date_field(date_string: str) -> date:
        """Parse ISO format date string."""
        try:
            return datetime.fromisoformat(date_string).date()
        except ValueError as e:
            raise FormValidationError(
                f"Invalid date format: {str(e)}",
                details={'date_string': date_string}
            )

    def parse_time_field(time_string: str) -> time:
        """Parse time string in HH:MM[:SS] format."""
        try:
            return datetime.strptime(time_string, "%H:%M:%S").time()
        except ValueError:
            try:
                return datetime.strptime(time_string, "%H:%M").time()
            except ValueError as e:
                raise FormValidationError(
                    f"Invalid time format: {str(e)}",
                    details={'time_string': time_string}
                )
    
    try:
        # Populate data
        for field_name, value in form_data.items():
            if not hasattr(form, field_name):
                continue
            
            field = getattr(form, field_name)
            
            if isinstance(value, str):
                if field_name == 'date':
                    field.data = parse_date_field(value)
                elif field_name in ['start_time', 'end_time']:
                    field.data = parse_time_field(value)
                else:
                    field.data = value
            else:
                field.data = value
        
        # Attach errors
        for field_name, errors in form_errors.items():
            if hasattr(form, field_name):
                getattr(form, field_name).errors = errors
        
        return form
    except FormError:
        raise
    except Exception as e:
        raise FormError(
            f"Failed to repopulate form: {str(e)}",
            error_code="FORM_REPOPULATION_FAILED"
        )

def flash_form_errors(form, form_errors: Dict[str, List[str]]) -> None:
    """
    Flash form errors stored in serialized format.
    
    Args:
        form: Flask-WTF form instance
        form_errors: Dictionary of field errors
        
    Raises:
        FormError: If flashing fails
    """
    try:
        for field_name, errors in form_errors.items():
            if not hasattr(form, field_name):
                continue
            
            field = getattr(form, field_name)
            for error in errors:
                # Sanitize error message before flashing
                safe_error = html.escape(str(error))
                flash(f"{field.label.text}: {safe_error}", 'danger')
    except Exception as e:
        raise FormError(
            f"Failed to flash form errors: {str(e)}",
            error_code="ERROR_FLASH_FAILED"
        )

def is_invalid_field(field_name: str, form_errors: Dict[str, List[str]]) -> bool:
    """
    Check if a form field has errors based on serialized form errors.
    
    Args:
        field_name: Name of the field to check
        form_errors: Dictionary of field errors
        
    Returns:
        True if field has errors, False otherwise
    """
    return field_name in form_errors and len(form_errors[field_name]) > 0

# === DRY Helper Functions for Common Form Operations ===

def save_form_to_session(form, session_obj, exclude_fields: Optional[List[str]] = None) -> None:
    """
    Save form data and errors to session (DRY helper).
    Automatically excludes password fields for security.
    
    Args:
        form: Flask-WTF form instance
        session_obj: Flask session object
        exclude_fields: Additional fields to exclude (passwords excluded by default)
    """
    if exclude_fields is None:
        exclude_fields = []
    
    # Always exclude password-related fields for security
    exclude_fields.extend(['password', 'confirm_password', 'new_password', 'old_password'])
    
    # Serialize and store form data
    form_data = serialize_form_data(form)
    
    # Remove sensitive fields
    for field in exclude_fields:
        form_data.pop(field, None)
    
    session_obj['form_data'] = form_data
    session_obj['form_errors'] = serialize_form_errors(form)

def restore_form_from_session(form, session_obj, flash_errors: bool = True, clear_session: bool = True) -> bool:
    """
    Restore form data and errors from session (DRY helper).
    
    Args:
        form: Flask-WTF form instance to populate
        session_obj: Flask session object
        flash_errors: Whether to flash errors to user
        clear_session: Whether to clear session data after restoring
        
    Returns:
        True if form was restored, False if no session data existed
    """
    form_data = session_obj.get('form_data', None)
    form_errors = session_obj.get('form_errors', None)
    
    # Nothing to restore
    if not form_data and not form_errors:
        return False
    
    # Repopulate form with saved data and errors
    if form_data or form_errors:
        repopulate_form(form, form_data or {}, form_errors or {})
        
        # Flash errors to user if requested
        if flash_errors and form_errors:
            flash_form_errors(form, form_errors)
    
    # Clear session data to prevent reuse
    if clear_session:
        session_obj.pop('form_data', None)
        session_obj.pop('form_errors', None)
    
    return True

def clear_form_session(session_obj) -> None:
    """
    Clear form data from session (DRY helper).
    Use this after successful form submission.
    
    Args:
        session_obj: Flask session object
    """
    session_obj.pop('form_data', None)
    session_obj.pop('form_errors', None)

def handle_form_success(session_obj) -> None:
    """
    Handle successful form submission (DRY helper).
    Clears form data from session.
    
    Args:
        session_obj: Flask session object
    """
    clear_form_session(session_obj)


def validate_ajax_form(form_class, data: Dict[str, Any], field_mappings: Optional[Dict[str, str]] = None) -> tuple[bool, Optional[str], Any]:
    """
    Validate a form for AJAX endpoints (DRY helper).
    Returns tuple of (success: bool, error_message: str or None, form: Form).
    
    Args:
        form_class: The Flask-WTF form class to instantiate
        data: Dictionary of form data to validate
        field_mappings: Optional mapping of data keys to form field names
        
    Returns:
        Tuple of (success, error_message, form)
        - success: True if valid, False otherwise
        - error_message: First error message if invalid, None if valid
        - form: The form instance
        
    Example:
        success, error, form = validate_ajax_form(EmailForm, {'email': 'test@test.com'})
        if not success:
            return jsonify({"error": error}), 400
    """
    # Apply field mappings if provided (e.g., {'user_email': 'email'})
    if field_mappings:
        mapped_data = {field_mappings.get(k, k): v for k, v in data.items()}
    else:
        mapped_data = data

    # Inject CSRF token from headers so Flask-WTF validation succeeds for JSON requests
    # This is necessary as AJAX requests do not automatically include CSRF tokens
    csrf_header = request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF-Token')
    if csrf_header:
        mapped_data = {**mapped_data, 'csrf_token': csrf_header}
    
    # Create and validate form
    form = form_class(data=mapped_data)
    
    if not form.validate():
        # Extract first error message for user-friendly response
        errors = [error for error_list in form.errors.values() for error in error_list]
        error_message = errors[0] if errors else "Validation failed"
        return False, error_message, form
    
    return True, None, form

def flash_all_form_errors(form) -> None:
    """
    Flash all errors from a form (DRY helper).
    Use this to display validation errors to the user.
    
    Args:
        form: Flask-WTF form instance
    """
    for errors in form.errors.values():
        for error in errors:
            flash(error, "error")
