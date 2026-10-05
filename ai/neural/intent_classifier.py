"""
AJAX AI - Intent Engine & Semantic Intent Classifier
Evaluates natural language input against intent datasets using semantic token matching and cosine similarity.
"""

import os
import json
import re
import math
from typing import Dict, Any, List, Optional, Tuple
from core.logger import ajax_logger

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "intents.json")

def tokenize(text: str) -> List[str]:
    return re.findall(r'\w+', text.lower())

def text_to_vector(tokens: List[str]) -> Dict[str, int]:
    vec: Dict[str, int] = {}
    for t in tokens:
        vec[t] = vec.get(t, 0) + 1
    return vec

def cosine_sim(vec1: Dict[str, int], vec2: Dict[str, int]) -> float:
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    sum1 = sum([vec1[x]**2 for x in vec1.keys()])
    sum2 = sum([vec2[x]**2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    if not denominator:
        return 0.0
    return float(numerator) / denominator

class IntentClassifier:
    def __init__(self, dataset_path: str = DATA_PATH):
        self.dataset_path = dataset_path
        self.intents: List[Dict[str, Any]] = []
        self.load_dataset()

    def load_dataset(self):
        if os.path.exists(self.dataset_path):
            try:
                with open(self.dataset_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.intents = data.get("intents", [])
                ajax_logger.info(f"Loaded {len(self.intents)} intents into IntentClassifier.")
            except Exception as e:
                ajax_logger.error(f"Failed to load intents dataset: {e}")

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Predict intent with confidence score (0.0 to 1.0) and extracted entities.
        """
        text_clean = text.lower().strip()
        tokens = tokenize(text_clean)
        vec = text_to_vector(tokens)

        best_intent = "GENERAL_CHAT"
        best_confidence = 0.0
        best_tool = None
        best_response = None
        entities = {}

        for item in self.intents:
            intent_name = item["intent"]
            tool_name = item.get("tool")
            resp = item.get("response")

            for pattern in item.get("patterns", []):
                pattern_clean = pattern.lower().strip()
                
                # Direct match with word boundaries to avoid substring false positives (e.g. 'hi' in 'delhi')
                if pattern_clean == text_clean:
                    score = 1.0
                elif re.search(r'\b' + re.escape(pattern_clean) + r'\b', text_clean):
                    score = 0.95
                else:
                    pat_vec = text_to_vector(tokenize(pattern_clean))
                    score = cosine_sim(vec, pat_vec)

                if score > best_confidence:
                    best_confidence = score
                    best_intent = intent_name
                    best_tool = tool_name
                    best_response = resp

        # Extract basic entities (e.g. app name, search query, city)
        if best_intent == "OPEN_APPLICATION" or best_intent == "CLOSE_APPLICATION":
            # Extract anything after "open" or "close" or "launch"
            m = re.search(r'(?:open|launch|close|start|chalao|kholo|band\s+karo)\s+([a-zA-Z0-9\s]+)', text_clean)
            if m:
                entities["app_name"] = m.group(1).strip()
        elif best_intent == "SEARCH_WEB" or best_intent == "PLAY_YOUTUBE" or best_intent == "SEARCH_WIKIPEDIA":
            m = re.search(r'(?:search|play|find|about|par\s+chalao)\s+(?:for\s+)?([a-zA-Z0-9\s]+)', text_clean)
            if m:
                entities["query"] = m.group(1).strip()
            else:
                entities["query"] = text_clean
        elif best_intent == "WEATHER":
            m = re.search(r'(?:in|for|at|ka\s+mausam)\s+([a-zA-Z]+)', text_clean)
            if m:
                entities["city"] = m.group(1).strip()

        return {
            "intent": best_intent,
            "confidence": round(best_confidence, 2),
            "tool": best_tool,
            "entities": entities,
            "predefined_response": best_response
        }

intent_classifier = IntentClassifier()
