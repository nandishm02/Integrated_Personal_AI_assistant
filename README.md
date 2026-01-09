# Integrated Personal AI Assistant

The Integrated Personal AI Assistant is a software system designed to assist users in performing everyday digital tasks through voice commands and intelligent automation. The project aims to reduce the need for switching between multiple applications by providing a single, unified assistant capable of understanding natural language and executing tasks efficiently.

This project was developed as part of the Bachelor of Engineering curriculum in Artificial Intelligence and Data Science.

---

## Project Description

Modern users interact with several applications for communication, scheduling, reminders, and information retrieval. This fragmented workflow increases cognitive load and reduces productivity. The Integrated Personal AI Assistant addresses this problem by combining multiple services into one intelligent system.

The assistant listens to voice commands, understands user intent using natural language processing, and performs actions such as sending messages, managing emails, setting reminders, and controlling desktop applications. A web-based interface provides real-time feedback on the assistant’s status and activities.

---

## Key Functionalities

- Voice-based command recognition
- Natural language understanding using a local language model
- Desktop application control
- WhatsApp message automation
- Gmail integration for sending emails
- Google Calendar integration for reminders
- Notification reading
- Real-time web dashboard with activity logs and system status

---

## System Architecture

The system follows a client–server architecture.

- The backend is developed in Python and handles speech recognition, intent analysis, and task execution.
- A local Large Language Model (Ollama LLM) is used for command interpretation.
- The frontend is a web-based dashboard built using Flask and Socket.IO, providing real-time updates and logs.

This modular architecture allows easy extension of features in the future.

---

## Technologies Used

### Backend
- Python 3.9+
- Flask
- Socket.IO
- SpeechRecognition
- pyttsx3
- PyAutoGUI
- Ollama LLM

### Frontend
- HTML
- CSS (Tailwind CSS)
- JavaScript

### APIs and Services
- Gmail API
- Google Calendar API
- WhatsApp Web automation

---

## Project Structure

```text
├── main_assistant.py
├── ollama_llm.py
├── app.py
├── gmail_integration.py
├── reminder.py
├── Wtsapp.py
├── AppControl.py
├── notifications.py
├── templates/
│   └── index_assistant.html
├── static/
├── credentials.json
├── requirements.txt
└── README.md
