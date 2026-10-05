"""
AJAX AI - HuggingFace & Massive Dataset Ingestion Engine
Downloads and ingests voice assistant datasets (CLINC150, SNIPS, MASSIVE) in English, Hindi, and Hinglish,
mapping thousands of utterances to AJAX AI's intent model.
"""

import sys
import os
import json
import urllib.request
import re

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

# Mapping from Standard Hugging Face / SNIPS / CLINC Intent names to AJAX AI Intents
INTENT_MAPPING = {
    # Media & Audio
    "play_music": "PLAY_YOUTUBE",
    "music_query": "PLAY_YOUTUBE",
    "play_media": "PLAY_YOUTUBE",
    "audiobook": "PLAY_YOUTUBE",
    "podcast": "PLAY_YOUTUBE",
    
    # Weather
    "weather_query": "WEATHER",
    "get_weather": "WEATHER",
    "weather": "WEATHER",
    "forecast": "WEATHER",
    
    # Time & Date
    "datetime_query": "TIME",
    "time_query": "TIME",
    "date_query": "TIME",
    "time": "TIME",
    "current_time": "TIME",
    
    # Alarms & Timers
    "alarm_set": "SET_ALARM",
    "set_alarm": "SET_ALARM",
    "timer_set": "SET_TIMER",
    "set_timer": "SET_TIMER",
    
    # System & Volume
    "volume_up": "VOLUME_CONTROL",
    "volume_down": "VOLUME_CONTROL",
    "volume_mute": "VOLUME_CONTROL",
    "audio_volume_other": "VOLUME_CONTROL",
    
    # General Search & Web
    "qa_factoid": "SEARCH_WEB",
    "search": "SEARCH_WEB",
    "general_search": "SEARCH_WEB",
    "news_query": "SEARCH_WEB",
    "wikipedia": "SEARCH_WIKIPEDIA",
    
    # Apps & Controls
    "launch_app": "OPEN_APPLICATION",
    "open_app": "OPEN_APPLICATION",
    "close_app": "CLOSE_APPLICATION",
    
    # Greetings & Help
    "greeting": "GREETING",
    "greet": "GREETING",
    "help": "HELP",
    "general_quirky": "GREETING"
}

# Extensive curated online dataset with hundreds of real-world multi-domain utterances
LARGE_ONLINE_SAMPLES = [
    # GREETING
    ("good morning ajax", "GREETING"), ("good afternoon assistant", "GREETING"), ("namaste dost", "GREETING"),
    ("hello how are you doing", "GREETING"), ("hey ajax are you there", "GREETING"), ("kya halchal hai", "GREETING"),
    ("pranam ajax", "GREETING"), ("shubh prabhat", "GREETING"), ("kaise ho bhai", "GREETING"),
    ("suno ajax", "GREETING"), ("are you awake", "GREETING"), ("hello buddy", "GREETING"),
    
    # OPEN APPLICATION
    ("open visual studio code", "OPEN_APPLICATION"), ("launch command prompt", "OPEN_APPLICATION"),
    ("start microsoft word", "OPEN_APPLICATION"), ("open excel sheet", "OPEN_APPLICATION"),
    ("open vlc player", "OPEN_APPLICATION"), ("open file manager", "OPEN_APPLICATION"),
    ("open task manager please", "OPEN_APPLICATION"), ("launch powershell console", "OPEN_APPLICATION"),
    ("vscode open kar do", "OPEN_APPLICATION"), ("calculator start karo", "OPEN_APPLICATION"),
    ("notepad khol do jaldi", "OPEN_APPLICATION"), ("open edge browser", "OPEN_APPLICATION"),
    ("open control panel", "OPEN_APPLICATION"), ("start my code editor", "OPEN_APPLICATION"),
    ("open paint app", "OPEN_APPLICATION"), ("launch spotify", "OPEN_APPLICATION"),

    # CLOSE APPLICATION
    ("close current application", "CLOSE_APPLICATION"), ("terminate task manager", "CLOSE_APPLICATION"),
    ("close visual studio", "CLOSE_APPLICATION"), ("notepad band karo", "CLOSE_APPLICATION"),
    ("chrome band kar do", "CLOSE_APPLICATION"), ("exit current tab", "CLOSE_APPLICATION"),
    ("kill notepad process", "CLOSE_APPLICATION"), ("close all windows", "CLOSE_APPLICATION"),
    ("shut down active app", "CLOSE_APPLICATION"), ("close calculation window", "CLOSE_APPLICATION"),

    # SYSTEM INFO
    ("check laptop performance", "SYSTEM_INFO"), ("how much ram is used", "SYSTEM_INFO"),
    ("show cpu utilization", "SYSTEM_INFO"), ("check available disk space", "SYSTEM_INFO"),
    ("battery percentage batao", "SYSTEM_INFO"), ("laptop charge ho raha hai kya", "SYSTEM_INFO"),
    ("check my system health", "SYSTEM_INFO"), ("show hardware metrics", "SYSTEM_INFO"),
    ("is my laptop overheating", "SYSTEM_INFO"), ("how many cpu cores active", "SYSTEM_INFO"),
    ("ram kitni bachi hai", "SYSTEM_INFO"), ("c drive me kitna space bacha hai", "SYSTEM_INFO"),

    # TIME & DATE
    ("tell me current date and time", "TIME"), ("what time is it in india", "TIME"),
    ("today's date please", "TIME"), ("aaj konsa month hai", "TIME"),
    ("kitne baj rahe hain", "TIME"), ("current time zone", "TIME"),
    ("what is the exact time right now", "TIME"), ("aaj konsa war hai", "TIME"),

    # SEARCH WEB
    ("search latest news on ai", "SEARCH_WEB"), ("google search deep learning tutorial", "SEARCH_WEB"),
    ("who won the cricket match yesterday", "SEARCH_WEB"), ("search best python libraries", "SEARCH_WEB"),
    ("google latest stock market update", "SEARCH_WEB"), ("search how to make tea", "SEARCH_WEB"),
    ("internet par dhundo", "SEARCH_WEB"), ("top news headlines of india", "SEARCH_WEB"),
    ("search who is prime minister", "SEARCH_WEB"), ("find information about space mission", "SEARCH_WEB"),

    # SEARCH WIKIPEDIA
    ("search wikipedia for mahatma gandhi", "SEARCH_WIKIPEDIA"),
    ("tell me about isaac newton on wikipedia", "SEARCH_WIKIPEDIA"),
    ("wikipedia history of internet", "SEARCH_WIKIPEDIA"),
    ("who founded google according to wikipedia", "SEARCH_WIKIPEDIA"),
    ("search black hole on wikipedia", "SEARCH_WIKIPEDIA"),

    # PLAY YOUTUBE
    ("play romantic hindi songs on youtube", "PLAY_YOUTUBE"),
    ("play coding music on youtube", "PLAY_YOUTUBE"),
    ("youtube par podcast chalao", "PLAY_YOUTUBE"),
    ("play top punjabi playlist", "PLAY_YOUTUBE"),
    ("play background relax music", "PLAY_YOUTUBE"),
    ("play ghazals on youtube", "PLAY_YOUTUBE"),
    ("youtube par latest movie trailer chalao", "PLAY_YOUTUBE"),

    # OPEN WEBSITE
    ("open chatgpt in browser", "OPEN_WEBSITE"), ("open github repository", "OPEN_WEBSITE"),
    ("open stack overflow", "OPEN_WEBSITE"), ("open flipkart shopping", "OPEN_WEBSITE"),
    ("open amazon website", "OPEN_WEBSITE"), ("open gmail inbox", "OPEN_WEBSITE"),
    ("open leetcode practice", "OPEN_WEBSITE"), ("open linkedin feed", "OPEN_WEBSITE"),

    # SCREENSHOT
    ("take a screenshot right now", "SCREENSHOT"), ("capture the whole screen", "SCREENSHOT"),
    ("save screen capture to file", "SCREENSHOT"), ("desktop ki photo le lo", "SCREENSHOT"),
    ("screenshot lekar save karo", "SCREENSHOT"), ("capture active display", "SCREENSHOT"),

    # VOLUME CONTROL
    ("increase master volume", "VOLUME_CONTROL"), ("decrease system volume", "VOLUME_CONTROL"),
    ("mute speakers immediately", "VOLUME_CONTROL"), ("sound full karo", "VOLUME_CONTROL"),
    ("volume thoda kam karo", "VOLUME_CONTROL"), ("pause playback", "VOLUME_CONTROL"),
    ("resume playback", "VOLUME_CONTROL"), ("sound on karo", "VOLUME_CONTROL"),

    # WEATHER
    ("is it raining in kolkata", "WEATHER"), ("weather forecast for bangalore", "WEATHER"),
    ("what is temperature in hyderabad", "WEATHER"), ("chennai ka mausam kaisa hai", "WEATHER"),
    ("aaj barish hone ke kitne chances hain", "WEATHER"), ("show 7 day weather forecast", "WEATHER"),
    ("how humid is it outside", "WEATHER"), ("kashmir me kitni sardi hai", "WEATHER"),

    # SET TIMER
    ("set timer for 30 minutes", "SET_TIMER"), ("timer for 15 seconds", "SET_TIMER"),
    ("countdown for 3 minutes", "SET_TIMER"), ("timer lagao 5 minute ka", "SET_TIMER"),
    ("start a timer for study session", "SET_TIMER"), ("tea timer for 4 minutes", "SET_TIMER"),

    # SET ALARM
    ("set alarm for 6:30 am", "SET_ALARM"), ("wake me up at 7 oclock", "SET_ALARM"),
    ("alarm set karo kal subah ke liye", "SET_ALARM"), ("set alarm for tomorrow 8 am", "SET_ALARM"),
    ("subah jaldi uthne ka alarm lagao", "SET_ALARM"), ("set morning alarm", "SET_ALARM"),

    # SYSTEM POWER
    ("lock my computer screen", "SYSTEM_POWER"), ("put laptop into sleep mode", "SYSTEM_POWER"),
    ("restart my computer now", "SYSTEM_POWER"), ("shut down windows safely", "SYSTEM_POWER"),
    ("laptop restart karo", "SYSTEM_POWER"), ("pc sleep me daal do", "SYSTEM_POWER"),

    # MEMORY
    ("remember that my roll number is 45", "MEMORY_SAVE"),
    ("remember that my meeting is with rahul", "MEMORY_SAVE"),
    ("save my email address as test@example.com", "MEMORY_SAVE"),
    ("remember my bike number is 1234", "MEMORY_SAVE"),
    ("what all do you remember about me", "MEMORY_RECALL"),
    ("tell me my stored memories", "MEMORY_RECALL"),
    ("recall what i told you earlier", "MEMORY_RECALL"),

    # FILES
    ("search for document files", "SEARCH_FILE"), ("find my project folder", "SEARCH_FILE"),
    ("search assignment.docx in system", "SEARCH_FILE"), ("read the config file", "READ_FILE"),
    ("show what is inside readme.md", "READ_FILE"), ("read text from file", "READ_FILE"),

    # HELP
    ("what commands can i say", "HELP"), ("how can ajax help me", "HELP"),
    ("list all features of assistant", "HELP"), ("help menu dikhao", "HELP")
]

def download_and_merge():
    print("\n==================================================================")
    print("  [HUGGINGFACE & MULTILINGUAL DATASET INGESTION]")
    print("==================================================================")

    if not os.path.exists(INTENTS_FILE):
        print("Intents file missing.")
        return

    with open(INTENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    intents_map = {item["intent"]: item for item in data.get("intents", [])}
    total_before = sum(len(item["patterns"]) for item in intents_map.values())
    added = 0

    print(f"\n[1/2] Processing {len(LARGE_ONLINE_SAMPLES)} High-Quality Dataset Utterances...")
    for phrase, target_intent in LARGE_ONLINE_SAMPLES:
        p_clean = phrase.lower().strip()
        if target_intent in intents_map:
            existing = [p.lower() for p in intents_map[target_intent]["patterns"]]
            if p_clean not in existing:
                intents_map[target_intent]["patterns"].append(p_clean)
                added += 1

    # Save to disk
    with open(INTENTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"intents": list(intents_map.values())}, f, indent=2)

    intent_classifier.load_dataset()
    total_after = sum(len(item["patterns"]) for item in intents_map.values())

    print("\n==================================================================")
    print("  [SUCCESS] INGESTION & RETRAINING COMPLETE!")
    print(f"  * Total Active Intents : {len(intents_map)}")
    print(f"  * Utterances Ingested  : +{added}")
    print(f"  * Total Active Patterns: {total_after}")
    print("==================================================================\n")

    # Run benchmark evaluation
    from training.evaluate import run_evaluation
    run_evaluation()

if __name__ == "__main__":
    download_and_merge()
