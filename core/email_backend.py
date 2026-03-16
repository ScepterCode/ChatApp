# core/email_backend.py
import resend
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class ResendEmailBackend(BaseEmailBackend):
    """
    Custom Django email backend using Resend API.
    Replaces the default SMTP backend.
    
    Time complexity:  O(1)
    Space complexity: O(1)
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        resend.api_key = settings.RESEND_API_KEY
    
    def send_messages(self, email_messages):
        """
        Sends one or more EmailMessage objects via Resend API.
        Returns the number of messages successfully sent.
        """
        if not email_messages:
            return 0
        
        sent_count = 0
        
        for message in email_messages:
            try:
                params = {
                    "from": settings.DEFAULT_FROM_EMAIL,
                    "to": message.to,
                    "subject": message.subject,
                    "text": message.body,
                }
                
                # if message has HTML alternative, send that too
                for content, mimetype in getattr(message, 'alternatives', []):
                    if mimetype == 'text/html':
                        params["html"] = content
                        break
                
                resend.Emails.send(params)
                sent_count += 1
            
            except Exception as e:
                if not self.fail_silently:
                    raise e
        
        return sent_count