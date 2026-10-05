"""
AJAX AI - Intent Model Trainer & Continuous Learning Engine
Supports:
1. Automated dataset ingestion from requirements_query.txt and database interactions.
2. Interactive custom command training mode.
3. Model evaluation and live accuracy metrics.
"""

import sys
import os
import re
import json
import argparse

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.crud import get_training_examples
from ai.neural.intent_classifier import intent_classifier
from core.logger import training_logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTENTS_FILE = os.path.join(BASE_DIR, "data", "intents.json")
REQ_QUERY_FILE = os.path.join(BASE_DIR, "requirements_query.txt")

def extract_phrases_from_req_file() -> list:
    """Extracts spoken phrases from requirements_query.txt."""
    if not os.path.exists(REQ_QUERY_FILE):
        return []
        
    extracted = []
    current_category = ""
    
    with open(REQ_QUERY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("---"):
                current_category = line.replace("-", "").strip()
            elif line.startswith("-"):
                # Extract quoted strings
                quotes = re.findall(r'"([^"]+)"', line)
                for q in quotes:
                    extracted.append((q.strip(), current_category))
    return extracted

def train_from_sources():
    print("\n==================================================================")
    print("  [TRAIN] AJAX AI - INTENT MODEL TRAINING PIPELINE")
    print("==================================================================")
    
    if not os.path.exists(INTENTS_FILE):
        print(f"Error: Intents dataset file not found at {INTENTS_FILE}")
        return

    with open(INTENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    intents_map = {item["intent"]: item for item in data.get("intents", [])}
    total_patterns_before = sum(len(item["patterns"]) for item in intents_map.values())
    added_count = 0

    # 1. Ingest from requirements_query.txt
    req_phrases = extract_phrases_from_req_file()
    print(f"\n[1/3] Parsing 'requirements_query.txt' ({len(req_phrases)} phrases found)...")
    for phrase, cat in req_phrases:
        p_lower = phrase.lower().strip()
        target_intent = "GENERAL_CHAT"
        if "close" in p_lower:
            target_intent = "CLOSE_APPLICATION"
        elif "open" in p_lower:
            target_intent = "OPEN_APPLICATION"
        elif "volume" in p_lower or "mute" in p_lower or "pause" in p_lower or "resume" in p_lower:
            target_intent = "VOLUME_CONTROL"
        elif "time" in p_lower or "date" in p_lower:
            target_intent = "TIME"
        elif "battery" in p_lower or "cpu" in p_lower or "status" in p_lower:
            target_intent = "SYSTEM_INFO"
        elif "shutdown" in p_lower or "restart" in p_lower or "sleep" in p_lower:
            target_intent = "SYSTEM_POWER"
        elif "play" in p_lower:
            target_intent = "PLAY_YOUTUBE"
        elif "weather" in p_lower:
            target_intent = "WEATHER"
        elif "screenshot" in p_lower:
            target_intent = "SCREENSHOT"
        elif "timer" in p_lower:
            target_intent = "SET_TIMER"
        elif "alarm" in p_lower:
            target_intent = "SET_ALARM"
        elif "remember" in p_lower:
            target_intent = "MEMORY_SAVE"
        elif "search" in p_lower or "google" in p_lower or "news" in p_lower:
            target_intent = "SEARCH_WEB"

        if target_intent in intents_map:
            existing = [x.lower() for x in intents_map[target_intent]["patterns"]]
            if p_lower not in existing:
                intents_map[target_intent]["patterns"].append(p_lower)
                added_count += 1
                print(f"  + Added: '{p_lower}' -> {target_intent}")

    # 2. Ingest approved user samples from Database
    print("\n[2/3] Ingesting approved training samples from SQLite database...")
    db_samples = get_training_examples(approved_only=True)
    db_added = 0
    for sample in db_samples:
        intent = sample["intent"]
        text = sample["raw_text"].lower().strip()
        if intent in intents_map:
            existing = [x.lower() for x in intents_map[intent]["patterns"]]
            if text not in existing:
                intents_map[intent]["patterns"].append(text)
                added_count += 1
                db_added += 1
    print(f"  + Ingested {db_added} approved interaction samples from database.")

    # 3. Save model dataset
    print("\n[3/3] Compiling and saving new Model Weights...")
    with open(INTENTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"intents": list(intents_map.values())}, f, indent=2)

    # Reload classifier in memory
    intent_classifier.load_dataset()
    total_patterns_after = sum(len(item["patterns"]) for item in intents_map.values())

    print("\n==================================================================")
    print("  [SUCCESS] TRAINING COMPLETE!")
    print(f"  * Total Intents Active : {len(intents_map)}")
    print(f"  * Patterns Before      : {total_patterns_before}")
    print(f"  * Patterns Ingested    : +{added_count}")
    print(f"  * Total Patterns Now   : {total_patterns_after}")
    print("==================================================================\n")

    # Run instant evaluation
    from training.evaluate import run_evaluation
    run_evaluation()

def interactive_training_mode():
    """Interactive loop to add custom commands in real-time."""
    print("\n==================================================================")
    print("  [TEACH] AJAX AI - INTERACTIVE COMMAND TRAINING")
    print("==================================================================")
    print(" Type a new sentence/command you want AJAX to understand.")
    print(" Type 'exit' to finish.\n")

    if not os.path.exists(INTENTS_FILE):
        print("Intents dataset missing.")
        return

    with open(INTENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    intents_map = {item["intent"]: item for item in data.get("intents", [])}
    available_intents = list(intents_map.keys())

    while True:
        try:
            phrase = input("\nEnter New Command Phrase >> ").strip()
            if not phrase:
                continue
            if phrase.lower() in ("exit", "quit", "q"):
                break

            # Show prediction
            pred = intent_classifier.predict(phrase)
            print(f"Current Prediction: {pred['intent']} (Confidence: {pred['confidence']})")

            print("\nSelect Target Intent:")
            for i, intent_name in enumerate(available_intents, 1):
                print(f"  [{i}] {intent_name}")
            print(f"  [0] Keep Auto-Predicted ({pred['intent']})")

            choice = input("\nEnter intent number (or press Enter for auto) >> ").strip()
            if not choice or choice == "0":
                chosen_intent = pred['intent']
            else:
                try:
                    idx = int(choice) - 1
                    chosen_intent = available_intents[idx]
                except Exception:
                    print("Invalid choice. Skipping.")
                    continue

            if chosen_intent in intents_map:
                existing = [p.lower() for p in intents_map[chosen_intent]["patterns"]]
                if phrase.lower() not in existing:
                    intents_map[chosen_intent]["patterns"].append(phrase.lower())
                    with open(INTENTS_FILE, "w", encoding="utf-8") as f:
                        json.dump({"intents": list(intents_map.values())}, f, indent=2)
                    intent_classifier.load_dataset()
                    print(f"[OK] Learned successfully: '{phrase}' -> {chosen_intent}")
                else:
                    print("Phrase already exists in dataset.")

        except KeyboardInterrupt:
            break

    print("\nInteractive training session ended.")

def main():
    parser = argparse.ArgumentParser(description="AJAX AI Training System")
    parser.add_argument("--interactive", action="store_true", help="Start Interactive Teaching Mode")
    args = parser.parse_args()

    if args.interactive:
        interactive_training_mode()
    else:
        train_from_sources()

if __name__ == "__main__":
    main()
