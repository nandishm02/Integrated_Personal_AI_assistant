import requests
import json
import re


OLLAMA_API_BASE_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL_NAME = "mistral"  

def get_ollama_response(prompt: str) -> str | None:
    """
    Sends a prompt to the local Ollama API and returns the generated text.
    """
    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "model": OLLAMA_MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 2000
        }
    }

    try:
        response = requests.post(OLLAMA_API_BASE_URL, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("response")
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to Ollama API at {OLLAMA_API_BASE_URL}.")
        print(f"Please ensure Ollama is running and the model '{OLLAMA_MODEL_NAME}' is downloaded.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Ollama API request failed: {e}")
        return None
    except json.JSONDecodeError:
        print("Failed to decode JSON from Ollama response.")
        return None
    except KeyError:
        print("Unexpected Ollama response format.")
        return None

def analyze_command_with_ollama(command: str) -> dict:
    """
    Analyzes a voice command using the local Ollama LLM to extract intent and entities.
    Returns a dictionary with 'intent' and 'entities'.
    """
    
    prompt_template = """You are an AI assistant designed to analyze user voice commands and extract their intent and relevant entities.
Your output must be a JSON object with the following structure:
{{
  "intent": "string",
  "entities": {{
    "app_name": "string",
    "contact": "string",
    "message": "string",
    "date": "string",
    "time": "string",
    "note": "string",
    "recipient": "string",
    "subject": "string",
    "body": "string",
    "text_to_type": "string",
    "target_app": "string",
    "summary": "string",
    "question": "string",
    "sender_name": "string",
    "sender_email": "string"
  }}
}}

COMMAND ANALYSIS RULES:
1. For reading emails, the intent MUST be EXACTLY "read_unread_emails"
2. For sending emails, the intent MUST be EXACTLY "send_email"
3. For WhatsApp messages, the intent MUST be EXACTLY "send_whatsapp_message"
4. Use "sender_name" for names like "Google" or "John"
5. Use "sender_email" for email addresses like "noreply@google.com"

Here are some examples:

:User  "Open Notepad"
Output: {{"intent": "open_application", "entities": {{"app_name": "notepad"}}}}

:User  "Send a WhatsApp message to John saying hello"
Output: {{"intent": "send_whatsapp_message", "entities": {{"contact": "John", "message": "hello"}}}}

:User  "Remind me to buy groceries tomorrow at 5 PM"
Output: {{"intent": "set_reminder", "entities": {{"date": "tomorrow", "time": "5 PM", "note": "buy groceries"}}}}

:User  "Send an email to Alice with subject meeting update and body the meeting is rescheduled to Friday"
Output: {{"intent": "send_email", "entities": {{"recipient": "Alice", "subject": "meeting update", "body": "the meeting is rescheduled to Friday"}}}}

:User  "Type 'This is a test' into Microsoft Word"
Output: {{"intent": "type_into_application", "entities": {{"text_to_type": "This is a test", "target_app": "Microsoft Word"}}}}

:User  "Read my unread emails"
Output: {{"intent": "read_unread_emails", "entities": {{}}}}

:User  "Read unread emails from Google"
Output: {{"intent": "read_unread_emails", "entities": {{"sender_name": "Google"}}}}

:User  "Check new messages from noreply@google.com"
Output: {{"intent": "read_unread_emails", "entities": {{"sender_email": "noreply@google.com"}}}}

:User  "Show me emails from Amazon"
Output: {{"intent": "read_unread_emails", "entities": {{"sender_name": "Amazon"}}}}

:User  "Count my unread emails"
Output: {{"intent": "read_unread_emails", "entities": {{}}}}

:User  "How many unread emails do I have?"
Output: {{"intent": "read_unread_emails", "entities": {{}}}}

User  command: "{command}"
Output:
"""
    
    full_prompt = prompt_template.format(command=command)
    llm_raw_output = get_ollama_response(full_prompt)

    if llm_raw_output:
        try:
            json_string = llm_raw_output.strip()
            parsed_response = json.loads(json_string)
            
            intent = parsed_response.get("intent", "unknown")
            # Keep existing logic for read_unread_emails if needed, but ensure it doesn't conflict with new intent
            if "email" in intent.lower() and "read" in intent.lower() and "count" not in intent.lower():
                parsed_response["intent"] = "read_unread_emails"
            
            return parsed_response
        except json.JSONDecodeError:
            print(f"Could not parse Ollama response as JSON: {llm_raw_output}")
            
            # Fallback for email reading if LLM fails to parse JSON
            email_read_pattern = r'(read|check|show).*email.*(from|google)'
            if re.search(email_read_pattern, command, re.IGNORECASE):
                sender_match = re.search(r'from\s+([\w@\.\-]+)', command, re.IGNORECASE)
                if sender_match:
                    sender = sender_match.group(1)
                    if '@' in sender:
                        return {"intent": "read_unread_emails", "entities": {"sender_email": sender}}
                    else:
                        return {"intent": "read_unread_emails", "entities": {"sender_name": sender}}
                else:
                    return {"intent": "read_unread_emails", "entities": {}}
            
            # Fallback for email counting if LLM fails to parse JSON
            email_count_pattern = r'(count|how many).*unread email'
            if re.search(email_count_pattern, command, re.IGNORECASE):
                return {"intent": "read_unread_emails", "entities": {}}

            return {"intent": "unknown", "entities": {}}
    return {"intent": "unknown", "entities": {}}

if __name__ == "__main__":
    print("Testing Ollama LLM integration...")
    
    test_commands = [
        "Read unread emails from Google",
        "Check new messages from noreply@google.com",
        "Show me emails from Amazon",
        "Read my emails",
        "Check unread emails from GitHub",
        "Count my unread emails",
        "How many unread emails do I have?"
    ]
    
    for test_command in test_commands:
        result = analyze_command_with_ollama(test_command)
        print(f"Command: '{test_command}' -> Result: {result}")
