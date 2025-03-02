# Description: Handles reading/writing events on the user's Google Calendar.


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

    def create_calendar_event(self, summary, description, start_time, end_time, attendees=None, create_meet_link=False):
        """
        Creates a calendar event.
        Attendees should be a list of dicts: [{'email': 'someone@example.com'}]
        """
        event_body = {
            'summary': summary,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': start_time.tzinfo.zone  # "America/New_York"
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': end_time.tzinfo.zone
            },
            'attendees': [
                {'email': attendees if attendees else []}
            ],
            'conferenceData': {
                'createRequest': {
                    'requestId': 'unique-req-id',
                    'conferenceSolutionKey': { 'type': 'hangoutsMeet' }
                }
            }
        }
        try:
            print("DEBUG: Attendees:", event_body['attendees'])
            event_result = self.service.events().insert(
                calendarId='primary',
                body=event_body,
                conferenceDataVersion=1
            ).execute()
            print(f"Event created: {event_result.get('htmlLink')}")
            return event_result
        except Exception as e:
            print(f"Error creating calendar event: {e}")
            return None