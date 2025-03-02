import base64
from email.mime.text import MIMEText

class GmailAgent:
    """
    Handles sending and receiving emails using Gmail API.
    """

    def __init__(self, service):
        self.service = service

    def check_new_messages(self, WHITELISTED_EMAILS, SUBJECT_KEYWORDS):
        query  = self.build_gmail_query(WHITELISTED_EMAILS, SUBJECT_KEYWORDS, True)
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


    def build_gmail_query(self, whitelisted_addresses, subject_keywords, unread_only=True):
        """
        Build a Gmail search query like:
        'is:unread from:(addr1 OR addr2) subject:(keyword1 OR keyword2)'
        """
        # e.g. from:(addr1 OR addr2 OR addr3)
        from_part = " OR ".join(whitelisted_addresses)
        # e.g. subject:(keyword1 OR keyword2 OR keyword3)
        subject_part = " OR ".join(subject_keywords)

        # Construct final string
        query_parts = []
        if unread_only:
            query_parts.append("is:unread")

        # "from:(addr1 OR addr2 OR addr3)"
        if whitelisted_addresses:
            query_parts.append(f"from:({from_part})")

        # "subject:(Dinner OR Meeting OR ...)"
        if subject_keywords:
            # If you have spaces in the keywords, you might need quotes around them
            # for safety, but let's keep it simple:
            query_parts.append(f"subject:({subject_part})")

        # Join everything with spaces
        query_str = " ".join(query_parts)
        return query_str