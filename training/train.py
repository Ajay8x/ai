import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from database.crud import get_training_examples
from core.logger import training_logger

INTENTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "intents.json")

def retrain_from_database():
    training_logger.info("Starting intent model retraining...")
    approved_samples = get_training_examples(approved_only=True)
    
    if not os.path.exists(INTENTS_FILE):
        print("Base intents dataset not found.")
        return

    with open(INTENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    intents_map = {item["intent"]: item for item in data.get("intents", [])}

    added_count = 0
    for sample in approved_samples:
        intent = sample["intent"]
        text = sample["raw_text"]
        if intent in intents_map:
            if text not in intents_map[intent]["patterns"]:
                intents_map[intent]["patterns"].append(text)
                added_count += 1

    with open(INTENTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"intents": list(intents_map.values())}, f, indent=2)

    training_logger.info(f"Retraining complete. Ingested {added_count} new approved patterns.")
    print(f"Retraining complete! Ingested {added_count} new approved user samples into intents model.")

if __name__ == "__main__":
    retrain_from_database()
