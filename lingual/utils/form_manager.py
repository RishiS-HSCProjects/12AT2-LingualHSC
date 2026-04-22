from flask import flash, request
from datetime import date, datetime, time
from typing import Any, Dict, List, Optional
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
        """ Convert error to dictionary for JSON serialization. """
        return {
            'message': self.message,
            'field_name': self.field_name,
            'error_code': self.error_code,
            'details': self.details
        }

class FormSecurityError(FormError):
    """ Specific exception for security-related form errors. """
    
    def __init__(self, message: str, field_name: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, field_name, error_code="SECURITY_ERROR", details=details)

class FormValidationError(FormError):
    """Specific exception for validation-related form errors."""
    
    def __init__(self, message: str, field_name: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, field_name, error_code="VALIDATION_ERROR", details=details)

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
