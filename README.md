# CalendarAgent

**CalendarAgent** is a Python-based automation tool that integrates with **Gmail** and **Google Calendar** to:
1. Read and parse incoming emails from specific (“whitelisted”) addresses.
2. Negotiate meeting times (via email) using an AI prompt (OpenAI).
3. Check for calendar conflicts.
4. Schedule events automatically (including a Google Meet link if desired).
5. Invite the email sender, ensuring both parties have the event in their calendars.

---

## Table of Contents
1. [Features](#features)
2. [Prerequisites](#prerequisites)
3. [Setup and Installation](#setup-and-installation)
4. [Configuration](#configuration)
   - [config.yaml](#configyaml)
   - [Whitelisted Emails](#whitelisted-emails)
   - [Subject Keywords](#subject-keywords)
5. [Usage](#usage)
6. [Authentication and Security](#authentication-and-security)
7. [How It Works](#how-it-works)
8. [Known Limitations / Future Improvements](#known-limitations--future-improvements)
9. [License](#license)

---

## Features
- **Gmail Integration**: Uses the Gmail API to read incoming emails from a configurable whitelist and subject filter.  
- **LLM Parsing**: Extracts proposed times from unstructured email text using OpenAI’s ChatCompletion (or a fallback library like `dateutil`/`dateparser`).  
- **Calendar Coordination**: Checks your Google Calendar for conflicts and schedules the first available time.  
- **Automated Reply**: Notifies the sender via email to confirm or request alternative times.  
- **Google Meet**: Optionally creates a Meet link and adds it to the event.  
- **Configurable**: Store all key settings (OAuth scopes, whitelisted emails, subject keywords, etc.) in a YAML config file.

---

## Prerequisites
1. **Python 3.9+** (or your preferred version).  
2. **Google Cloud Console** credentials for OAuth (download the `credentials.json` file).  
3. **OpenAI API Key** (if you plan to use ChatCompletion for advanced date/time extraction).  
4. (Optional) **Docker** if you want to containerize.

---

## Setup and Installation

1. **Clone** this repository:
   ```bash
   git clone https://github.com/YourUsername/CalendarAgent.git
   cd CalendarAgent

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Make sure you have google-api-python-client, google-auth-httplib2, google-auth-oauthlib, openai, pytz, and optionally python-dotenv installed.

3. Obtain credentials.json:

Create a Google Cloud project at Google Cloud Console.
Enable Gmail and Calendar APIs.
Configure the OAuth consent screen.
Generate OAuth client ID credentials for a Desktop or Web application.
Download the credentials.json to the root of this project (or specify the path in config.yaml).

4. (Optional) Add .env:
If you want to keep secrets (like OPENAI_API_KEY) out of the main config, create a file called .env:
```bash
OPENAI_API_KEY=sk-...
```
Ensure you load it with dotenv in your code if you’re referencing environment variables.
Run the project:

```bash
python main.py
```
The first time, you’ll be prompted to authorize via a local browser window. After authorization, a token.json file will be created to store your refresh tokens.

5. Configuration
*config.yaml*
Inside the config/ folder, you’ll find a config.yaml (or you might create one). Example contents:

```yaml
SCOPES:
  - https://www.googleapis.com/auth/gmail.modify
  - https://www.googleapis.com/auth/gmail.send
  - https://www.googleapis.com/auth/calendar

CREDENTIALS_FILE: "credentials.json"
TOKEN_FILE: "token.json"

LOCAL_TIMEZONE: "America/New_York"
CALENDAR_ID: "primary"

OPENAI_API_KEY: "${OPENAI_API_KEY}"  # Or put your key directly, e.g., 'sk-123abc...'

CHECK_EMAIL_FREQUENCY_SECONDS: 30

WHITELISTED_ADDRESSES:
  - "divyamsharma1999@gmail.com"
  - <Add more>

SUBJECT_KEYWORDS:
  - "Dinner"
  - "Meeting"
  - "Interview"
  - "Invite"
  - "Date"
```

6. **Key Fields:**

SCOPES: Must include Gmail and Calendar scopes. If you want to modify or send emails, do not use gmail.readonly.
CREDENTIALS_FILE & TOKEN_FILE: Paths to your OAuth credentials.
WHITELISTED_ADDRESSES: Only emails from these addresses are processed.
SUBJECT_KEYWORDS: Subject filters. The agent only processes emails if at least one of these keywords is in the subject.
OPENAI_API_KEY: If you store it directly, it can be 'sk-...'. If you want to load from environment, use '${OPENAI_API_KEY}' and handle expansion in your code.

**Whitelisted Emails**
Any address not in WHITELISTED_ADDRESSES is ignored by the agent (or can be marked as read, but not processed). This ensures the agent doesn’t spam replies to random or unwanted emails.

**Subject Keywords**
Only emails containing at least one of these keywords will be considered a “meeting request.” For example, if the user’s subject is “Dinner Date,” and “Dinner” is in your list, it matches.

7. **Usage**
Run python main.py.
The agent enters its scheduler loop, checking for unread messages that match your config filters (e.g., from whitelisted emails, containing your keywords).
If a matching email is found:
It passes the message to the OpenAI (or date parser) logic to extract times.
Checks your calendar to see if those times are free.
Schedules the first available time and replies to confirm. If no times are free, it requests more options.
The agent sleeps for the interval specified in CHECK_EMAIL_FREQUENCY_SECONDS and repeats.
Authentication and Security
OAuth: You must complete a one-time local OAuth flow. Google will generate a token.json storing your refresh token. Keep this file safe.
OpenAI Key: If you store your OPENAI_API_KEY in .env or config.yaml, avoid committing it to public repos.
Scope Limitations: Using https://www.googleapis.com/auth/gmail.modify allows the agent to mark messages as read or remove labels. If you only want read-only, you lose the ability to mark messages read. Similarly, https://mail.google.com/ is broader.
Whitelisting addresses is recommended to avoid responding to spam or undesired messages.

8. **How It Works**
**GmailAgent:**
Authenticates with Gmail via the OAuth credentials in CREDENTIALS_FILE.
Periodically checks for unread messages that match the query built from:
```csharp
is:unread from:(WHITELISTED_ADDRESSES) subject:(SUBJECT_KEYWORDS)
```

Retrieves email details (subject, sender, body) for matching emails.

**OpenAI (or parser) step:**
Takes the email body text and tries to extract proposed date/time.
If no times found, the agent replies requesting times.
If times found, it iterates until it finds an available slot on your calendar.

**CalendarAgent:**
Uses Google Calendar API to check for conflicts.
If a free slot is found, creates an event with the chosen start/end time, includes a Google Meet link if configured, and invites the sender.

**Confirmation Email:**
Notifies the sender that the meeting was scheduled successfully.
If all proposed times are busy, requests alternative proposals.

9. **Known Limitations / Future Improvements**
    
**Relative Dates:** Handling phrases like “tonight,” “tomorrow,” or “next week” requires special logic or user prompts to confirm the date.

**Multi-turn:** If the user doesn’t respond right away or needs multiple back-and-forth steps, you can expand the logic or store conversation states.

**Time Zones:** The user might mention “PST” or “UTC” while your default is “America/New_York.” Additional logic needed if you want a perfect cross-timezone scheduling.

**Threading:** The agent checks for new messages on a timer. You could integrate webhooks or other triggers for faster response.

**Auto-Suggestions:** You might want to automatically propose alternate times instead of just “No time is free. Please propose more options.”
