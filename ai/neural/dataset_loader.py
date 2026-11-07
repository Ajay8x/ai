"""Shared intent dataset loader with optional supplemental vocabulary support."""

import json
import os
from typing import Any, Dict


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SUPPLEMENTAL_DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "intent_variants.json")
EXPANSION_DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "intent_expansion.json")


def load_intent_dataset(dataset_path: str) -> Dict[str, Any]:
    """Load the base intent dataset and merge curated supplemental patterns."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    intents = data.get("intents", [])
    merged_count = 0

    def merge_patterns(additional_intents):
        nonlocal merged_count
        intents_by_name = {item.get("intent"): item for item in intents}
        for additional in additional_intents:
            name = additional.get("intent")
            if not name:
                continue
            target = intents_by_name.get(name)
            if target is None:
                target = {
                    "intent": name,
                    "patterns": [],
                    "tool": additional.get("tool"),
                    "response": additional.get("response")
                }
                intents.append(target)
                intents_by_name[name] = target

            patterns = target.setdefault("patterns", [])
            existing = {str(pattern).casefold().strip() for pattern in patterns}
            for pattern in additional.get("patterns", []):
                normalized = str(pattern).strip()
                if normalized and normalized.casefold() not in existing:
                    patterns.append(normalized)
                    existing.add(normalized.casefold())
                    merged_count += 1

    if os.path.exists(SUPPLEMENTAL_DATASET_PATH):
        with open(SUPPLEMENTAL_DATASET_PATH, "r", encoding="utf-8") as f:
            supplemental = json.load(f)
        merge_patterns(supplemental.get("intents", []))

    if os.path.exists(EXPANSION_DATASET_PATH):
        with open(EXPANSION_DATASET_PATH, "r", encoding="utf-8") as f:
            expansion = json.load(f)
        merge_patterns(expansion.get("intents", []))

    data["intents"] = intents
    data["supplemental_patterns_merged"] = merged_count
    return data
