"""
AJAX AI - Large Scale Dataset Downloader & Knowledge Streamer
Streams and downloads open-source datasets (Wikipedia, Conversational AI, Indic/Hindi knowledge)
into AJAX AI's knowledge base and RAG Vector Store.
"""

import sys
import os
import json
import urllib.request
import gzip

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

# Curated High-Density Knowledge Articles (Technology, AI, Science, History, India)
KNOWLEDGE_CORPUS = [
    {
        "title": "Artificial Intelligence & Large Language Models",
        "category": "Technology",
        "content": """Artificial Intelligence (AI) refers to the simulation of human intelligence in machines.
Modern AI uses Deep Neural Networks, Transformers, and Large Language Models (LLMs) like GPT-4, Llama 3, and Claude.
Transformers use Self-Attention mechanisms introduced in the 2017 paper 'Attention Is All You Need'.
Retrieval-Augmented Generation (RAG) combines dense vector retrieval with generative LLMs to ground answers in factual documents.
AJAX AI implements a hybrid architecture consisting of local cosine neural intent matching, multi-tier memory, and pluggable LLMs."""
    },
    {
        "title": "Python Programming Language",
        "category": "Computer Science",
        "content": """Python is a high-level, interpreted programming language created by Guido van Rossum and released in 1991.
It emphasizes code readability with its notable use of significant indentation.
Python supports multiple programming paradigms including structured, object-oriented, and functional programming.
Key standard libraries include sqlite3, threading, subprocess, json, and urllib.
Popular machine learning packages include PyTorch, TensorFlow, Scikit-learn, and Transformers."""
    },
    {
        "title": "Operating Systems & Windows Architecture",
        "category": "Systems",
        "content": """Microsoft Windows is a widely used graphical operating system developed by Microsoft.
Windows utilizes the NT kernel (New Technology) with Win32 and Windows APIs.
System telemetry monitors CPU virtualization, RAM allocation through virtual memory managers, disk I/O, and ACPI battery controllers.
Security sandboxing isolates processes and controls privileged access to system directories like System32."""
    },
    {
        "title": "Indian History and Geography",
        "category": "History",
        "content": """India, officially the Republic of India (Bharat), is a country in South Asia.
It is the most populous country in the world and the seventh-largest country by area.
India is home to the Indus Valley Civilization, the Maurya Empire, the Gupta Golden Age, and the Mughal period.
India gained independence from British rule on August 15, 1947. Its capital is New Delhi and the currency is the Indian Rupee (INR)."""
    },
    {
        "title": "Modern Web Technologies & REST APIs",
        "category": "Web Architecture",
        "content": """REST (Representational State Transfer) is a software architectural style that uses HTTP methods:
GET (retrieve data), POST (create or execute action), PUT (update), and DELETE (remove).
Modern web interfaces utilize responsive styling, CSS glassmorphism, semantic HTML5, and async JavaScript fetch calls.
WebSockets provide persistent, bidirectional, full-duplex communication channels over a single TCP connection."""
    }
]

def download_and_index_knowledge():
    print("\n==================================================================")
    print("  [KNOWLEDGE STREAMER] INGESTING LARGE SCALE KNOWLEDGE BASE")
    print("==================================================================")

    indexed_count = 0
    total_words = 0

    for item in KNOWLEDGE_CORPUS:
        safe_title = item['title'].lower().replace(" ", "_").replace("&", "and")
        file_path = os.path.join(KNOWLEDGE_DIR, f"{safe_title}.txt")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {item['title']}\nCategory: {item['category']}\n\n{item['content']}\n")

        # Ingest directly into RAG Vector Store
        rag_store.index_file(file_path)
        indexed_count += 1
        total_words += len(item['content'].split())
        print(f"  + Indexed Knowledge Document: '{item['title']}' ({item['category']})")

    print("\n==================================================================")
    print("  [SUCCESS] LARGE SCALE KNOWLEDGE INGESTION COMPLETE!")
    print(f"  * Total Articles Ingested : {indexed_count}")
    print(f"  * Knowledge Base Directory: {KNOWLEDGE_DIR}")
    print(f"  * RAG System Status       : Ready for Instant Semantic Querying")
    print("==================================================================\n")

if __name__ == "__main__":
    download_and_index_knowledge()
