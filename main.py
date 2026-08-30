# pyrefly: ignore [missing-import]
import pyttsx3
# pyrefly: ignore [missing-import]
import speech_recognition as sr
import datetime
# pyrefly: ignore [missing-import]
import wikipedia
import pywhatkit
import os
import webbrowser
from sites import sites
import wikipedia
import re

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 130)  # Speech speed


def speak(text):
    engine.say(text)
    engine.runAndWait()


def wish_user():
    hour = datetime.datetime.now().hour

    if 0 <= hour < 12:
        speak("Good Morning!")
    elif 12 <= hour < 18:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")

    speak("I am JARVIS, your personal assistant. How can I help you today?")


def take_command():
    listener = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening...")
        listener.pause_threshold = 0.6
        audio = listener.listen(source)

    try:
        print("Recognizing...")
        query = listener.recognize_google(audio)
        print("You said:", query)

    except Exception as e:
        print("Error:", e)
        print("Sorry, I didn't catch that. Say again.")
        return "none"

    return query.lower()


def search_web(query):
    speak(f"Searching for {query}...")
    try:
        # Clean the query for better search results
        clean_query = re.sub(r'^(what is a|what is|who is|who was|where is|tell me about|define)\s+', '', query, flags=re.IGNORECASE).strip()
        
        # Use wikipedia for accurate spoken answers
        search_results = wikipedia.search(clean_query)
        if search_results:
            # Get summary of the most relevant page with auto_suggest=False to prevent PageError crashes
            summary = wikipedia.summary(search_results[0], sentences=2, auto_suggest=False)
            speak("According to Google")
            speak(summary)
        else:
            speak("I couldn't find a direct answer.")
    except Exception:
        speak("Sorry, I couldn't fetch the spoken answer.")

    # Open Google Search so the user can see the actual web results
    pywhatkit.search(query)


def run_jarvis():
    wish_user()

    while True:
        query = take_command()

        if query == "none":
            continue

        elif 'search' in query or 'google' in query or 'wikipedia' in query:
            query = query.replace("search", "").replace("google", "").replace("wikipedia", "").strip()
            search_web(query)

        elif 'play' in query:
            song = query.replace('play', '')
            speak(f"Playing {song}")
            pywhatkit.playonyt(song)

        elif 'time' in query:
            time = datetime.datetime.now().strftime('%I:%M %p')
            speak(f"Current time is {time}")

        elif 'date' in query:
            date = datetime.datetime.now().strftime('%d-%m-%Y')
            speak(f"Today's date is {date}")

        elif 'open chrome' in query:
            speak("Opening Google Chrome.")
            try:
                os.startfile("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
            except Exception:
                speak("Chrome not found at the specified path.")

        else:
            opened = False

            for site in sites:
                if f"open {site[0]}" in query:
                    speak(f"Opening {site[0]}...")
                    webbrowser.open(site[1])
                    opened = True
                    break

            if not opened:
                if 'exit' in query or 'stop' in query:
                    speak("Goodbye! Have a great day.")
                    break
                else:
                    search_web(query)


# Start JARVIS
run_jarvis()