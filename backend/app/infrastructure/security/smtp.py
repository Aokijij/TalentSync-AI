import hashlib
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate

from app.application.ports.services import MailDeliveryError


class SmtpDelivery:
    def __init__(self, settings):
        self.settings = settings

    def send(self, *, recipient, subject, body, message_id):
        config = self.settings
        if not config.smtp_enabled:
            raise MailDeliveryError(retryable=False, kind="configuration")
        try:
            message = EmailMessage()
            message["From"], message["To"], message["Subject"] = config.smtp_from, recipient, subject
            message["Date"] = formatdate(localtime=False)
            namespace = hashlib.sha256(("mail:" + config.secret_key).encode()).hexdigest()[:16]
            message["Message-ID"] = f"<talentsync-{namespace}-{message_id}@{config.smtp_from.rsplit('@', 1)[1]}>"
            message.set_content(body)
            context = ssl.create_default_context()
            transport = smtplib.SMTP_SSL if config.smtp_security == "ssl" else smtplib.SMTP
            options = {"context": context} if config.smtp_security == "ssl" else {}
            with transport(config.smtp_host, config.smtp_port, timeout=15, **options) as smtp:
                smtp.ehlo()
                if config.smtp_security == "starttls":
                    smtp.starttls(context=context)
                    smtp.ehlo()
                if config.smtp_username:
                    smtp.login(config.smtp_username, config.smtp_password)
                refused = smtp.send_message(message, from_addr=config.smtp_from, to_addrs=[recipient])
                if refused:
                    retryable = any(code < 500 for code, _ in refused.values())
                    raise MailDeliveryError(retryable=retryable, kind="temporary" if retryable else "permanent")
        except (smtplib.SMTPAuthenticationError, smtplib.SMTPNotSupportedError, ssl.SSLError, ValueError, IndexError):
            raise MailDeliveryError(retryable=False, kind="configuration") from None
        except smtplib.SMTPRecipientsRefused as error:
            retryable = any(code < 500 for code, _ in error.recipients.values())
            raise MailDeliveryError(retryable=retryable, kind="temporary" if retryable else "permanent") from None
        except smtplib.SMTPResponseException as error:
            retryable = error.smtp_code < 500
            raise MailDeliveryError(retryable=retryable, kind="temporary" if retryable else "permanent") from None
        except (smtplib.SMTPException, OSError):
            raise MailDeliveryError(retryable=True, kind="transport") from None
