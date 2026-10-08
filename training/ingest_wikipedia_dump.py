"""
AJAX AI - Wikimedia & Wikipedia Ingestion Engine
Streams Wikipedia articles directly via Wikimedia APIs or extracts offline Wikipedia XML dumps.
"""

import sys
import os
import re
import json
import requests

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.rag.store import rag_store
from core.logger import training_logger

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "knowledge")
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

TOP_WIKI_TOPICS = [
    "Artificial intelligence", "Machine learning", "Quantum computing", "Neural network",
    "Computer science", "Python (programming language)", "Operating system", "Microsoft Windows",
    "Albert Einstein", "Isaac Newton", "Alan Turing", "Nikola Tesla",
    "India", "History of India", "Space exploration", "Solar System", "Milky Way",
    "Internet", "World Wide Web", "Cybersecurity", "Robotics", "Renewable energy"
]

def fetch_wikipedia_articles(topics: list = TOP_WIKI_TOPICS):
    print("\n==================================================================")
    print("  [WIKIMEDIA STREAMER] FETCHING KNOWLEDGE ARTICLES")
    print("==================================================================")
    print(f" Target Knowledge Directory: {KNOWLEDGE_DIR}")
    print(f" Topics to Ingest: {len(topics)}\n")

    ingested = 0

    for topic in topics:
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ', '_')}"
            headers = {"User-Agent": "AJAX-AI/3.0 (Personal AI Research Assistant)"}
            
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                title = data.get("title", topic)
                extract = data.get("extract", "")
                page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

                if extract and len(extract) > 50:
                    safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', title.lower())
                    file_path = os.path.join(KNOWLEDGE_DIR, f"wiki_{safe_title}.txt")

                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(f"# {title}\nURL: {page_url}\n\n{extract}\n")

                    rag_store.index_file(file_path)
                    ingested += 1
                    print(f"  + Ingested: '{title}' ({len(extract.split())} words)")
        except Exception as e:
            print(f"  - Skipped '{topic}': {e}")

    print("\n==================================================================")
    print(f"  [SUCCESS] WIKIPEDIA STREAMING COMPLETE! (+{ingested} Articles)")
    print(f"  * All articles indexed into RAG for offline querying!")
    print("==================================================================\n")

if __name__ == "__main__":
    fetch_wikipedia_articles()
