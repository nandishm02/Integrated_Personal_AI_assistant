import os
import pickle
import base64
import re
import pyttsx3
import speech_recognition as sr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import Levenshtein
from bs4 import BeautifulSoup # Added for parsing HTML email bodies


SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/gmail.modify']


engine = pyttsx3.init()
recognizer = sr.Recognizer()

def speak(text):
    """Convert text to speech."""
    print("Gmail:", text)
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

def convert_speech_to_email_format(email):
    """Convert spoken words to email format."""
    email = email.replace(" at ", "@").replace(" dot ", ".").replace(" ", "")
    return email

def is_valid_email(email):
    """Validate the email address format."""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def gmail_authenticate():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('gmail', 'v1', credentials=creds)
    return service

def send_email(service, to, subject, body):
    message = MIMEMultipart()
    message['to'] = to
    message['subject'] = subject
    message.attach(MIMEText(body, 'plain'))
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message_body = {'raw': raw}
    service.users().messages().send(userId='me', body=message_body).execute()

def fetch_recipient_emails(service):
    """Fetch recipient emails from sent messages and save to a file."""
    results = service.users().messages().list(userId='me', labelIds=['SENT'], maxResults=100).execute()
    messages = results.get('messages', [])

    recipient_emails = set()  

    if not messages:
        print("No sent messages found.")
    else:
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            headers = msg['payload']['headers']
            for header in headers:
                if header['name'] == 'To':
                    recipients = header['value'].split(',')
                    for recipient in recipients:
                        recipient_emails.add(recipient.strip())  

    
    with open('recipient_emails.txt', 'w') as f:
        for email in recipient_emails:
            f.write(email + '\n')
    print("Recipient emails saved to recipient_emails.txt")

def load_recipient_emails():
    """Load recipient emails from a file."""
    if os.path.exists('recipient_emails.txt'):
        with open('recipient_emails.txt', 'r') as f:
            return [line.strip() for line in f.readlines()]
    return []

def find_closest_email(input_email, recipient_emails):
    """Find the email address with the highest similarity using Levenshtein distance."""
    best_match = None
    min_distance = float('inf')  
    for email in recipient_emails:
        distance = Levenshtein.distance(input_email, email)
        
        
        if distance < min_distance:
            min_distance = distance
            best_match = email
    return best_match


def voice_send_mail(to: str = None, subject: str = None, body: str = None):
    speak("Let's send an email.")
    service = gmail_authenticate() 
  
    if not to:
        speak("Who do you want to send the email to?")
        to_input = get_audio()
        if not to_input:
            speak("I couldn't understand the recipient.")
            return

        to = convert_speech_to_email_format(to_input)
        recipient_emails = load_recipient_emails()  
        closest_email = find_closest_email(to, recipient_emails)
        print(closest_email)
        if closest_email:
            speak(f"Did you mean {closest_email}?")
            confirmation = get_audio("Say yes to confirm or no to provide a different email.")
            if confirmation and "yes" in confirmation:
                to = closest_email
            else:
                speak("Please say the full email address of the recipient again.")
                return
    else:
       
        if not is_valid_email(to):
            speak(f"The email address {to} doesn't seem valid. Let's try again.")
            to = None
            return voice_send_mail(to, subject, body)  

    if not subject:
        speak("What is the subject of the email?")
        subject = get_audio()
        if not subject:
            speak("I couldn't understand the subject.")
            return

    if not body:
        speak("What is the message body?")
        body = get_audio()
        if not body:
            speak("I couldn't understand the message body.")
            return

    speak(f"Ready to send email to {to} with subject '{subject}' and body '{body}'. Should I send it?")
    confirmation = get_audio("Say yes to send or no to cancel.")
    
    if confirmation and "yes" in confirmation:
        send_email(service, to, subject, body)
        speak("Email sent successfully.")

        fetch_recipient_emails(service)
    else:
        speak("Email cancelled.")

def read_unread_emails(sender_filter: str = None, email_filter: str = None):
    """
    Reads unread emails, optionally filtered by sender name or email.
    Provides the information via voice.
    """
    service = gmail_authenticate()
    query = 'is:unread'
    if sender_filter:
        query += f' from:{sender_filter}'
    if email_filter:
        query += f' from:{email_filter}'

    try:
        results = service.users().messages().list(userId='me', q=query, maxResults=5).execute() # Limit to 5 for brevity
        messages = results.get('messages', [])

        if not messages:
            speak("You have no unread emails matching your criteria.")
            return

        speak(f"You have {len(messages)} unread emails matching your criteria.")
        for i, message in enumerate(messages):
            msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            headers = msg['payload']['headers']
            
            sender = "Unknown Sender"
            subject = "No Subject"
            
            for header in headers:
                if header['name'] == 'From':
                    sender = header['value']
                elif header['name'] == 'Subject':
                    subject = header['value']
            
            msg_body = ""
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                        msg_body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                    elif part['mimeType'] == 'text/html' and 'data' in part['body']:
                        html_body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        soup = BeautifulSoup(html_body, 'html.parser')
                        msg_body = soup.get_text()
                        break
            elif 'data' in msg['payload']['body']:
                msg_body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')

            # Clean up body for speaking
            msg_body_snippet = msg_body.strip().split('\n')[0] # Take first line
            if len(msg_body_snippet) > 100: # Limit snippet length
                msg_body_snippet = msg_body_snippet[:100] + "..."
            
            speak(f"Email {i+1} from {sender}. Subject: {subject}. Message snippet: {msg_body_snippet}")
            
            # Ask to mark as read
            speak("Would you like me to mark this email as read?")
            confirmation = get_audio("Say yes to mark as read or no to keep unread.")
            if confirmation and "yes" in confirmation:
                service.users().messages().modify(userId='me', id=message['id'], body={'removeLabelIds': ['UNREAD']}).execute()
                speak("Email marked as read.")
            else:
                speak("Email kept unread.")

    except Exception as e:
        speak("I encountered an error while trying to read your emails.")
        print(f"Error reading emails: {e}")

def count_unread_emails_by_sender():
    """
    Counts unread emails and provides a breakdown by sender via voice.
    This function is separate from read_unread_emails to maintain existing functionality.
    """
    service = gmail_authenticate()
    query = 'is:unread'

    try:
        results = service.users().messages().list(userId='me', q=query, maxResults=500).execute() # Increased maxResults for counting
        messages = results.get('messages', [])

        if not messages:
            speak("You have no unread emails.")
            return

        unread_counts = {}
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            headers = msg['payload']['headers']
            
            sender = "Unknown Sender"
            for header in headers:
                if header['name'] == 'From':
                    sender = header['value']
                    # Extract just the email address or name if available
                    match = re.search(r'<(.*?)>', sender)
                    if match:
                        sender = match.group(1)
                    else:
                        sender = sender.split('<')[0].strip() # Take name part if no email in <>
                    break
            
            unread_counts[sender] = unread_counts.get(sender, 0) + 1

        speak(f"You have a total of {len(messages)} unread emails.")
        speak("Here is the breakdown by sender:")
        for sender, count in unread_counts.items():
            speak(f"You have {count} unread emails from {sender}.")
            print(f"Unread emails from {sender}: {count}")

    except Exception as e:
        speak("I encountered an error while trying to count your unread emails.")
        print(f"Error counting emails: {e}")


if __name__ == "__main__":
    service = gmail_authenticate()
    fetch_recipient_emails(service)  
    # Example usage:
    # voice_send_mail()
    # read_unread_emails() # Reads all unread emails
    # read_unread_emails(sender_filter="John Doe") # Reads unread emails from John Doe
    # read_unread_emails(email_filter="example@domain.com") # Reads unread emails from example@domain.com
    # count_unread_emails_by_sender() # New function call
