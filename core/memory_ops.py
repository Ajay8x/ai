"""
AJAX AI - Core Memory Operations
Unified with Database CRUD & MongoDB Atlas
"""

from database.crud import save_memory, search_memories

def remember_data(query, speak_func):
    memory_text = query.replace('remember that', '').strip()
    if callable(speak_func):
        speak_func("Got it. I will remember that.")
    save_memory("note", memory_text, category="user_note", source="voice_command")

def fetch_memory(speak_func):
    try:
        memories = search_memories(query="note", limit=5)
        if memories:
            latest = memories[0].get("value_text", "")
            if callable(speak_func):
                speak_func(f"You asked me to remember: {latest}")
        else:
            if callable(speak_func):
                speak_func("I don't remember anything yet.")
    except Exception:
        if callable(speak_func):
            speak_func("I don't remember anything yet.")
