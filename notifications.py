import pyautogui
import pytesseract
import time
from PIL import ImageGrab
import pyttsx3

engine = pyttsx3.init()

def speak(text):
    print("Notification:", text)
    engine.say(text)
    engine.runAndWait()

def read_notifications():
    speak("Opening the notification center.")
    
    # Open the Windows Notification panel
    pyautogui.hotkey('win', 'n')
    time.sleep(2)

    # Capture right side of screen (notification panel)
    screen_width, screen_height = pyautogui.size()
    left = screen_width - 420
    top = 0
    right = screen_width
    bottom = screen_height

    screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
    screenshot.save("notification_panel.png")

    raw_text = pytesseract.image_to_string(screenshot, config='--psm 6')
    lines = raw_text.strip().split('\n')

    reading = False
    meaningful_lines = []
    stop_triggered = False

    for line in lines:
        clean = line.strip()
        if not clean or len(clean) < 3:
            continue

        # Start reading when first 'real' notification found
        if "Notification:" in clean:
            reading = True

        if reading:
            # Stop if footer or junk line detected
            if "© IN" in clean or "15-05-2025" in clean:
                stop_triggered = True
                break

            # Filter known UI garbage
            junk = ['Clear all', 'Do not disturb', 'Focus', 'ENG', 'Notification settings']
            if any(j in clean for j in junk):
                continue

            # Skip symbols only
            if not any(c.isalnum() for c in clean):
                continue

            meaningful_lines.append(clean)

    if not meaningful_lines:
        speak("There are no important notifications.")
    else:
        speak("Here are your notifications.")
        for line in meaningful_lines:
            speak(line)
