"""Shared intent dataset loader with optional supplemental vocabulary support."""

import json
import os
from typing import Any, Dict


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SUPPLEMENTAL_DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "intent_variants.json")
EXPANSION_DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "intent_expansion.json")

# These categories describe the same user goal closely enough that a single
# specialist intent is easier to train, route, and maintain. Unique system,
# RAG, network, calculation, and safety actions intentionally remain separate.
INTENT_MERGE_MAP = {
    "DEFINE_TERM": "EXPLAIN_CONCEPT",
    "EXTRACT_KEY_POINTS": "SUMMARIZE_TEXT",
    "PROOFREAD_TEXT": "TEXT_EDITING",
    "GRAMMAR_CHECK": "TEXT_EDITING",
    "GENERATE_IDEA": "BRAINSTORM",
    "MAKE_PLAN": "TASK_PLANNING",
    "CREATE_CHECKLIST": "TASK_PLANNING",
    "PRIORITIZE_TASKS": "TASK_PLANNING",
    "EMAIL_DRAFT": "EMAIL_ASSIST",
    "EMAIL_REWRITE": "EMAIL_ASSIST",
    "EMAIL_SUMMARY": "EMAIL_ASSIST",
}


def canonical_intent_name(name: str) -> str:
    """Return the stable target label for an intent, following merge aliases."""
    current = str(name or "GENERAL_CHAT").strip() or "GENERAL_CHAT"
    seen = set()
    while current in INTENT_MERGE_MAP and current not in seen:
        seen.add(current)
        current = INTENT_MERGE_MAP[current]
    return current


def _merge_intent_items(items):
    """Collapse aliases while retaining every unique training phrase."""
    merged = []
    by_name = {}
    for item in items or []:
        name = canonical_intent_name(item.get("intent"))
        target = by_name.get(name)
        if target is None:
            target = {
                key: value for key, value in item.items()
                if key not in {"intent", "patterns"}
            }
            target["intent"] = name
            target["patterns"] = []
            by_name[name] = target
            merged.append(target)

        existing = {str(pattern).casefold().strip() for pattern in target["patterns"]}
        for pattern in item.get("patterns", []):
            normalized = str(pattern).strip()
            if normalized and normalized.casefold() not in existing:
                target["patterns"].append(normalized)
                existing.add(normalized.casefold())
    return merged


def load_intent_dataset(dataset_path: str) -> Dict[str, Any]:
    """Load the base intent dataset and merge curated supplemental patterns."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    intents = _merge_intent_items(data.get("intents", []))
    merged_count = 0

    def merge_patterns(additional_intents):
        nonlocal merged_count
        intents_by_name = {item.get("intent"): item for item in intents}
        for additional in additional_intents:
            name = canonical_intent_name(additional.get("intent"))
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
