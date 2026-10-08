"""
AJAX AI - Mass Knowledge Harvester & Global Dataset Downloader
Downloads over 50+ comprehensive knowledge topics across Programming, Science, Mathematics,
History, Indian Constitution, ISRO Space Missions, and World Architecture into RAG Knowledge Base.
"""

import sys
import os
import re
import requests
import time

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

# 50+ Key Encyclopedic Topics to Download
EXPANDED_TOPICS = [
    # Programming & Tech
    "C (programming language)", "C++", "Java (programming language)", "JavaScript", "Rust (programming language)",
    "SQL", "Git", "Linux", "Docker (software)", "Data structure", "Algorithm", "Software engineering",
    "Database", "Cloud computing", "Microservices", "Computer network",
    
    # Science & Physics
    "General relativity", "Quantum mechanics", "Thermodynamics", "Black hole", "Big Bang",
    "DNA", "Evolution", "Cell (biology)", "CRISPR gene editing", "Photosynthesis", "Periodic table",
    
    # Mathematics
    "Calculus", "Linear algebra", "Probability theory", "Statistics", "Number theory", "Discrete mathematics",
    
    # India & Space
    "Constitution of India", "ISRO", "Chandrayaan-3", "Mars Orbiter Mission", "A. P. J. Abdul Kalam",
    "Economy of India", "Geography of India", "Ganges", "Himalayas", "Parliament of India",
    
    # World History & Society
    "World War I", "World War II", "United Nations", "Industrial Revolution", "Renaissance", "Ancient Egypt",
    "Economics", "Psychology", "Philosophy", "Astronomy"
]

def harvest_mass_knowledge():
    print("\n==================================================================")
    print("  [MASS KNOWLEDGE HARVESTER] DOWNLOADING 50+ GLOBAL TOPICS")
    print("==================================================================")
    print(f" Target Directory: {KNOWLEDGE_DIR}")
    print(f" Total Topics in Queue: {len(EXPANDED_TOPICS)}\n")

    success_count = 0
    headers = {"User-Agent": "AJAX-AI/3.0 (Educational AI Research Assistant; Contact: research@ajax.ai)"}

    for idx, topic in enumerate(EXPANDED_TOPICS, 1):
        clean_topic = topic.replace(" ", "_")
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{clean_topic}"
        
        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                title = data.get("title", topic)
                extract = data.get("extract", "")
                page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

                if extract and len(extract) > 40:
                    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', title.lower())
                    out_path = os.path.join(KNOWLEDGE_DIR, f"wiki_{safe_name}.txt")

                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(f"# {title}\nURL: {page_url}\n\n{extract}\n")

                    rag_store.index_file(out_path)
                    success_count += 1
                    print(f"  [{idx}/{len(EXPANDED_TOPICS)}] Ingested: '{title}' ({len(extract.split())} words)")
            time.sleep(0.05) # Polite request pacing
        except Exception as e:
            print(f"  [{idx}/{len(EXPANDED_TOPICS)}] Skipped '{topic}': {e}")

    print("\n==================================================================")
    print(f"  [SUCCESS] MASS DOWNLOAD COMPLETE! (+{success_count} Articles Ingested)")
    print(f"  * Total Knowledge Documents in RAG: {len(rag_store.documents)} chunks")
    print("==================================================================\n")

if __name__ == "__main__":
    harvest_mass_knowledge()
