import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.neural.intent_classifier import intent_classifier

TEST_CASES = [
    ("what is the time right now", "TIME"),
    ("current time batao", "TIME"),
    ("open chrome browser", "OPEN_APPLICATION"),
    ("bhai chrome kholo", "OPEN_APPLICATION"),
    ("check my battery and cpu status", "SYSTEM_INFO"),
    ("system info dikhao", "SYSTEM_INFO"),
    ("search on google for latest ai news", "SEARCH_WEB"),
    ("play arijit singh on youtube", "PLAY_YOUTUBE"),
    ("take a screenshot of desktop", "SCREENSHOT"),
    ("volume badhao", "VOLUME_CONTROL"),
    ("weather in delhi", "WEATHER"),
    ("set a timer for 5 minutes", "SET_TIMER"),
    ("help me", "HELP")
]

def run_evaluation():
    print("\n=== RUNNING INTENT MODEL EVALUATION ===")
    correct = 0
    total = len(TEST_CASES)

    for query, expected in TEST_CASES:
        res = intent_classifier.predict(query)
        predicted = res["intent"]
        conf = res["confidence"]
        is_ok = (predicted == expected)
        if is_ok:
            correct += 1
            status = "PASS"
        else:
            status = "FAIL"
            
        print(f"[{status}] '{query}' -> Predicted: {predicted} (Confidence: {conf}) | Expected: {expected}")

    accuracy = (correct / total) * 100
    print(f"\nBenchmark Accuracy: {accuracy:.1f}% ({correct}/{total} passed)\n")
    return accuracy

if __name__ == "__main__":
    run_evaluation()
