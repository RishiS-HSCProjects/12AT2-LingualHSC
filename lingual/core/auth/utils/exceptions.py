class EmailSendingDisabledException(Exception):
    """Raised when email sending is disabled in the application configuration."""
    def __init__(self, msg: str = ''):
        super().__init__(msg or "Email sending is disabled in the application configuration.")

class VerificationEmailError:
    """Namespace for verification email validation, configuration, or send failures."""

    class Base(Exception):
        def __init__(self, msg: str = '', status_code: int = 400, *args) -> None:
            self.status_code = status_code
            super().__init__(msg, *args)

    class NoReg(Base):
        def __init__(self, msg: str = '', status_code: int = 400, *args) -> None:
            super().__init__(msg or "Registration information not found. Please try again.", status_code, *args)

    class SMTPConfig(Base):
        def __init__(self, msg: str = '', status_code: int = 400, *args) -> None:
            super().__init__(msg or "Email service is not configured correctly.", status_code, *args)

    class SendFailure(Base):
        def __init__(self, msg: str = '', status_code: int = 400, *args) -> None:
            super().__init__(msg or "Unable to send verification email.", status_code, *args)
