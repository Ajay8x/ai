"""
AJAX AI - Dataset Ingestion & Mass Training Pipeline
Downloads and compiles comprehensive multilingual (English, Hindi, Hinglish) assistant datasets,
trains the neural intent classifier, and benchmarks performance.
"""

import sys
import os
import json

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.neural.intent_classifier import intent_classifier
from core.logger import training_logger

INTENTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "intents.json")

# Comprehensive High-Quality Multilingual Dataset
EXPANDED_DATASET = {
    "GREETING": [
        "hello", "hi", "hey", "namaste", "kem cho", "kaise ho", "good morning", "good evening", "good afternoon",
        "ajax hello", "hey buddy", "ram ram", "kya haal hai", "hello ajax", "hi jarvis", "namashkar", "pranam",
        "sasriyakaal", "kaisa chal raha hai", "wassup", "howdy", "hey there", "namaste ajax", "suno", "hey assistant"
    ],
    "OPEN_APPLICATION": [
        "open chrome", "launch chrome", "chrome kholo", "chrome chala do", "open notepad", "notepad start karo",
        "open calculator", "calc kholo", "open vscode", "open code", "open terminal", "open powershell", "open paint",
        "open task manager", "open settings", "bhai chrome open kar", "start chrome", "run notepad", "open command prompt",
        "open cmd", "launch vs code", "visual studio code kholo", "open ms word", "open excel", "open file explorer",
        "calculator chala do", "paint kholo", "app open karo", "chrome browser open karo", "notepad open karo"
    ],
    "CLOSE_APPLICATION": [
        "close chrome", "exit chrome", "chrome band karo", "close notepad", "notepad band kar do", "close calc",
        "close calculator", "terminate app", "band kar do", "close tab", "close window", "shut down chrome",
        "kill process", "stop notepad", "notepad hatao", "app band karo", "window band karo", "close this", "exit app"
    ],
    "SYSTEM_INFO": [
        "system status", "pc status", "cpu status", "ram status", "battery status", "check battery", "check cpu",
        "system info", "pc ki health batao", "battery kitni hai", "cpu kitna use ho raha hai", "disk space kitna hai",
        "ram kitni khali hai", "laptop status", "how much battery left", "check ram", "show system diagnostics",
        "check disk usage", "system performance kaisa hai", "memory kitni use ho rahi hai", "battery charge ho rahi hai kya"
    ],
    "TIME": [
        "what time is it", "tell me time", "current time", "time kya hua hai", "kitne baje hain", "time batao",
        "date and time", "aaj ka time", "samay kya hai", "aaj konsi date hai", "what is today's date", "date batao",
        "current date", "tell me date and time", "ghadi me kitna baja hai", "what day is today", "aaj konsa din hai"
    ],
    "SEARCH_WEB": [
        "search on google", "search web for", "google par search karo", "search karo", "find on internet", "search",
        "google elon musk", "search who is pm of india", "google latest news", "search what is python", "google par dhundo",
        "internet par search karo", "search artificial intelligence", "tell me latest tech news", "google search",
        "search meaning of", "find details about", "search web", "look up on google", "news batao", "top news headlines"
    ],
    "SEARCH_WIKIPEDIA": [
        "wikipedia search", "search wikipedia for", "who is", "what is wikipedia", "batao wikipedia par",
        "tell me about on wikipedia", "search history of india on wikipedia", "wikipedia per dhundo", "explain on wikipedia",
        "who was albert einstein", "wikipedia summary of quantum computing"
    ],
    "PLAY_YOUTUBE": [
        "play on youtube", "play song", "youtube par chalao", "play video", "gana sunao", "play",
        "play arijit singh", "play lofi songs", "youtube par video chalao", "song play karo", "play bollywood music",
        "play punjabi songs", "youtube par gaana lagao", "play something relaxing", "play music", "play trailer"
    ],
    "OPEN_WEBSITE": [
        "open youtube", "open github", "open chatgpt", "open instagram", "open facebook", "open website",
        "website kholo", "open google", "open twitter", "open reddit", "open linkedin", "open netflix",
        "open whatsapp web", "open amazon", "open flipkart", "open canva", "open stackoverflow", "open wikipedia"
    ],
    "SCREENSHOT": [
        "take a screenshot", "capture screen", "screenshot le lo", "screen capture karo", "screenshot",
        "take screen photo", "save screenshot", "screen ki image capture karo", "take screenshot now", "capture desktop"
    ],
    "VOLUME_CONTROL": [
        "increase volume", "volume up", "volume down", "decrease volume", "mute volume", "unmute",
        "aawaz badhao", "aawaz kam karo", "mute karo", "sound badhao", "volume 50 percent", "turn up volume",
        "turn down volume", "pause music", "resume music", "pause", "resume", "sound mute karo", "sound unmute karo"
    ],
    "WEATHER": [
        "what is the weather", "weather today", "mausam kaisa hai", "weather forecast", "aaj barish hogi kya",
        "temperature kitna hai", "weather in delhi", "weather in mumbai", "weather in new york", "current weather",
        "delhi ka mausam", "aaj dhoop niklegi kya", "temperature check karo", "how cold is it outside", "rain prediction"
    ],
    "SET_TIMER": [
        "set a timer", "timer lagao", "set timer for", "5 minute ka timer", "timer set karo",
        "set a timer for 10 minutes", "start countdown for 1 minute", "2 minute ka timer lagao", "timer start karo",
        "alert me in 15 minutes", "timer 30 seconds"
    ],
    "SET_ALARM": [
        "set an alarm", "alarm lagao", "alarm set karo", "wake me up at", "set an alarm for 7 am",
        "subah 6 baje ka alarm", "alarm lagao kal subah ke liye", "set alarm for 08:00", "alarm 7 baje ka lagana"
    ],
    "SYSTEM_POWER": [
        "shutdown pc", "restart pc", "lock pc", "sleep pc", "pc band karo", "pc restart kar do",
        "computer lock karo", "turn off computer", "reboot system", "lock my desktop", "put computer to sleep",
        "laptop band karo", "power off pc"
    ],
    "SEARCH_FILE": [
        "search file", "find file", "file dhundo", "look for document", "search pdf files",
        "search project folder", "find resume.pdf", "find text file", "computer me file dhundo", "locate file"
    ],
    "READ_FILE": [
        "read file", "open file content", "file padho", "show file content", "read notes.txt",
        "show text in file", "display file content", "file ka data dikhao", "read document"
    ],
    "MEMORY_SAVE": [
        "remember that", "remember my name is", "remember that my keys are on the table", "save this fact",
        "yaad rakhna", "ye baat yaad rakho", "remember my favorite color is blue", "store in memory",
        "remember my office starts at 9 am", "ye note yaad rakho"
    ],
    "MEMORY_RECALL": [
        "what do you remember", "what is stored in memory", "tell me my saved notes", "mujhe kya yaad hai",
        "yaad kiye huye facts batao", "show my memories", "what do you know about me", "recall memory"
    ],
    "HELP": [
        "help", "what can you do", "commands list", "madad", "features batao", "help me",
        "how to use ajax", "what are your capabilities", "options dikhao", "assist me"
    ]
}

def train_expanded_dataset():
    print("\n==================================================================")
    print("  [TRAINING] EXPANDED MULTILINGUAL DATASET PIPELINE")
    print("==================================================================")

    with open(INTENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing_intents = {item["intent"]: item for item in data.get("intents", [])}

    added_phrases = 0
    new_intents_count = 0

    for intent_name, patterns in EXPANDED_DATASET.items():
        if intent_name in existing_intents:
            existing_patterns = [p.lower() for p in existing_intents[intent_name]["patterns"]]
            for p in patterns:
                p_clean = p.lower().strip()
                if p_clean not in existing_patterns:
                    existing_intents[intent_name]["patterns"].append(p_clean)
                    existing_patterns.append(p_clean)
                    added_phrases += 1
        else:
            existing_intents[intent_name] = {
                "intent": intent_name,
                "patterns": [p.lower().strip() for p in patterns],
                "tool": intent_name.lower()
            }
            new_intents_count += 1
            added_phrases += len(patterns)

    # Save to disk
    with open(INTENTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"intents": list(existing_intents.values())}, f, indent=2)

    intent_classifier.load_dataset()
    total_active_patterns = sum(len(item["patterns"]) for item in existing_intents.values())

    print(f"\n[OK] Successfully Ingested Expanded Dataset!")
    print(f"  * Total Active Intents : {len(existing_intents)}")
    print(f"  * New Patterns Added   : +{added_phrases}")
    print(f"  * Total Patterns Now   : {total_active_patterns}")
    print("==================================================================\n")

    # Run Benchmark
    from training.evaluate import run_evaluation
    run_evaluation()

if __name__ == "__main__":
    train_expanded_dataset()
