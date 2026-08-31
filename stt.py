import speech_recognition as sr

def take_command():
    """
    Microphone se user ki voice leta hai
    aur usko text mein convert karta hai.
    """
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
