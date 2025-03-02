import datetime
from dateutil import parser
import pytz
import re
import time
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import openai
from email.header import decode_header
from base64 import urlsafe_b64decode
from email.mime.text import MIMEText
import base64
from configLoader import load_config
from agents.gmailAgent import GmailAgent
from agents.calendarAgent import CalendarAgent


class MeetingScheduler:
    """
    Orchestrates the logic:
      - Parse emails for proposed times using OpenAI
      - Check existing events for collisions
      - Communicate back/forth to finalize
      - Create meeting on Google Calendar
    """

    def __init__(self, config, calendar_agent: CalendarAgent, gmail_agent: GmailAgent ):
        self.config = config
        self.LOCAL_TIMEZONE = self.config["LOCAL_TIMEZONE"]
        self.gmail_agent = gmail_agent
        self.calendar_agent = calendar_agent

    def parse_email_for_proposed_times(self, email_body):
        """
        Uses OpenAI to parse natural language in the email to extract proposed times.
        Return a list of potential datetimes or an empty list.
        This is heavily simplified; in production you might use advanced prompt-engineering or extraction logic.
        """
        # prompt = f"""
        # The user email content is: 
        # {email_body}

        # The respondent might have proposed any meeting time in the email in words such as "Let's meet on Monday at 9:00 AM".
        # or "How about 10:00 AM on Tuesday?". or "Can we meet on Wednesday at 3:00 PM PST?".
        # Please extract any proposed meeting dates/times in a structured JSON format like:
        # [
        #     {{"day": "2025-03-10", "start_time": "9:00 AM", "end_time": "10:00 AM"}}
        # ]
        # If no proposals, return empty list: []
        # """
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        system_instructions =f"""
         You are a date/time extraction assistant for scheduling meetings.
        - Today's date is {today_str}. Keep this in context if someone says today/tonight or tomorrow or next week and so on!
        - If the user doesn't specify a year, assume the next occurrence of that date in current year which is 2025.
        - Return valid JSON only.
        - Provide a 24-hour time format (HH:MM) if the user says "2 PM", provide as 14:00.
        - If no times, return an empty list.
        - If the user specifies a timezone such as PST, or EST, use that. Otherwise, default to America/New_York.
        - Handle references like 'this Tuesday', '2 PM PST', or 'March 4th'.
        """

        user_content = f"""
        EMAIL BODY:
        {email_body}

        Return a JSON array of objects of the form:
        {{
        "day": "YYYY-MM-DD",  # if no year is mentioned, then it is 2025
        "start_time": "HH:MM", # 24 hours
        "end_time": "HH:MM",   # 24 hours
        "timezone": "e.g., default is America/New_York"
        }}
        If not sure, do your best guess. If multiple intervals, return an array with multiple objects.
        """

        try:
            # response = openai.chat.completions.create(
            # model="gpt-4o-mini",
            # messages=[{"role": "user", "content": prompt}],
            # max_tokens=150,
            # temperature=0.1
            # )
            response = openai.chat.completions.create(
                model="gpt-4o-mini",   # or "gpt-4"
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=300,
                temperature=0.0
            )
            raw_text = response.choices[0].message.content.strip()
            print("DEBUG: OpenAI raw response:", repr(raw_text))

            raw_text_no_fences = re.sub(r"```(\w*)", "", raw_text)
            raw_text_no_fences = raw_text_no_fences.replace("```", "").strip()

            print("DEBUG after fence removal:", raw_text_no_fences)
            # Attempt to parse as JSON. In production, handle exceptions carefully.
            import json
            proposals = json.loads(raw_text_no_fences)
            return proposals
        except Exception as e:
            print(f"OpenAI parse error: {e}")
            return []

    # def convert_to_localized_datetime(self, day_str, start_str, end_str, tz):
    #     """
    #     Convert the textual date/time strings to Python datetime objects in a given timezone.
    #     """
    #     localtz = pytz.timezone(tz)
    #     # Basic parse of day_str: "YYYY-MM-DD"
    #     year, month, day = map(int, day_str.split('-'))
    #     # Basic parse of times "HH:MM <AM/PM>"
    #     # This is simplistic – consider more robust time-parsing with dateutil, etc.
    #     def parse_time(t):
    #         match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)', t, re.IGNORECASE)
    #         if not match:
    #             return 0, 0
    #         hh, mm, ampm = match.groups()
    #         hh = int(hh)
    #         mm = int(mm)
    #         if ampm.lower() == 'pm' and hh != 12:
    #             hh += 12
    #         if ampm.lower() == 'am' and hh == 12:
    #             hh = 0
    #         return hh, mm

    #     sh, sm = parse_time(start_str)
    #     eh, em = parse_time(end_str)

    #     start_dt = localtz.localize(datetime.datetime(year, month, day, sh, sm))
    #     end_dt   = localtz.localize(datetime.datetime(year, month, day, eh, em))
    #     return start_dt, end_dt
        
    def convert_to_localized_datetime(self, day_str, start_time_str, end_time_str, tz="America/New_York"):
        """
        Use dateutil.parser to interpret the day/time strings more flexibly.
        If day_str is e.g. '2025-03-04', or 'March 4 2025', or the LLM 
        gave 'Tuesday, March 4, 2025' we rely on dateutil to parse them.
        """
        localtz = pytz.timezone(tz)

        # Combine day_str with start_time_str, let dateutil parse them together
        # e.g. "2025-03-04 2 PM" or "March 4, 2025 14:00"
        start_string = f"{day_str} {start_time_str}"
        end_string   = f"{day_str} {end_time_str}"

        naive_start = parser.parse(start_string)  # e.g. 2025-03-04 14:00:00
        naive_end   = parser.parse(end_string)

        # Localize or attach the time zone
        start_dt = localtz.localize(naive_start, is_dst=None)
        end_dt   = localtz.localize(naive_end, is_dst=None)

        return start_dt, end_dt

    def is_time_slot_free(self, start_dt, end_dt):
        """
        Check Google Calendar for collisions in the given time range.
        Returns True if free, False if busy.
        """
        events = self.calendar_agent.get_calendar_events(start_dt, end_dt)
        if events:
            return False
        return True

    def handle_incoming_email(self, subject, sender, body):
        """
        Main logic for responding to an incoming email with proposed times:
          - Extract proposed times (if any)
          - For each proposed time, check availability
          - If free, schedule. If not free, propose alternatives.
        """
        print(f"Handling email from {sender}, subject: {subject}")

        # Attempt to parse times from the email
        proposals = self.parse_email_for_proposed_times(body)
        if not proposals:
            # If the user didn't propose times, request them
            self.gmail_agent.send_email(
                to_email=sender,
                subject="Re: " + subject,
                body=(
                    "Hi there,\n\nI didn't see any meeting times proposed. "
                    "Could you let me know what times might work for you?\n\nThanks!"
                )
            )
            return

        # If proposals exist, check them one by one
        for proposal in proposals:
            day_str = proposal.get('day')
            start_str = proposal.get('start_time')
            end_str = proposal.get('end_time')

            start_dt, end_dt = self.convert_to_localized_datetime(day_str, start_str, end_str, self.LOCAL_TIMEZONE)
            # Check if free
            if self.is_time_slot_free(start_dt, end_dt):
                # Schedule meeting
                event = self.calendar_agent.create_calendar_event(
                    summary="Meeting with " + sender,
                    description="Auto-scheduled by AI Calendar Agent",
                    start_time=start_dt,
                    end_time=end_dt,
                    attendees=[sender],
                    create_meet_link=True
                )
                if event:
                    # Notify user
                    self.gmail_agent.send_email(
                        to_email=sender,
                        subject="Meeting Confirmed: " + subject,
                        body=(
                            f"Hi,\n\nYour proposed time {start_str}-{end_str} on {day_str} "
                            f"works! I've scheduled it on my calendar and sent you an invite as well. Meet link: {event.get('hangoutLink','N/A')} \n See you then!\n\nThanks."
                        )
                    )
                    return
                else:
                    # If event creation failed for some reason
                    self.gmail_agent.send_email(
                        to_email=sender,
                        subject="Re: " + subject,
                        body=(
                            "Hi,\n\nI tried to schedule the meeting but something went wrong. "
                            "Please try again or propose another time.\n\nThanks."
                        )
                    )
                    return
            else:
                # Not free, propose next or keep checking further proposals
                continue

        # If we exhausted all proposals and no free slot found:
        self.gmail_agent.send_email(
            to_email=sender,
            subject="Re: " + subject,
            body=(
                "Hi,\n\nUnfortunately, all your proposed times conflict with existing events. "
                "Could you suggest some additional times?\n\nThanks!"
            )
        )

    def run_scheduler_loop(self):
        """
        Periodically checks for new emails, processes them, and reacts accordingly.
        """
        print("Starting meeting scheduler loop. Press Ctrl+C to stop.")
        while True:
            messages = self.gmail_agent.check_new_messages(self.config["WHITELISTED_EMAILS"], self.config["SUBJECT_KEYWORDS"])
            for msg in messages:
                msg_id = msg['id']
                subject, sender, body = self.gmail_agent.get_message_details(msg_id)
                # Process the email
                print(f"Processing email: {subject} from {sender}\n")
                self.handle_incoming_email(subject, sender, body)
                # Mark message as read or archived if you like
                # For example, to mark as read:
                self.gmail_agent.service.users().messages().modify(
                    userId='me',
                    id=msg_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()

            # Sleep a bit before checking again
            time.sleep(1000)

