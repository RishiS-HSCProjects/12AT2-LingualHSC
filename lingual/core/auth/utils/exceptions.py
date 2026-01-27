class EmailSendingDisabledException(Exception):
    """Raised when email sending is disabled in the application configuration."""
    def __init__(self):
        super().__init__("Email sending is disabled in the application configuration.")