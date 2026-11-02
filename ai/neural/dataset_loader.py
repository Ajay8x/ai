"""Shared intent dataset loader with optional supplemental vocabulary support."""

import json
import os
from typing import Any, Dict


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SUPPLEMENTAL_DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "intent_variants.json")


def load_intent_dataset(dataset_path: str) -> Dict[str, Any]:
    """Load the base intent dataset and merge curated supplemental patterns."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    intents = data.get("intents", [])
    if not os.path.exists(SUPPLEMENTAL_DATASET_PATH):
        return {"intents": intents}

    with open(SUPPLEMENTAL_DATASET_PATH, "r", encoding="utf-8") as f:
        supplemental = json.load(f)

    additions = {
        item.get("intent"): item.get("patterns", [])
        for item in supplemental.get("intents", [])
    }

    merged_count = 0
    for intent in intents:
        patterns = intent.setdefault("patterns", [])
        existing = {str(pattern).casefold().strip() for pattern in patterns}
        for pattern in additions.get(intent.get("intent"), []):
            normalized = str(pattern).strip()
            if normalized and normalized.casefold() not in existing:
                patterns.append(normalized)
                existing.add(normalized.casefold())
                merged_count += 1

    data["intents"] = intents
    data["supplemental_patterns_merged"] = merged_count
    return data
