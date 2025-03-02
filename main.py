import os
import datetime
import pytz
import re
import time

# Google Auth libraries
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If you have a library called LangGraph, you can import from it:
# from langgraph import SomeLangGraphClass

import openai  # Using OpenAI for LLM-driven email parsing
from email.header import decode_header
from base64 import urlsafe_b64decode
from email.mime.text import MIMEText
import base64


from configLoader import load_config
from agents.gmailAgent import GmailAgent
from agents.calendarAgent import CalendarAgent
from agents.meetingScheduler import MeetingScheduler
from agents.authServices import get_gmail_service, get_calendar_service

def main():
    # Create Gmail/Calendar clients
    config = load_config()

    #Extracting the credentials from the config
    SCOPES = config["SCOPES"]
    creds_file = config["CREDENTIALS_FILE"]
    token_file = config["TOKEN_FILE"]
    local_timezone = config["LOCAL_TIMEZONE"]
    openai_api_key = config["OPENAI_API_KEY"]
    frequency = config.get("CHECK_EMAIL_FREQUENCY_SECONDS", 30)
    calendar_id  = config["CALENDAR_ID"]
    

    openai.api_key = openai_api_key

    gmail_service = get_gmail_service()
    calendar_service = get_calendar_service()

    # Wrap them in our agent classes
    gmail_agent = GmailAgent(gmail_service)
    calendar_agent = CalendarAgent(calendar_service)

    # Create our meeting scheduler
    scheduler = MeetingScheduler(gmail_agent, calendar_agent)

    # Start checking for new emails in a loop (blocking)
    scheduler.run_scheduler_loop()


if __name__ == '__main__':
    main()