import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db
from core.router import router
from database.crud import create_conversation

def run_benchmark():
    init_db()
    conv_id = create_conversation("Speed Benchmark")
    
    queries = [
        "what time is it",
        "calculate 125 * 8",
        "tell me about machine learning",
        "who are you",
        "get system status"
    ]
    
    print("\n======================= SPEED & ACCURACY BENCHMARK =======================")
    for q in queries:
        t0 = time.perf_counter()
        res = router.process_query(q, conv_id)
        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000
        print(f"\n[QUERY]: \"{q}\"")
        print(f"[LATENCY]: {elapsed_ms:.2f} ms")
        print(f"[INTENT]: {res.get('intent')} (Tool: {res.get('tool_called')})")
        resp_clean = str(res.get('response', '')).replace('\n', ' ')
        print(f"[RESPONSE]: {resp_clean[:140]}...")
    print("\n===========================================================================")

if __name__ == "__main__":
    run_benchmark()
