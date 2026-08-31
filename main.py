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
import re

# sites.py se websites ki list import kar rahe hain
from sites import sites


# ============================================================
# TEXT-TO-SPEECH ENGINE INITIALIZE
# ============================================================

# pyttsx3 speech engine ko initialize kar rahe hain
engine = pyttsx3.init()

# JARVIS ki speaking speed set kar rahe hain
# Value kam = speech slow
# Value zyada = speech fast
engine.setProperty('rate', 130)


# ============================================================
# SPEAK FUNCTION
# ============================================================

def speak(text):
    """
    Diye gaye text ko voice mein convert karta hai.
    """

    # Text ko speech engine mein bhejte hain
    engine.say(text)

    # Jab tak speech complete nahi hoti, wait karega
    engine.runAndWait()


# ============================================================
# USER KO WISH KARNE KA FUNCTION
# ============================================================

def wish_user():
    """
    Current time ke according user ko Good Morning,
    Good Afternoon ya Good Evening bolta hai.
    """

    # Current hour nikal rahe hain (0 se 23)
    hour = datetime.datetime.now().hour

    # Agar time 12 AM se 12 PM se pehle hai
    if 0 <= hour < 12:
        speak("Good Morning!")

    # Agar time 12 PM se 6 PM se pehle hai
    elif 12 <= hour < 18:
        speak("Good Afternoon!")

    # Baaki time ke liye Evening bolega
    else:
        speak("Good Evening!")

    # JARVIS apna introduction dega
    speak(
        "I am JARVIS, your personal assistant. "
        "How can I help you today?"
    )


# ============================================================
# VOICE COMMAND LENE KA FUNCTION
# ============================================================

def take_command():
    """
    Microphone se user ki voice leta hai
    aur usko text mein convert karta hai.
    """

    # Speech Recognizer ka object bana rahe hain
    listener = sr.Recognizer()

    # Computer ka microphone activate kar rahe hain
    with sr.Microphone() as source:

        # Terminal mein status show hoga
        print("Listening...")

        # JARVIS kitni der pause ke baad samjhe
        # ki user bolna band kar chuka hai
        listener.pause_threshold = 0.6

        # Microphone se audio record kar rahe hain
        audio = listener.listen(source)

    try:

        # Voice ko recognize karna start
        print("Recognizing...")

        # Google Speech Recognition se voice ko text mein convert
        query = listener.recognize_google(audio)

        # User ne kya bola wo terminal mein show hoga
        print("You said:", query)

    except Exception as e:

        # Agar voice recognize nahi hui to error show hoga
        print("Error:", e)

        # User ko dobara bolne ke liye kahenge
        print("Sorry, I didn't catch that. Say again.")

        # "none" return karenge
        return "none"

    # Command ko lowercase mein convert karke return karenge
    return query.lower()


# ============================================================
# WEB SEARCH FUNCTION
# ============================================================

def search_web(query):
    """
    User ki query ko Wikipedia aur Google par search karta hai.
    """

    # User ko batayega ki search ho rahi hai
    speak(f"Searching for {query}...")

    try:

        # ----------------------------------------------------
        # QUERY CLEAN KARNA
        # ----------------------------------------------------

        # Kuch common words ko query ke starting se remove kar rahe hain
        #
        # Example:
        # "What is Python?"
        #
        # ban jayega:
        # "Python"

        clean_query = re.sub(
            r'^(what is a|what is|who is|who was|where is|'
            r'tell me about|define)\s+',
            '',
            query,
            flags=re.IGNORECASE
        ).strip()


        # ----------------------------------------------------
        # WIKIPEDIA SEARCH
        # ----------------------------------------------------

        # Wikipedia mein clean query search kar rahe hain
        search_results = wikipedia.search(clean_query)

        # Agar Wikipedia mein result mil gaya
        if search_results:

            # Sabse relevant result ka 2 sentence summary nikal rahe hain
            summary = wikipedia.summary(
                search_results[0],
                sentences=2,
                auto_suggest=False
            )

            # User ko source batayega
            speak("According to Wikipedia")

            # Wikipedia ka answer bolkar sunayega
            speak(summary)

        else:

            # Agar Wikipedia mein result nahi mila
            speak("I couldn't find a direct answer.")

    except Exception:

        # Agar internet ya Wikipedia mein koi error aaye
        speak("Sorry, I couldn't fetch the spoken answer.")


    # --------------------------------------------------------
    # GOOGLE SEARCH OPEN KARNA
    # --------------------------------------------------------

    # Google mein actual search results browser mein open karega
    pywhatkit.search(query)


# ============================================================
# MAIN JARVIS FUNCTION
# ============================================================

def run_jarvis():
    """
    Ye JARVIS ka main function hai.
    Ye continuously user ki commands sunta rahega.
    """

    # JARVIS start hote hi user ko wish karega
    wish_user()

    # JARVIS ko continuously run karne ke liye infinite loop
    while True:

        # User ki voice command lena
        query = take_command()


        # ----------------------------------------------------
        # AGAR VOICE RECOGNIZE NAHI HUI
        # ----------------------------------------------------

        if query == "none":

            # Dobara command sunne ke liye loop continue
            continue


        # ----------------------------------------------------
        # SEARCH / GOOGLE / WIKIPEDIA COMMAND
        # ----------------------------------------------------

        elif (
            'search' in query
            or 'google' in query
            or 'wikipedia' in query
        ):

            # Command mein se unwanted keywords remove kar rahe hain
            query = (
                query
                .replace("search", "")
                .replace("google", "")
                .replace("wikipedia", "")
                .strip()
            )

            # Web search function call kar rahe hain
            search_web(query)


        # ----------------------------------------------------
        # YOUTUBE PAR SONG/VIDEO PLAY KARNA
        # ----------------------------------------------------

        elif 'play' in query:

            # "play" word ko command se remove kar rahe hain
            #
            # Example:
            # "play Arijit Singh"
            #
            # banega:
            # "Arijit Singh"

            song = query.replace('play', '').strip()

            # User ko batayega kya play kar raha hai
            speak(f"Playing {song}")

            # YouTube par song/video play karega
            pywhatkit.playonyt(song)


        # ----------------------------------------------------
        # CURRENT TIME BATANA
        # ----------------------------------------------------

        elif 'time' in query:

            # Current time nikal rahe hain
            current_time = datetime.datetime.now().strftime(
                '%I:%M %p'
            )

            # Time ko voice mein bolenge
            speak(f"Current time is {current_time}")


        # ----------------------------------------------------
        # CURRENT DATE BATANA
        # ----------------------------------------------------

        elif 'date' in query:

            # Aaj ki date nikal rahe hain
            current_date = datetime.datetime.now().strftime(
                '%d-%m-%Y'
            )

            # Date ko voice mein bolenge
            speak(f"Today's date is {current_date}")


        # ----------------------------------------------------
        # GOOGLE CHROME OPEN KARNA
        # ----------------------------------------------------

        elif 'open chrome' in query:

            # User ko batayega ki Chrome open ho raha hai
            speak("Opening Google Chrome.")

            try:

                # Windows mein Chrome ko open kar rahe hain
                os.startfile(
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                )

            except Exception:

                # Agar Chrome specified location par nahi mila
                speak("Chrome not found at the specified path.")


        # ----------------------------------------------------
        # SITES.PY SE WEBSITE OPEN KARNA
        # ----------------------------------------------------

        else:

            # Ye check karega ki koi website open hui ya nahi
            opened = False

            # sites.py mein stored sabhi websites ko check karenge
            for site in sites:

                # Check kar rahe hain user ne
                # "open youtube", "open google" etc. bola hai ya nahi
                if f"open {site[0]}" in query:

                    # User ko batayega website open ho rahi hai
                    speak(f"Opening {site[0]}...")

                    # Website ko default browser mein open karega
                    webbrowser.open(site[1])

                    # Website successfully open ho gayi
                    opened = True

                    # Loop ko stop kar do
                    break


            # ------------------------------------------------
            # EXIT YA UNKNOWN COMMAND
            # ------------------------------------------------

            if not opened:

                # Check karo user JARVIS ko band karna chahta hai
                if 'exit' in query or 'stop' in query:

                    # Goodbye message
                    speak("Goodbye! Have a great day.")

                    # Main loop se bahar aa jao
                    break

                # Agar query "open" se start hoti hai aur koi website match nahi hui
                elif query.startswith('open '):
                    
                    app_name = query.replace('open ', '').strip()
                    
                    # Common Windows apps ki list aur unke commands
                    app_commands = {
                        "setting": "ms-settings:",
                        "settings": "ms-settings:",
                        "calculator": "calc",
                        "calc": "calc",
                        "command prompt": "cmd",
                        "cmd": "cmd",
                        "notepad": "notepad",
                        "paint": "mspaint",
                        "word": "winword",
                        "excel": "excel",
                        "powerpoint": "powerpnt",
                        "file explorer": "explorer",
                        "control panel": "control",
                        "task manager": "taskmgr"
                    }
                    
                    # Agar app dictionary mein hai, to uski correct command lenge
                    # Varna user ne jo bola wahi command mein daal denge
                    command_to_run = app_commands.get(app_name, app_name)
                    
                    speak(f"Opening {app_name}")
                    
                    # Windows ki start command use karke app open karenge
                    os.system(f"start {command_to_run}")

                else:

                    # Agar command kisi known function se match nahi hui
                    # to usko web par search karenge
                    search_web(query)


# ============================================================
# JARVIS START KARNA
# ============================================================

# Main JARVIS function ko run kar rahe hain
run_jarvis()