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


def search_wikipedia(query):
    speak(f"Searching Wikipedia for {query}...")
    try:
        results = wikipedia.summary(query, sentences=2)
        speak("According to Wikipedia")
        speak(results)
    except wikipedia.exceptions.DisambiguationError:
        speak("There are multiple results for this topic. Please be more specific.")
    except wikipedia.exceptions.PageError:
        speak("Sorry, I couldn't find any information on that topic.")
    except Exception:
        speak("Sorry, I couldn't fetch data from Wikipedia.")


def run_jarvis():
    wish_user()

    while True:
        query = take_command()

        if query == "none":
            continue

        elif 'wikipedia' in query:
            query = query.replace("wikipedia", "").strip()
            search_wikipedia(query)

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
                    search_wikipedia(query)


# Start JARVIS
run_jarvis()