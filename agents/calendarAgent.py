# Description: Handles reading/writing events on the user's Google Calendar.

import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class CalendarAgent:
    """
    Handles reading/writing events on the user's Google Calendar.
    """

    def __init__(self, service):
        self.service = service

    def get_calendar_events(self, start_time, end_time):
        """
        Fetches calendar events between start_time and end_time.
        """
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            return events
        except Exception as e:
            print(f"Error fetching calendar events: {e}")
            return []

    def create_calendar_event(self, summary, description, start_time, end_time, attendees=None):
        """
        Creates a calendar event.
        Attendees should be a list of dicts: [{'email': 'someone@example.com'}]
        """
        event_body = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': str(start_time.tzinfo)
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': str(end_time.tzinfo)
            },
            'attendees': attendees if attendees else []
        }
        try:
            event_result = self.service.events().insert(
                calendarId='primary',
                body=event_body
            ).execute()
            print(f"Event created: {event_result.get('htmlLink')}")
            return event_result
        except Exception as e:
            print(f"Error creating calendar event: {e}")
            return None