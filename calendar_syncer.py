import os
import sys
import json
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import config

# Scope and credential file settings loaded from central config
SCOPES = config.SCOPES
CLIENT_SECRET_FILE = config.CLIENT_SECRET_FILE
TOKEN_FILE = config.TOKEN_FILE

def get_calendar_service():
    """Authenticates the user and returns the Google Calendar API service instance."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_FILE):
                print(
                    f"[Google API Error] Missing '{CLIENT_SECRET_FILE}'.\n"
                    "Please download your OAuth client ID credentials JSON from the Google Cloud Console,\n"
                    "save it in this directory, and rename it to 'credentials.json'."
                )
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)

def insert_event_to_google(event_data: dict) -> dict:
    """
    Reads structured JSON data, maps it, and calls insert_event() 
    (service.events().insert) to add it to Google Calendar.
    """
    try:
        service = get_calendar_service()
    except Exception as e:
        print(f"[Auth Error] Failed to initialize Google Calendar client: {e}")
        return {"error": "Authentication failed", "details": str(e)}

    # Map the analyzed JSON schema fields to standard Google Calendar Event body
    summary = event_data.get("summary", "New Event")
    start_time = event_data.get("datetime")
    
    if not start_time:
        print("[Error] No datetime provided in input event data.")
        return {"error": "Missing datetime parameter"}

    # Set default end time (+1 hour if duration not specified)
    duration = event_data.get("duration_minutes") or 60
    # Create simple RFC3339 formatted end time if needed
    # Note: Google Calendar requires start/end times in ISO/RFC3339 format
    
    event_body = {
        "summary": summary,
        "description": f"Automatically generated event from local analyzer.\nIntent: {event_data.get('intent', 'N/A')}",
        "start": {
            "dateTime": start_time,
            "timeZone": config.TIMEZONE,
        },
        "end": {
            "dateTime": start_time, # Fallback, update below if you have duration parsing
            "timeZone": config.TIMEZONE,
        },
    }

    # If duration is specified, parse start and calculate end offset
    try:
        from datetime import datetime, timedelta
        # Parse timezone offset (e.g. Z or +07:00)
        if start_time.endswith("Z"):
            dt_start = datetime.fromisoformat(start_time[:-1])
        else:
            # Handle standard offsets
            dt_start = datetime.fromisoformat(start_time)
        
        dt_end = dt_start + timedelta(minutes=duration)
        event_body["end"]["dateTime"] = dt_end.isoformat()
    except Exception:
        # Fallback end time if parsing fails
        event_body["end"]["dateTime"] = start_time

    # Add participants as attendees if available
    participants = event_data.get("participants", [])
    if participants:
        event_body["attendees"] = [{"email": email} if "@" in email else {"displayName": email} for email in participants]

    try:
        # Call events().insert API to upload event to primary calendar
        event_result = service.events().insert(
            calendarId="primary", 
            body=event_body
        ).execute()
        
        print(f"✅ Event successfully created!")
        print(f"Event Link: {event_result.get('htmlLink')}")
        return event_result
        
    except HttpError as error:
        print(f"[Google API Error] Failed to create event: {error}")
        return {"error": "API Call Failed", "details": str(error)}

if __name__ == "__main__":
    # Sample structured JSON representing analyzed output from Layer 2 (Ollama / Regex)
    sample_layer2_output = {
        "intent": "Meeting",
        "summary": "Mai 9h họp",
        "datetime": "2026-06-04T09:00:00+07:00", # Parsed execution schedule
        "duration_minutes": 60,
        "participants": []
    }
    
    print("Reading analyzed event data from Layer 2...")
    print(json.dumps(sample_layer2_output, indent=2))
    
    print("\nRunning Google Calendar Sync...")
    insert_event_to_google(sample_layer2_output)
