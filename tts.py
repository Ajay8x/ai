import pyttsx3
import datetime

# ============================================================
# TEXT-TO-SPEECH ENGINE INITIALIZE
# ============================================================

engine = pyttsx3.init()
engine.setProperty('rate', 110)

def speak(text):
    """
    Diye gaye text ko voice mein convert karta hai.
    """
    engine.say(text)
    engine.runAndWait()

def wish_user():
    """
    Current time ke according user ko Good Morning,
    Good Afternoon ya Good Evening bolta hai.
    """
    hour = datetime.datetime.now().hour
    if 0 <= hour < 12:
        speak("Good Morning!")
    elif 12 <= hour < 18:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")

    speak(
        "I am JARVIS, your personal assistant. "
        "How can I help you today?"
    )
