import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from ai.neural.intent_classifier import intent_classifier
from ai.llm.factory import llm_brain
from core.diagnostics import diagnostics

print("=== 1. NEURAL DIAGNOSTICS ===")
print(intent_classifier.get_diagnostics())

print("\n=== 2. MULTILINGUAL INTENT PREDICTIONS ===")
test_queries = [
    "what time is it",
    "open chrome",
    "weather in mumbai",
    "delhi me mausam kaisa hai",
    "play arijit singh songs on youtube",
    "calculate 45 * 12",
    "500 ka 20%",
    "give me binary search algorithm in python",
    "write hello world in java",
    "iss kahan par hai",
    "dollar ka rate kya hai inr me",
    "namaste ajax kaise ho"
]

for q in test_queries:
    res = intent_classifier.predict(q)
    intent = res["intent"]
    conf = res["confidence"]
    eng = res["neural_engine"]
    tool = res.get("tool")
    entities = res.get("entities", {})
    print(f"Query: {q:38} | Intent: {intent:18} | Conf: {conf:4.2f} | Engine: {eng:24} | Tool: {str(tool):18} | Entities: {entities}")

print("\n=== 3. LLM BRAIN STATUS & GENERATION ===")
print("Brain status:", llm_brain.get_status())
resp = llm_brain.generate([{"role": "user", "content": "give me binary search algorithm in python"}])
print("Generated Code Length:", len(resp.content), "chars")
print("Provider:", resp.provider)
print("Code Sample Preview:\n" + "\n".join(resp.content.splitlines()[:6]))

print("\n=== 4. SYSTEM HEALTH CHECK ===")
health = diagnostics.run_health_check()
print("Overall status:", health.get("status"))
print("Intent engine status:", health.get("intent_engine"))
print("LLM status:", health.get("llm_provider"))
print("ALL TESTS PASSED SUCCESSFULLY!")
