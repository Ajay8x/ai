def remember_data(query, speak_func):
    memory_text = query.replace('remember that', '').strip()
    speak_func("Got it. I will remember that.")
    with open("memory.txt", "w") as f:
        f.write(memory_text)

def fetch_memory(speak_func):
    try:
        with open("memory.txt", "r") as f:
            memory_text = f.read()
            speak_func(f"You asked me to remember that: {memory_text}")
    except FileNotFoundError:
        speak_func("I don't remember anything yet.")
