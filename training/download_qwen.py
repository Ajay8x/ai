"""
AJAX AI - Hugging Face Qwen Downloader & Local LLM Setup
Downloads Qwen3.5-9B (or other Qwen models) from Hugging Face and prepares it for local inference.
"""

import sys
import os
import argparse
import shutil

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

DEFAULT_MODEL_ID = "Qwen/Qwen3.5-9B"

def check_disk_space(target_dir: str, required_gb: float = 20.0):
    try:
        total, used, free = shutil.disk_usage(target_dir)
        free_gb = free / (1024 ** 3)
        print(f"[*] Available Disk Space: {free_gb:.2f} GB (Required: ~{required_gb:.1f} GB)")
        if free_gb < required_gb:
            print(f"[!] Warning: Free space ({free_gb:.2f} GB) might be low for full 9B weights.")
        return free_gb
    except Exception as e:
        print(f"[*] Could not verify disk space: {e}")
        return None

def download_qwen_model(
    repo_id: str = DEFAULT_MODEL_ID,
    destination_folder: str = None,
    hf_token: str = None,
    allow_patterns: list = None,
    ignore_patterns: list = None
):
    print("\n" + "="*65)
    print("  [AJAX AI] HUGGING FACE MODEL DOWNLOADER")
    print(f"  Target Model : {repo_id}")
    print("="*65)

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("[!] 'huggingface_hub' is not installed. Installing now...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub"])
        from huggingface_hub import snapshot_download

    safe_model_name = repo_id.split("/")[-1].lower()
    if not destination_folder:
        destination_folder = os.path.join(MODELS_DIR, safe_model_name)
    
    os.makedirs(destination_folder, exist_ok=True)
    print(f"[*] Destination Directory : {destination_folder}")
    check_disk_space(destination_folder, required_gb=18.0)

    token = hf_token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")

    print(f"[*] Starting download from Hugging Face for '{repo_id}'...")
    print("[*] Please wait, this may take some time depending on your network speed...\n")

    try:
        local_dir = snapshot_download(
            repo_id=repo_id,
            local_dir=destination_folder,
            local_dir_use_symlinks=False,
            token=token,
            allow_patterns=allow_patterns,
            ignore_patterns=ignore_patterns,
            resume_download=True
        )
        print("\n" + "="*65)
        print(f"  [SUCCESS] Model downloaded successfully to:")
        print(f"  {local_dir}")
        print("="*65)
        print("\nTo use this model in AJAX AI:")
        print(f"1. Set in your .env file:")
        print(f"   DEFAULT_LLM_PROVIDER=local_hf")
        print(f"   LOCAL_MODEL_PATH={local_dir}")
        print(f"2. Or run AJAX AI main application: python main.py\n")
        return local_dir
    except Exception as e:
        print(f"\n[!] Error downloading model: {e}")
        print("[*] Troubleshooting tips:")
        print("    - Check your internet connection")
        print("    - If the model is gated, provide your HF Token via --token or HF_TOKEN env var")
        print("    - Ensure adequate disk space is available")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Qwen3.5-9B or any Hugging Face model for AJAX AI.")
    parser.add_argument("--repo_id", type=str, default=DEFAULT_MODEL_ID, help=f"Hugging Face Model ID (default: {DEFAULT_MODEL_ID})")
    parser.add_argument("--dest", type=str, default=None, help="Custom target directory")
    parser.add_argument("--token", type=str, default=None, help="Hugging Face API Access Token (if needed)")
    args = parser.parse_args()

    download_qwen_model(
        repo_id=args.repo_id,
        destination_folder=args.dest,
        hf_token=args.token
    )
