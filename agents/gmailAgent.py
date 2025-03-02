import base64
from email.mime.text import MIMEText

class GmailAgent:
    """
    Handles sending and receiving emails using Gmail API.
    """

    def __init__(self, service):
        self.service = service

    def check_new_messages(self, query='is:unread'):
        """
        Checks for new unread messages matching the given query.
        Returns a list of message data.
        """
        try:
            response = self.service.users().messages().list(
                userId='me', q=query
            ).execute()
            messages = []
            if 'messages' in response:
                messages = response['messages']
            return messages
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return []

    def get_message_details(self, msg_id):
        """
        Fetch message details and decode the body.
        """
        message = self.service.users().messages().get(
            userId='me', id=msg_id, format='full'
        ).execute()

        payload = message.get('payload', {})
        headers = payload.get('headers', [])
        subject, sender = None, None

        for h in headers:
            if h['name'] == 'Subject':
                subject = h['value']
            if h['name'] == 'From':
                sender = h['value']

        # Find message body
        parts = payload.get('parts', [])
        body = ""
        if not parts:
            body_data = payload.get('body', {}).get('data', '')
            body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='replace')
        else:
            for part in parts:
                if part.get('mimeType') == 'text/plain':
                    body_data = part.get('body', {}).get('data', '')
                    body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='replace')
                    break

        return subject, sender, body

    def send_email(self, to_email, subject, body):
        """
        Sends an email to the specified address.
        """
        message = MIMEText(body)
        message['to'] = to_email
        message['subject'] = subject

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        try:
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            print(f"Email sent to {to_email} with subject: {subject}")
        except Exception as e:
            print(f"Error sending email: {e}")