"""
AJAX AI - Mass Intent & Combinatorial Dataset Synthesis Engine
Generates and ingests 1000+ comprehensive multilingual patterns covering all domains:
PC Control, Windows automation, Hindi/Hinglish slang, technical queries, web lookups, media, and tools.
"""

import sys
import os
import json
import itertools

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

# Combinatorial Grammar & Entity Generators
APPS = ["chrome", "google chrome", "notepad", "calculator", "calc", "vscode", "visual studio code", "terminal", "cmd", "powershell", "paint", "task manager", "settings", "file explorer", "word", "excel", "spotify", "vlc", "control panel", "edge"]
ACTIONS_OPEN_EN = ["open", "launch", "start", "run", "bring up", "switch to", "initialize"]
ACTIONS_OPEN_HI = ["kholo", "chala do", "start karo", "open kar do", "khol do", "chalu karo", "chalao"]

CITIES = ["delhi", "mumbai", "kolkata", "chennai", "bangalore", "hyderabad", "pune", "ahmedabad", "jaipur", "london", "new york", "dubai", "tokyo", "paris", "shimla", "goa"]
WEATHER_TERMS_EN = ["what is the weather in", "weather forecast for", "temperature in", "is it raining in", "how hot is it in", "how cold is it in", "current weather at"]
WEATHER_TERMS_HI = ["ka mausam kaisa hai", "me barish hogi kya", "ka temperature kitna hai", "ka live weather batao", "me kitni sardi hai", "me kitni garmi hai"]

ARTISTS = ["arijit singh", "lofi songs", "punjabi songs", "bollywood music", "romantic tracks", "relaxing music", "coding songs", "kishore kumar", "sidhu moosewala", "workout playlist", "classical ragas", "devotional bhajans"]
PLAY_PREFIX_EN = ["play", "start playing", "play music by", "stream", "tune into", "listen to"]
PLAY_PREFIX_HI = ["ka gaana chalao", "ka gana sunao", "chalao youtube par", "play karo youtube pe", "bajao", "sunao"]

TIMERS_VALS = ["1 minute", "2 minutes", "5 minutes", "10 minutes", "15 minutes", "20 minutes", "30 minutes", "45 minutes", "1 hour", "30 seconds", "45 seconds"]
ALARMS_VALS = ["6 am", "7 am", "8 am", "6:30 am", "7:30 am", "8:30 am", "9 am", "10 pm", "5 am", "alarm for tomorrow morning"]

def generate_massive_dataset() -> dict:
    dataset = {
        "OPEN_APPLICATION": [],
        "CLOSE_APPLICATION": [],
        "WEATHER": [],
        "PLAY_YOUTUBE": [],
        "SET_TIMER": [],
        "SET_ALARM": [],
        "SYSTEM_INFO": [
            "check cpu load", "check ram utilization", "how much memory is free", "show disk space left",
            "battery health check", "is laptop plugged in", "laptop ki battery status batao", "cpu temperature check",
            "show active background processes", "top cpu consuming apps", "hardware status report", "show system health summary",
            "ram kitni use ho rahi hai", "disk free space check karo", "system diagnostics dikhao", "pc performance kaisa chal raha hai"
        ],
        "SYSTEM_POWER": [
            "shutdown computer now", "restart windows", "lock workstation", "put system to sleep",
            "pc band kar do", "laptop restart karo", "computer lock karo please", "turn off the pc",
            "reboot operating system", "log off user", "sleep mode me daal do", "power down computer"
        ],
        "TIME": [
            "what time is it right now", "tell me current time and date", "exact time batao", "aaj konsi tarikh hai",
            "what is today's day and date", "current time zone", "ghadi me kitna time hua hai", "show time and calendar",
            "aaj ka din aur tarikh kya hai", "kitne baj rahe hain", "current world time"
        ],
        "SEARCH_WEB": [
            "search on google for latest news", "google who is the richest person", "search python full tutorial",
            "find top ai tools on internet", "google stock market today", "search how to build machine learning models",
            "latest technology news batao", "google par search karo best laptops", "internet par dhundo",
            "search meaning of artificial intelligence", "look up latest space missions", "google search cricket live score"
        ],
        "SEARCH_WIKIPEDIA": [
            "wikipedia search for albert einstein", "tell me about indian history on wikipedia",
            "who was mahatma gandhi according to wikipedia", "search quantum mechanics on wikipedia",
            "wikipedia page of space station", "explain black holes via wikipedia", "wikipedia article on computer science"
        ],
        "SCREENSHOT": [
            "take a full screenshot", "capture my screen", "save desktop image", "screenshot le lo jaldi",
            "capture display window", "take screen photo and save", "screenshot capture karo", "save current view"
        ],
        "VOLUME_CONTROL": [
            "increase volume by 10 percent", "turn up the sound", "volume down please", "decrease master audio",
            "mute system audio", "unmute the speaker", "aawaz badhao thodi", "aawaz kam karo", "sound mute karo",
            "pause current video", "resume the playback", "pause audio", "continue playing"
        ],
        "MEMORY_SAVE": [
            "remember that my car number is 9876", "save that my favorite book is atomic habits",
            "remember my doctor appointment is on friday", "store this note in memory",
            "ye baat yaad rakhna ki meri birthday 15 august ko hai", "remember my college name is IIT",
            "save this user preference", "ye information yaad rakho"
        ],
        "MEMORY_RECALL": [
            "what do you remember about my schedule", "tell me all saved notes", "show my stored memory list",
            "mujhe yaad kiye huye facts batao", "what information do you know about me", "recall stored details",
            "memories dikhao", "what is stored in memory"
        ],
        "SEARCH_FILE": [
            "search for resume in my computer", "find python scripts in directory", "look for project_notes.docx",
            "search all pdf files", "computer me assignment file dhundo", "find downloads folder", "locate text documents"
        ],
        "READ_FILE": [
            "read content of notes.txt", "show text inside README.md", "open and read file data",
            "display code from main.py", "file padh kar batao", "show what is written in this document"
        ],
        "HELP": [
            "show all available voice commands", "what are all the tools you can run", "help me understand your capabilities",
            "features list dikhao", "how can i control my computer with ajax", "command reference menu", "madad menu dikhao"
        ],
        "GREETING": [
            "good morning ajax assistant", "hey there hope you are doing well", "namaste ajax bhai",
            "hello ajax how are you today", "hey buddy are you online", "shubh prabhat ajax", "ram ram bhai", "kaise ho ajax"
        ]
    }

    # Generate App Combinations
    for app in APPS:
        for act in ACTIONS_OPEN_EN:
            dataset["OPEN_APPLICATION"].append(f"{act} {app}")
        for act in ACTIONS_OPEN_HI:
            dataset["OPEN_APPLICATION"].append(f"{app} {act}")
            dataset["OPEN_APPLICATION"].append(f"bhai {app} {act}")
        dataset["CLOSE_APPLICATION"].append(f"close {app}")
        dataset["CLOSE_APPLICATION"].append(f"exit {app}")
        dataset["CLOSE_APPLICATION"].append(f"{app} band karo")
        dataset["CLOSE_APPLICATION"].append(f"{app} ko band kar do")

    # Generate Weather Combinations
    for city in CITIES:
        for term in WEATHER_TERMS_EN:
            dataset["WEATHER"].append(f"{term} {city}")
        for term in WEATHER_TERMS_HI:
            dataset["WEATHER"].append(f"{city} {term}")

    # Generate YouTube Combinations
    for artist in ARTISTS:
        for p in PLAY_PREFIX_EN:
            dataset["PLAY_YOUTUBE"].append(f"{p} {artist}")
            dataset["PLAY_YOUTUBE"].append(f"{p} {artist} on youtube")
        for p in PLAY_PREFIX_HI:
            dataset["PLAY_YOUTUBE"].append(f"{artist} {p}")

    # Generate Timer & Alarm Combinations
    for t in TIMERS_VALS:
        dataset["SET_TIMER"].append(f"set a timer for {t}")
        dataset["SET_TIMER"].append(f"{t} ka timer lagao")
        dataset["SET_TIMER"].append(f"start {t} countdown")
        dataset["SET_TIMER"].append(f"timer set karo {t} ke liye")

    for a in ALARMS_VALS:
        dataset["SET_ALARM"].append(f"set an alarm for {a}")
        dataset["SET_ALARM"].append(f"wake me up at {a}")
        dataset["SET_ALARM"].append(f"{a} ka alarm lagao")
        dataset["SET_ALARM"].append(f"alarm set karo {a} baje")

    return dataset

def run_mass_training():
    print("\n==================================================================")
    print("  [MASSIVE TRAINING ENGINE] SYNTHESIZING 1,000+ HIGH-SCALE PATTERNS")
    print("==================================================================")

    generated = generate_massive_dataset()

    with open(INTENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    intents_map = {item["intent"]: item for item in data.get("intents", [])}
    total_before = sum(len(item["patterns"]) for item in intents_map.values())
    added = 0

    for intent_name, patterns in generated.items():
        if intent_name in intents_map:
            existing = set(p.lower() for p in intents_map[intent_name]["patterns"])
            for p in patterns:
                p_clean = p.lower().strip()
                if p_clean not in existing:
                    intents_map[intent_name]["patterns"].append(p_clean)
                    existing.add(p_clean)
                    added += 1

    with open(INTENTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"intents": list(intents_map.values())}, f, indent=2)

    intent_classifier.load_dataset()
    total_after = sum(len(item["patterns"]) for item in intents_map.values())

    print(f"\n[OK] Massive Dataset Compilation Finished!")
    print(f"  * Total Active Intents      : {len(intents_map)}")
    print(f"  * New Patterns Ingested     : +{added}")
    print(f"  * Total Active Patterns Now : {total_after}")
    print("==================================================================\n")

    from training.evaluate import run_evaluation
    run_evaluation()

if __name__ == "__main__":
    run_mass_training()
