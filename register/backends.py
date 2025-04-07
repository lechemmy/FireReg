import ssl
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend

class NoVerifyEmailBackend(SMTPBackend):
    """
    Custom email backend that disables SSL certificate verification.
    This should only be used in development environments.
    """
    def open(self):
        if self.connection:
            return False
        
        # Create a custom SSL context with certificate verification disabled
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        return super().open()