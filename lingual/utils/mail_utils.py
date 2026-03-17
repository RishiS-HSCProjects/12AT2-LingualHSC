from queue import Empty, Queue
from threading import Thread
from flask import current_app

def queue_email(
    recipients: list[str],
    subject: str,
    body: str,
) -> None:
    """
        Queue an email to be sent asynchronously by the background worker. 

        ## Parameters:
        - recipients: List of email addresses (strings) to send to.
        - subject: Subject line of the email.
        - body: Body text of the email.
    """

    allow_send_emails = current_app.config.get('ALLOW_SEND_EMAILS', True)
    mail_default_sender = current_app.config.get('MAIL_DEFAULT_SENDER')

    if not allow_send_emails:
        raise EmailError.EmailSendingDisabled()

    if not mail_default_sender:
        raise EmailError.SMTPConfig("Email service is not configured correctly. Missing default sender.")

    send_result_queue: Queue[EmailError.SendFailure | None] = Queue(maxsize=1) # Capture one async result/error.

    def send_email(app, result_queue: Queue[EmailError.SendFailure | None]):
        from lingual import mail
        with app.app_context():
            try:
                mail.send_message(
                    subject=subject,
                    recipients=recipients,
                    body=body
                )
                result_queue.put_nowait(None) # Indicate success.
            except Exception as e:
                app.logger.error(f"Threaded email send failed for {recipients}: {e}")
                try:
                    result_queue.put_nowait(EmailError.SendFailure("Unable to send email. Confirm the server has an active internet connection and try again."))
                except Exception:
                    pass # If the queue is full, we can't report the error back, but the email send failure is already logged.

    try:
        Thread(
            target=send_email, # Anonymously call send_email
            args=(current_app._get_current_object(), send_result_queue), # type: ignore -> Pass required values into async worker.
            daemon=True # Makes asynchronous to not halt application flow while sending email
        ).start()
    except Exception as e:
        current_app.logger.error(f"Error when starting verification email thread: {e}")
        raise EmailError.SendFailure("Something went wrong when sending the verification code.") from e
    
    cooldown = current_app.config.get('ASYNC_EMAIL_ERROR_WAIT_SECONDS', 1.5)

    if cooldown > 0:
        try:
            result = send_result_queue.get(timeout=cooldown) # Wait for async result or timeout.
            if result is not None:
                raise result # If async reported an error, raise it.
        except Empty:
            # No result from thread within wait time.
            # This is not necessarily an error, as email sending can be slow.

            # Log this occurrence for monitoring but proceed without raising an exception, allowing the email sending to continue asynchronously.
            current_app.logger.warning(f"No result from email thread after {cooldown} seconds for {recipients}. Proceeding without confirmation of email send success.")


# ########## #
# EXCEPTIONS #
# ########## #

class EmailError:
    """Namespace for verification email validation, configuration, or send failures."""

    class Base(Exception):
        def __init__(self, msg: str = '', status_code: int = 400, *args) -> None:
            self.status_code = status_code
            super().__init__(msg, *args)

    class EmailSendingDisabled(Base):
        def __init__(self, msg: str = '', status_code: int = 400, *args) -> None:
            super().__init__(msg or "Email sending is disabled in the application configuration.", status_code, *args)

    class SMTPConfig(Base):
        def __init__(self, msg: str = '', status_code: int = 400, *args) -> None:
            super().__init__(msg or "Email service is not configured correctly.", status_code, *args)

    class SendFailure(Base):
        def __init__(self, msg: str = '', status_code: int = 400, *args) -> None:
            super().__init__(msg or "Unable to send verification email.", status_code, *args)

