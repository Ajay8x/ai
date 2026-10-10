"""
AJAX AI - HuggingFace Dataset Automated Streamer & Ingestor
Fetches large-scale datasets from HuggingFace Datasets API and saves them directly to JSONL / PostgreSQL.
"""

import sys
import json
import time
import urllib.request
import argparse
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_open_orca(total_records: int = 1000, batch_size: int = 100, output_file: str = "data/open_orca.jsonl"):
    output_path = os.path.join(BASE_DIR, output_file)
    print(f"[*] Starting download of {total_records} records from Open-Orca...")
    print(f"[*] Output destination: {output_path}")

    downloaded = 0
    offset = 0

    with open(output_path, "a", encoding="utf-8") as f:
        while downloaded < total_records:
            length = min(batch_size, total_records - downloaded)
            url = f"https://datasets-server.huggingface.co/rows?dataset=Open-Orca%2FOpenOrca&config=default&split=train&offset={offset}&length={length}"
            
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "AjaxAI/3.0 Dataset Fetcher"})
                with urllib.request.urlopen(req, timeout=20) as res:
                    data = json.loads(res.read().decode("utf-8"))
                    rows = data.get("rows", [])
                    
                    if not rows:
                        print("\n[!] No more rows available.")
                        break

                    for r in rows:
                        row_data = r.get("row", {})
                        record = {
                            "id": row_data.get("id"),
                            "system_prompt": row_data.get("system_prompt", ""),
                            "question": row_data.get("question", ""),
                            "response": row_data.get("response", "")
                        }
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")
                        downloaded += 1

                    print(f"[*] Progress: {downloaded}/{total_records} rows downloaded (Offset: {offset})", end="\r")
                    offset += length
                    time.sleep(0.3) # Respectful API rate limiting
            except Exception as e:
                print(f"\n[!] Error fetching at offset {offset}: {e}. Retrying in 2s...")
                time.sleep(2)

    print(f"\n[SUCCESS] Successfully downloaded {downloaded} records to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch HuggingFace Datasets")
    parser.add_argument("--count", type=int, default=100, help="Number of records to download (default: 100)")
    parser.add_argument("--out", type=str, default="data/open_orca.jsonl", help="Output file path")
    args = parser.parse_args()

    fetch_open_orca(total_records=args.count, output_file=args.out)
