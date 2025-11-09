import os
import pickle
import pyttsx3
import speech_recognition as sr
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


engine = pyttsx3.init()
recognizer = sr.Recognizer()
SCOPES = ['https://www.googleapis.com/auth/calendar']

def speak(text):
    """Convert text to speech."""
    print("Reminder:", text)
    engine.say(text)
    engine.runAndWait()

def get_audio(prompt=None):
    """Listen on the microphone and return the recognized lower-case text, or None."""
    if prompt:
        speak(prompt)
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=7)
            text = recognizer.recognize_google(audio)
            print("You said:", text)
            return text.lower()
        except Exception:
            speak("Sorry, I couldn't understand.")
            return None

def authenticate_google_calendar():
    """Authenticate and return the Google Calendar service."""
    creds = None
    if os.path.exists('token1.pickle'):
        with open('token1.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials1.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token1.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('calendar', 'v3', credentials=creds)
    return service

def schedule_reminder(date_str, time_str, note):
    """Schedule a reminder in Google Calendar."""
    try:

        dt = datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M")
        service = authenticate_google_calendar()

        event = {
            'summary': note,
            'start': {
                'dateTime': dt.isoformat(),
                'timeZone': 'Asia/Kolkata',  
            },
            'end': {
                'dateTime': (dt + timedelta(hours=1)).isoformat(),  
                'timeZone': 'Asia/Kolkata',  
            },
        }

        service.events().insert(calendarId='primary', body=event).execute()
        speak(f"Reminder set for {date_str} at {time_str}.")
    except ValueError:
        speak("I couldn't understand the date or time format provided. Please try again.")
    except Exception as e:
        speak("There was an error in setting the reminder.")
        print(f"Error: {e}")


def set_reminder(date_str: str = None, time_str: str = None, note: str = None):
    speak("Let's set a reminder.")

    if not date_str:
        date_input = get_audio("Say the date in day month year format, like sixteen May twenty twenty five.")
        if not date_input:
            speak("Date not recognized.")
            return
        try:
            date_obj = datetime.strptime(date_input, "%d %B %Y")
            date_str = date_obj.strftime("%d-%m-%Y")
        except Exception:
            speak("Couldn't understand the date format. Please try again.")
            return

    if not time_str:
        time_input = get_audio("Say the time in 24-hour format, like fifteen thirty or 4:30.")
        if not time_input:
            speak("Time not recognized.")
            return
        time_str = time_input  

    if not note:
        note = get_audio("What should I remind you about?")
        if not note:
            speak("Note not recognized.")
            return

    schedule_reminder(date_str, time_str, note)

def list_reminders():
    """List upcoming reminders from Google Calendar."""
    service = authenticate_google_calendar()
    now = datetime.utcnow().isoformat() + 'Z'  
    events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        speak("No upcoming reminders found.")
        print("No upcoming reminders found.")
    else:
        speak("Here are your upcoming reminders:")
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event['summary']
            print(f"{start}: {summary}")
            speak(f"{start}: {summary}")


def delete_reminder(summary_to_delete: str = None):
    """Delete a reminder from Google Calendar."""
    service = authenticate_google_calendar()

    if not summary_to_delete:
        speak("Please say the summary of the reminder you want to delete.")
        summary_to_delete = get_audio()

    if not summary_to_delete:
        speak("No summary recognized. Cannot delete reminder.")
        return

    now = datetime.utcnow().isoformat() + 'Z'  
    events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    found_and_deleted = False
    for event in events:
        if event['summary'].lower() == summary_to_delete.lower(): 
            service.events().delete(calendarId='primary', eventId=event['id']).execute()
            speak(f"Reminder '{summary_to_delete}' has been deleted.")
            print(f"Deleted reminder: {summary_to_delete}")
            found_and_deleted = True
            break  

    if not found_and_deleted:
        speak("No reminder found with that summary.")
        print("No reminder found with that summary.")
