import speech_recognition as sr
import pyttsx3
from Wtsapp import send_whatsapp_message
from AppControl import open_application, is_known_app, open_website_search, close_application, load_installed_apps, type_into_application
from notifications import read_notifications
from reminder import set_reminder, list_reminders, delete_reminder
from gmail_integration import voice_send_mail, read_unread_emails, count_unread_emails_by_sender # Import the new function
import pyautogui
import time
import re
from datetime import datetime

from ollama_llm import analyze_command_with_ollama, get_ollama_response

load_installed_apps()
recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text: str):
    """Speak the text and print it."""
    print("Assistant:", text)
    engine.say(text)
    engine.runAndWait()

def get_audio(timeout=10, phrase_time_limit=10) -> str:
    """Listen on the microphone, return the recognized lower-case text, or None."""
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            print("Recognizing...")
            text = recognizer.recognize_google(audio)
            print("You said:", text)
            return text.lower()
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            speak("Sorry, I couldn't understand.")
            return None
        except sr.RequestError:
            speak("Network error.")
            return None

def parse_date_time_from_llm(date_str, time_str):
    """Parse date and time strings from LLM output into proper format."""
    try:
        date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
        
        date_formats = [
            "%d %B %Y",    # 25 August 2025
            "%d-%m-%Y",    # 25-08-2025
            "%d/%m/%Y",    # 25/08/2025
            "%B %d %Y",    # August 25 2025
        ]
        
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        
        if not parsed_date:
            return None, None
        
        time_str = time_str.upper().replace("AM", "").replace("PM", "").strip()
        if ":" in time_str:
            time_obj = datetime.strptime(time_str, "%H:%M")
        else:
            time_obj = datetime.strptime(time_str, "%H")
        
        final_datetime = datetime.combine(parsed_date.date(), time_obj.time())
        return final_datetime.strftime("%d-%m-%Y"), final_datetime.strftime("%H:%M")
        
    except Exception as e:
        print(f"Error parsing date/time: {e}")
        return None, None

def handle_send_message(entities: dict):
    """Handle the send_message intent using WhatsApp functionality."""
    contact = entities.get("contact") or entities.get("recipient")
    message = entities.get("message")
    
    if contact and message:
        speak(f"Sending WhatsApp message to {contact}.")
        send_whatsapp_message(contact=contact, message=message)
    else:
        speak("I need both a contact and a message to send a WhatsApp message.")
        
        send_whatsapp_message()

def handle_open_and_type(entities: dict):
    """Handle the open_application_and_type intent - open app and type text."""
    app_name = entities.get("app_name")
    text_to_type = entities.get("text_to_type")
    
    if app_name and text_to_type:
        if is_known_app(app_name):
            speak(f"Opening {app_name} and typing '{text_to_type}'.")
            if open_application(app_name):
                time.sleep(3)
                if type_into_application(app_name, text_to_type):
                    speak(f"Successfully typed into {app_name}.")
                else:
                    speak(f"Could not type into {app_name}.")
            else:
                speak(f"Failed to open {app_name}.")
        else:
            speak(f"I don't know how to open {app_name}.")
    else:
        speak("I need to know which application to open and what text to type.")

def listen_loop():
    """Main listening loop."""
    speak("Assistant is ready.")
    while True:
        command = get_audio(timeout=5, phrase_time_limit=6)
        if not command:
            continue

        print(f"Analyzing command with Ollama LLM: '{command}'")
        parsed_command = analyze_command_with_ollama(command)
        intent = parsed_command.get("intent")
        entities = parsed_command.get("entities", {})
        print(f"LLM parsed intent: {intent}, entities: {entities}")

        if intent == "greeting":
            speak("Yes, how can I assist you?")

        elif intent == "read_unread_emails":
            sender_name = entities.get("sender_name")
            sender_email = entities.get("sender_email")
            if sender_name or sender_email:
                speak(f"Checking for unread emails from {sender_name or sender_email}.")
                read_unread_emails(sender_filter=sender_name, email_filter=sender_email)
            else:
                # Use the new function for counting when no specific sender is mentioned
                speak("Counting your unread emails by sender.")
                count_unread_emails_by_sender()

        elif intent == "send_whatsapp_message" or intent == "send_message":
            handle_send_message(entities)

        elif intent == "open_application":
            app_name = entities.get("app_name")
            if app_name:
                if is_known_app(app_name):
                    speak(f"Opening application {app_name}")
                    open_application(app_name)
                else:
                    speak(f"Searching the web for {app_name}")
                    open_website_search(app_name)
            else:
                speak("Please specify which application to open.")

        elif intent == "open_application_and_type":
            handle_open_and_type(entities)

        elif intent == "close_application":
            app_name = entities.get("app_name")
            if app_name:
                if close_application(app_name):
                    speak(f"Closed {app_name}")
                else:
                    speak(f"Couldn't find any application named {app_name} to close.")
            else:
                speak("Please specify which application to close.")

        elif intent == "exit_assistant":
            speak("Okay, shutting down.")
            break

        elif intent == "read_notifications":
            read_notifications()

        elif intent == "clear_notifications":
            speak("Clearing all notifications.")
            pyautogui.hotkey('win', 'n')
            time.sleep(2)
            pyautogui.press('tab')
            pyautogui.press('enter')

        elif intent == "set_reminder":
            date_str = entities.get("date")
            time_str = entities.get("time")
            note = entities.get("note")
            
            if date_str and time_str and note:
                parsed_date, parsed_time = parse_date_time_from_llm(date_str, time_str)
                if parsed_date and parsed_time:
                    speak(f"Setting reminder for {parsed_date} at {parsed_time} about {note}.")
                    set_reminder(date_str=parsed_date, time_str=parsed_time, note=note)
                else:
                    speak("I couldn't understand the date or time format. Let's set it interactively.")
                    set_reminder()
            else:
                speak("Let's set a reminder.")
                set_reminder()

        elif intent == "list_reminders":
            list_reminders()

        elif intent == "delete_reminder":
            summary_to_delete = entities.get("summary")
            if summary_to_delete:
                speak(f"Attempting to delete reminder about {summary_to_delete}.")
                delete_reminder(summary_to_delete=summary_to_delete)
            else:
                speak("Please tell me which reminder to delete.")
                delete_reminder()

        elif intent == "send_email":
            recipient = entities.get("recipient")
            subject = entities.get("subject")
            body = entities.get("body")
            if recipient and subject and body:
                speak("Okay, sending that email.")
                voice_send_mail(to=recipient, subject=subject, body=body)
            else:
                speak("I need the recipient, subject, and body to send an email.")
                voice_send_mail()

        elif intent == "type_into_application":
            text_to_type = entities.get("text_to_type")
            target_app = entities.get("target_app")
            if text_to_type and target_app:
                speak(f"Opening {target_app} and typing '{text_to_type}'.")
                if type_into_application(target_app, text_to_type):
                    speak("Text typed successfully.")
                else:
                    speak(f"Could not type into {target_app}. The application may not be available.")
            else:
                speak("Please tell me what to type and into which application.")

        elif intent == "answer_question": 
            question = entities.get("question")
            if question:
                speak(f"Let me find that for you.")
                answer = get_ollama_response(question)
                if answer:
                    speak(answer)
                else:
                    speak("I couldn't find an answer to that question.")
            else:
                speak("What question would you like me to answer?")

        elif intent == "unknown":
            speak("I'm sorry, I didn't understand that command. Could you please rephrase?")
        else:
            speak("Command not yet implemented or recognized.")

if __name__ == "__main__":
    listen_loop()
