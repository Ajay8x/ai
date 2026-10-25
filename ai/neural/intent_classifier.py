"""
AJAX AI - Hybrid Deep Neural Intent Classifier & Semantic Engine
Combines:
1. Deterministic Fast-Path Guards (Sub-millisecond latency for Math, Code, Public APIs, and System controls).
2. PyTorch Deep Neural Network (NeuralIntentNet) evaluated on GPU/CPU for learned token representation & softmax probabilities.
3. Multi-tier Cosine Semantic Vector Matching across dataset patterns (English, Hindi, Hinglish).
4. Ensemble Fusion & Calibrated Confidence Scoring.
5. Deep Multilingual Entity Extraction.
"""

import os
import json
import re
import math
import time
from typing import Dict, Any, List, Optional, Tuple

from core.logger import ajax_logger

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(BASE_DIR, "data", "intents.json")
MODELS_DIR = os.path.join(BASE_DIR, "models")
MODEL_PT_PATH = os.path.join(MODELS_DIR, "ajax_neural_intent.pt")
VOCAB_META_PATH = os.path.join(MODELS_DIR, "vocab_metadata.json")

# ----------------- PYTORCH NEURAL NETWORK DEFINITION ----------------- #
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    nn = object  # type: ignore

if TORCH_AVAILABLE:
    class NeuralIntentNet(nn.Module):
        """
        Deep Neural Network for Intent Classification.
        Architecture: Fully-Connected Multi-Layer Perceptron with Dropout & ReLU activations.
        """
        def __init__(self, vocab_size: int, hidden_dim: int, num_classes: int):
            super().__init__()
            self.fc1 = nn.Linear(vocab_size, hidden_dim)
            self.relu = nn.ReLU()
            self.dropout = nn.Dropout(0.2)
            self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
            self.fc3 = nn.Linear(hidden_dim // 2, num_classes)

        def forward(self, x):
            out = self.fc1(x)
            out = self.relu(out)
            out = self.dropout(out)
            out = self.fc2(out)
            out = self.relu(out)
            out = self.fc3(out)
            return out
else:
    class NeuralIntentNet:  # type: ignore
        pass


def tokenize(text: str) -> List[str]:
    """Tokenize text preserving words and alphanumeric tokens across English and Hindi."""
    return re.findall(r'[\w\u0900-\u097F]+', text.lower())


def text_to_vector(tokens: List[str]) -> Dict[str, int]:
    """Bag-of-words vector generation."""
    vec: Dict[str, int] = {}
    for t in tokens:
        vec[t] = vec.get(t, 0) + 1
    return vec


def cosine_sim(vec1: Dict[str, int], vec2: Dict[str, int]) -> float:
    """Computes cosine similarity between two frequency vectors."""
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    sum1 = sum([vec1[x]**2 for x in vec1.keys()])
    sum2 = sum([vec2[x]**2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    if not denominator:
        return 0.0
    return float(numerator) / denominator


# ----------------- DEFAULT INTENT TO TOOL MAPPING ----------------- #
INTENT_TOOL_MAP: Dict[str, Optional[str]] = {
    "TIME": "get_system_time",
    "SYSTEM_INFO": "get_system_status",
    "WEATHER": "get_weather",
    "SET_TIMER": "set_timer",
    "SET_ALARM": "set_timer",
    "PLAY_YOUTUBE": "play_youtube",
    "SEARCH_WEB": "search_web",
    "SEARCH_WIKIPEDIA": "search_wikipedia",
    "OPEN_WEBSITE": "open_website",
    "SEARCH_FILE": "search_files",
    "READ_FILE": "read_file",
    "MEMORY_SAVE": "remember_fact",
    "MEMORY_RECALL": "recall_memory",
    "CALCULATE": "calculate",
    "TRACK_ISS": "get_iss_coordinates",
    "TRACK_EARTHQUAKES": "get_recent_earthquakes",
    "CONVERT_CURRENCY": "convert_currency",
    "PUBLIC_HOLIDAYS": "get_public_holidays",
    "OPEN_APPLICATION": None,
    "CLOSE_APPLICATION": None,
    "WRITE_CODE": None,
    "GREETING": None,
    "HELP": None,
    "GENERAL_CHAT": None
}


class IntentClassifier:
    """
    Production-Grade Hybrid Neural Intent Classifier:
    - Loads PyTorch trained checkpoint (ajax_neural_intent.pt)
    - Fallback to high-performance Cosine Semantic Vector Matching
    - Multilingual entity extraction (English, Hindi, Hinglish)
    """
    def __init__(self, dataset_path: str = DATA_PATH):
        self.dataset_path = dataset_path
        self.intents: List[Dict[str, Any]] = []
        
        # PyTorch Neural Net Components
        self.neural_model: Optional[Any] = None
        self.word_to_idx: Dict[str, int] = {}
        self.intent_labels: List[str] = []
        self.vocab_size: int = 0
        self.num_classes: int = 0
        self.device = None
        self.device_desc = "CPU"
        self.neural_loaded: bool = False

        self.load_dataset()
        self.init_pytorch_neural_net()

    def init_pytorch_neural_net(self):
        """Initializes and loads PyTorch NeuralIntentNet checkpoint if available."""
        if not TORCH_AVAILABLE:
            ajax_logger.info("PyTorch not installed in environment; using pure semantic cosine engine.")
            return

        if not os.path.exists(MODEL_PT_PATH) or not os.path.exists(VOCAB_META_PATH):
            ajax_logger.info(f"Neural checkpoint not found at {MODEL_PT_PATH}; using semantic cosine engine.")
            return

        try:
            # 1. Device Selection (CUDA -> DirectML -> CPU)
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
                self.device_desc = f"NVIDIA CUDA GPU ({torch.cuda.get_device_name(0)})"
            else:
                try:
                    import torch_directml
                    if torch_directml.is_available():
                        self.device = torch_directml.device()
                        self.device_desc = "DirectML GPU Accelerator"
                except Exception:
                    pass
            
            if self.device is None:
                self.device = torch.device("cpu")
                self.device_desc = f"Multi-Threaded CPU ({torch.get_num_threads()} threads)"

            # 2. Load Vocabulary Metadata
            with open(VOCAB_META_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
                self.word_to_idx = meta.get("word_to_idx", {})
                self.intent_labels = meta.get("intent_labels", [])
                self.vocab_size = meta.get("vocab_size", len(self.word_to_idx))
                self.num_classes = meta.get("num_classes", len(self.intent_labels))

            # 3. Instantiate Neural Model
            model = NeuralIntentNet(vocab_size=self.vocab_size, hidden_dim=128, num_classes=self.num_classes)
            state_dict = torch.load(MODEL_PT_PATH, map_location=self.device)
            model.load_state_dict(state_dict)
            model.to(self.device)
            model.eval()

            self.neural_model = model
            self.neural_loaded = True
            ajax_logger.info(
                f"Loaded PyTorch Deep Neural Model on {self.device_desc} "
                f"({self.num_classes} classes, {self.vocab_size} vocab)."
            )
        except Exception as e:
            self.neural_loaded = False
            self.neural_model = None
            ajax_logger.warning(f"Could not load PyTorch neural intent model ({e}); falling back to cosine similarity.")

    def load_dataset(self):
        """Loads or reloads the reference intents.json dataset."""
        if os.path.exists(self.dataset_path):
            try:
                with open(self.dataset_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.intents = data.get("intents", [])
                ajax_logger.info(f"Loaded {len(self.intents)} intents into IntentClassifier.")
            except Exception as e:
                ajax_logger.error(f"Failed to load intents dataset: {e}")

    def _neural_predict(self, text: str) -> Tuple[Optional[str], float, List[Tuple[str, float]]]:
        """
        Runs PyTorch forward pass with Softmax normalization.
        Returns: (top_intent, top_confidence, top_3_candidates)
        """
        if not self.neural_loaded or self.neural_model is None or not TORCH_AVAILABLE:
            return None, 0.0, []

        try:
            tokens = tokenize(text)
            if not tokens:
                return None, 0.0, []

            x = torch.zeros((1, self.vocab_size), dtype=torch.float32, device=self.device)
            found_count = 0
            for t in tokens:
                if t in self.word_to_idx:
                    x[0, self.word_to_idx[t]] += 1.0
                    found_count += 1

            if found_count == 0:
                return None, 0.0, []

            with torch.no_grad():
                logits = self.neural_model(x)
                probs = torch.softmax(logits, dim=1)
                k = min(3, self.num_classes)
                top_p, top_i = torch.topk(probs, k=k)

            top_intent = self.intent_labels[top_i[0][0].item()]
            top_prob = float(top_p[0][0].item())

            candidates = []
            for j in range(k):
                lbl = self.intent_labels[top_i[0][j].item()]
                c_prob = round(float(top_p[0][j].item()), 4)
                candidates.append((lbl, c_prob))

            return top_intent, top_prob, candidates
        except Exception as e:
            ajax_logger.warning(f"PyTorch neural inference notice: {e}")
            return None, 0.0, []

    def _cosine_predict(self, text: str, tokens: List[str]) -> Tuple[str, float, Optional[str], Optional[str]]:
        """
        Evaluates input tokens against all dataset patterns using Cosine Semantic Similarity.
        Returns: (best_intent, best_confidence, best_tool, best_response)
        """
        text_clean = text.lower().strip()
        vec = text_to_vector(tokens)
        text_len = max(len(tokens), 1)

        best_intent = "GENERAL_CHAT"
        best_confidence = 0.0
        best_tool = None
        best_response = None

        for item in self.intents:
            intent_name = item.get("intent", "GENERAL_CHAT")
            tool_name = item.get("tool")
            resp = item.get("response")

            for pattern in item.get("patterns", []):
                pattern_clean = pattern.lower().strip()
                pat_tokens = tokenize(pattern_clean)
                pat_len = max(len(pat_tokens), 1)

                # Exact match
                if pattern_clean == text_clean:
                    score = 1.0
                elif re.search(r'\b' + re.escape(pattern_clean) + r'\b', text_clean):
                    coverage = pat_len / text_len
                    if intent_name in ["GREETING", "FAREWELL", "THANK_YOU", "HELP"]:
                        if coverage >= 0.5 or text_len <= 2:
                            score = 0.95
                        else:
                            score = 0.20 * coverage
                    else:
                        score = 0.65 + (0.35 * coverage)
                else:
                    pat_vec = text_to_vector(pat_tokens)
                    score = cosine_sim(vec, pat_vec)

                if score > best_confidence:
                    best_confidence = score
                    best_intent = intent_name
                    best_tool = tool_name
                    best_response = resp

        return best_intent, best_confidence, best_tool, best_response

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Main Prediction Pipeline:
        1. Sub-millisecond deterministic guards (Math, Code, Emergency APIs).
        2. PyTorch Deep Neural Network prediction (Softmax probabilities).
        3. Semantic Cosine Vector Space matching.
        4. Ensemble fusion for maximum accuracy and confidence.
        5. Deep entity extraction.
        """
        start_t = time.perf_counter()
        text_clean = text.lower().strip()
        tokens = tokenize(text_clean)

        # ----------------- GUARD 1: ARITHMETIC / MATH ----------------- #
        is_explicit_math = bool(
            re.match(r'^(\s*calculate\s+)?(\d+(\.\d+)?\s*[\+\-\*\/\%\^xX÷]\s*\d+(\.\d+)?(\s*[\+\-\*\/\%\^xX÷]\s*\d+(\.\d+)?)*|\d+(\.\d+)?\s*%\s*(of|ka\s*)?\d+(\.\d+)?|\d+(\.\d+)?\s*(ka|of)\s*\d+(\.\d+)?\s*%|sqrt\(\d+(\.\d+)?\))\s*$', text_clean)
            or re.search(r'\d+\s*(?:ka|of)\s*\d+\s*%', text_clean)
            or re.search(r'\d+\s*%\s*(?:of|ka)\s*\d+', text_clean)
            or re.search(r'\b(calculate|compute|square\s+root|sqrt|factorial)\b', text_clean)
        )
        # Avoid coding queries with math keywords
        is_coding_kw = bool(re.search(r'\b(code|program|script|class|method|function|def|void)\b', text_clean))
        if is_explicit_math and not is_coding_kw:
            return {
                "intent": "CALCULATE",
                "confidence": 1.0,
                "tool": "calculate",
                "entities": {"expression": text_clean},
                "predefined_response": None,
                "neural_engine": "deterministic_guard",
                "inference_time_ms": round((time.perf_counter() - start_t) * 1000, 3)
            }

        # ----------------- GUARD 2: PROGRAMMING & CODE GENERATION ----------------- #
        is_explicit_app_launch = bool(re.search(r'\b(open|launch|kholo|start)\s+(vs\s*code|vscode|code\s*editor)\b', text_clean))
        is_coding = not is_explicit_app_launch and bool(
            re.search(r'\b(code|program|coding|script|class|method|function|syntax|algorithm|hello\s+world|loop|array|pointer|query|snippet)\b', text_clean)
            or re.search(r'\b(java|python|c\+\+|cpp|c#|javascript|js|html|css|sql|rust|golang|php|swift|kotlin|typescript|ts)\b', text_clean)
        )
        if is_coding:
            lang_match = re.search(r'\b(java|python|c\+\+|cpp|c#|javascript|js|html|css|sql|rust|golang|php|swift|kotlin|typescript|ts)\b', text_clean)
            target_lang = lang_match.group(1) if lang_match else "generic"
            return {
                "intent": "WRITE_CODE",
                "confidence": 0.96,
                "tool": None,
                "entities": {"language": target_lang, "query": text_clean},
                "predefined_response": None,
                "neural_engine": "deterministic_guard",
                "inference_time_ms": round((time.perf_counter() - start_t) * 1000, 3)
            }

        # ----------------- GUARD 3: PUBLIC APIS (ISS, EARTHQUAKES, CURRENCY, HOLIDAYS) ----------------- #
        if re.search(r'\b(iss\b|international\s+space\s+station|space\s+station\s+(location|position|coordinates)|iss\s+kahan\s+hai)', text_clean):
            return {
                "intent": "TRACK_ISS",
                "confidence": 0.98,
                "tool": "get_iss_coordinates",
                "entities": {},
                "predefined_response": None,
                "neural_engine": "deterministic_guard",
                "inference_time_ms": round((time.perf_counter() - start_t) * 1000, 3)
            }

        if re.search(r'\b(earthquake|earthquakes|bhookamp|bhukamp|seismic\s+activity)\b', text_clean):
            return {
                "intent": "TRACK_EARTHQUAKES",
                "confidence": 0.96,
                "tool": "get_recent_earthquakes",
                "entities": {"limit": 5, "min_magnitude": 4.0},
                "predefined_response": None,
                "neural_engine": "deterministic_guard",
                "inference_time_ms": round((time.perf_counter() - start_t) * 1000, 3)
            }

        curr_match = re.search(r'(\d+(?:\.\d+)?)\s*(usd|dollar|eur|euro|inr|gbp)\s*(?:to|in|me|ka)\s*(inr|usd|eur|gbp|rupee)', text_clean)
        if curr_match or re.search(r'\b(currency\s+exchange|exchange\s+rate|dollar\s+ka\s+rate|dollar\s+rate|usd\s+to\s+inr|dollar\s+to\s+inr)\b', text_clean):
            amt = float(curr_match.group(1)) if curr_match else 1.0
            from_c = "USD"
            to_c = "INR"
            if curr_match:
                fc = curr_match.group(2).upper()
                tc = curr_match.group(3).upper()
                from_c = "USD" if ("DOLLAR" in fc or "USD" in fc) else ("EUR" if "EUR" in fc else fc)
                to_c = "INR" if ("INR" in tc or "RUPEE" in tc) else tc
            return {
                "intent": "CONVERT_CURRENCY",
                "confidence": 0.97,
                "tool": "convert_currency",
                "entities": {"amount": amt, "from_currency": from_c, "to_currency": to_c},
                "predefined_response": None,
                "neural_engine": "deterministic_guard",
                "inference_time_ms": round((time.perf_counter() - start_t) * 1000, 3)
            }

        if re.search(r'\b(public\s+holiday|public\s+holidays|holiday\s+list|chhutti|chhuttiyan|holidays\s+in\s+india)\b', text_clean):
            return {
                "intent": "PUBLIC_HOLIDAYS",
                "confidence": 0.96,
                "tool": "get_public_holidays",
                "entities": {"country_code": "IN"},
                "predefined_response": None,
                "neural_engine": "deterministic_guard",
                "inference_time_ms": round((time.perf_counter() - start_t) * 1000, 3)
            }

        # ----------------- TIER 2: PYTORCH DEEP NEURAL EVALUATION ----------------- #
        neural_intent, neural_conf, candidates = self._neural_predict(text_clean)

        # ----------------- TIER 3: COSINE SEMANTIC VECTOR MATCHING ----------------- #
        cos_intent, cos_conf, cos_tool, cos_resp = self._cosine_predict(text_clean, tokens)

        # ----------------- TIER 4: ENSEMBLE FUSION ----------------- #
        final_intent = cos_intent
        final_conf = cos_conf
        final_tool = cos_tool or INTENT_TOOL_MAP.get(cos_intent)
        final_resp = cos_resp
        engine_used = "semantic_cosine"

        if neural_intent:
            if neural_intent == cos_intent:
                # Both models agree: high confidence reinforcement!
                final_intent = neural_intent
                final_conf = min(1.0, max(neural_conf, cos_conf) + 0.05)
                engine_used = "neural_ensemble_consensus"
            elif neural_conf >= 0.88 and cos_conf < 0.70:
                # Deep neural model is distinctly confident
                final_intent = neural_intent
                final_conf = neural_conf
                final_tool = INTENT_TOOL_MAP.get(neural_intent)
                engine_used = "pytorch_deep_learning"
            elif cos_conf >= 0.90:
                # Direct pattern string hit
                final_intent = cos_intent
                final_conf = cos_conf
                engine_used = "semantic_cosine_exact"
            else:
                # Blend with weight
                if neural_conf > cos_conf:
                    final_intent = neural_intent
                    final_conf = round(neural_conf * 0.7 + cos_conf * 0.3, 2)
                    final_tool = INTENT_TOOL_MAP.get(neural_intent)
                    engine_used = "pytorch_deep_learning"
                else:
                    final_intent = cos_intent
                    final_conf = round(cos_conf * 0.7 + neural_conf * 0.3, 2)
                    engine_used = "semantic_cosine"

        if not final_tool and final_intent in INTENT_TOOL_MAP:
            final_tool = INTENT_TOOL_MAP[final_intent]

        # ----------------- TIER 5: DEEP MULTILINGUAL ENTITY EXTRACTION ----------------- #
        entities: Dict[str, Any] = {}

        if final_intent in ["OPEN_APPLICATION", "CLOSE_APPLICATION"]:
            m = re.search(r'(?:open|launch|close|start|chalao|kholo|band\s+karo)\s+([a-zA-Z0-9\s]+)', text_clean)
            if m:
                app_name = m.group(1).strip()
                # Clean filler words
                app_name = re.sub(r'\b(app|application|software)\b', '', app_name).strip()
                entities["app_name"] = app_name or "application"
            else:
                entities["app_name"] = "application"

        elif final_intent in ["SEARCH_WEB", "PLAY_YOUTUBE", "SEARCH_WIKIPEDIA"]:
            m = re.search(r'(?:search|play|find|about|par\s+chalao|bajao|sunao)\s+(?:for\s+)?([a-zA-Z0-9\s\u0900-\u097F]+)', text_clean)
            if m:
                q = m.group(1).strip()
                q = re.sub(r'\b(on\s+youtube|on\s+google|on\s+web|par)\b', '', q).strip()
                entities["query"] = q or text_clean
            else:
                entities["query"] = text_clean

        elif final_intent == "WEATHER":
            m = re.search(r'(?:in|for|at|ka\s+mausam|me\s+mausam)\s+([a-zA-Z\u0900-\u097F]+)', text_clean)
            if m:
                entities["city"] = m.group(1).strip()
            else:
                # Check known Indian and major global cities in query
                known_cities = ["delhi", "mumbai", "bangalore", "bengaluru", "kolkata", "chennai", "hyderabad", "pune", "ahmedabad", "jaipur", "london", "new york", "tokyo", "paris", "dubai"]
                for c in known_cities:
                    if c in text_clean:
                        entities["city"] = c.title()
                        break
                if "city" not in entities:
                    entities["city"] = "Delhi"

        elif final_intent in ["SET_TIMER", "SET_ALARM"]:
            m = re.search(r'(\d+)\s*(minute|min|minutes|second|sec|seconds|hour|hours|ghanta|ghante)', text_clean)
            if m:
                entities["duration"] = int(m.group(1))
                entities["unit"] = m.group(2)
            else:
                entities["duration"] = 5
                entities["unit"] = "minutes"

        elif final_intent in ["MEMORY_SAVE", "MEMORY_RECALL"]:
            m = re.search(r'(?:remember\s+that|yaad\s+rakhna\s+ki|yaad\s+rakho\s+ki)\s+(.+)', text_clean)
            if m:
                entities["note"] = m.group(1).strip()
            else:
                entities["query"] = text_clean

        elif final_intent in ["SEARCH_FILE", "READ_FILE"]:
            m = re.search(r'(?:find|search|read|open|dekho)\s+(?:file\s+)?([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)', text_clean)
            if m:
                entities["filename"] = m.group(1).strip()

        latency_ms = round((time.perf_counter() - start_t) * 1000, 3)

        return {
            "intent": final_intent,
            "confidence": round(float(final_conf), 2),
            "tool": final_tool,
            "entities": entities,
            "predefined_response": final_resp,
            "neural_engine": engine_used,
            "top_candidates": candidates if candidates else [(final_intent, round(float(final_conf), 2))],
            "inference_time_ms": latency_ms
        }

    def get_diagnostics(self) -> Dict[str, Any]:
        """Provides real-time telemetry of the neural intent classifier subsystem."""
        return {
            "pytorch_available": TORCH_AVAILABLE,
            "neural_loaded": self.neural_loaded,
            "compute_device": self.device_desc,
            "vocab_size": self.vocab_size,
            "num_classes": self.num_classes,
            "intent_labels": self.intent_labels,
            "intents_dataset_count": len(self.intents),
            "checkpoint_path": MODEL_PT_PATH if os.path.exists(MODEL_PT_PATH) else "Not found"
        }


# Global Singleton Instance
intent_classifier = IntentClassifier()
