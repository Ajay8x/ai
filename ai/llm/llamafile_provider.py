"""
AJAX AI - Local Llamafile LLM Provider
Runs quantized GGUF models (e.g. Qwen3-4B Thinking) using Mozilla's high-performance llamafile engine.
Zero external Python dependencies, native Windows GPU/CPU acceleration, and OpenAI-compatible API.
"""

import os
import sys
import time
import json
import re
import subprocess
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional
from ai.llm.base import BaseLLMProvider, LLMResponse, ToolCall
from core.logger import ajax_logger, error_logger

class LlamafileProvider(BaseLLMProvider):
    """Manages local llamafile server lifecycle and inference for GGUF models."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        llamafile_path: Optional[str] = None,
        host: str = "127.0.0.1",
        port: int = 8080,
        gpu_layers: int = 99,
        ctx_size: int = 4096,
        auto_start: bool = True
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Resolve model path (default to local Qwen 4B Thinking GGUF)
        if not model_path:
            default_model = os.path.join(base_dir, "qwen3-4b-thinking-2507.Q4_K_M.gguf")
            self.model_path = default_model if os.path.exists(default_model) else ""
        else:
            self.model_path = model_path if os.path.isabs(model_path) else os.path.join(base_dir, model_path)

        # Resolve llamafile executable path
        if not llamafile_path:
            default_exe = os.path.join(base_dir, "llamafile-0.10.5.exe")
            if not os.path.exists(default_exe):
                # Search for any llamafile in root
                for f in os.listdir(base_dir):
                    if f.startswith("llamafile") and f.endswith(".exe"):
                        default_exe = os.path.join(base_dir, f)
                        break
            self.llamafile_path = default_exe
        else:
            self.llamafile_path = llamafile_path if os.path.isabs(llamafile_path) else os.path.join(base_dir, llamafile_path)

        self.host = host
        self.port = port
        self.gpu_layers = gpu_layers
        self.ctx_size = ctx_size
        self.auto_start = auto_start
        self.base_url = f"http://{self.host}:{self.port}/v1"
        self._process: Optional[subprocess.Popen] = None

    def is_server_running(self) -> bool:
        """Check if the local llamafile server is responsive."""
        try:
            req = urllib.request.Request(f"http://{self.host}:{self.port}/health", headers={"User-Agent": "AJAX-AI"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            pass

        try:
            req = urllib.request.Request(f"{self.base_url}/models", headers={"User-Agent": "AJAX-AI"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def start_server(self):
        """Spawn the llamafile background server process if not running."""
        if self.is_server_running():
            ajax_logger.info(f"Llamafile server is already active at http://{self.host}:{self.port}")
            return

        if not os.path.exists(self.llamafile_path):
            raise FileNotFoundError(f"Llamafile executable not found: {self.llamafile_path}")

        if not self.model_path or not os.path.exists(self.model_path):
            raise FileNotFoundError(f"GGUF model file not found: {self.model_path}")

        cmd = [
            self.llamafile_path,
            "-m", self.model_path,
            "--host", self.host,
            "--port", str(self.port),
            "-c", str(self.ctx_size),
            "-ngl", str(self.gpu_layers),
            "--nobrowser"
        ]

        ajax_logger.info(f"Starting Llamafile server: {' '.join(cmd)}")
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )

        # Wait up to 20 seconds for initialization
        for _ in range(40):
            time.sleep(0.5)
            if self.is_server_running():
                ajax_logger.info(f"Llamafile server successfully started at http://{self.host}:{self.port}")
                return

        raise TimeoutError("Timed out waiting for Llamafile server to initialize.")

    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> LLMResponse:
        if self.auto_start and not self.is_server_running():
            self.start_server()

        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": os.path.basename(self.model_path) if self.model_path else "qwen3-4b-thinking",
            "messages": messages,
            "temperature": max(temperature, 0.01),
            "max_tokens": max_tokens,
            "stream": False
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer not-needed"
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))

            choice = result.get("choices", [{}])[0]
            msg = choice.get("message", {})
            raw_content = msg.get("content", "") or ""

            # Extract reasoning/thinking thoughts from Qwen Thinking model
            cleaned_content = raw_content
            think_match = re.search(r"<think>(.*?)</think>", raw_content, flags=re.DOTALL)
            if think_match:
                thought = think_match.group(1).strip()
                cleaned_content = re.sub(r"<think>.*?</think>", "", raw_content, flags=re.DOTALL).strip()
                if thought:
                    ajax_logger.info(f"[Qwen Thinking Output]: {thought[:160]}...")

            tokens_used = result.get("usage", {}).get("total_tokens", len(raw_content.split()))

            return LLMResponse(
                content=cleaned_content or raw_content,
                tool_calls=[],
                model=os.path.basename(self.model_path) if self.model_path else "qwen3-4b-thinking",
                provider="llamafile_qwen_local",
                tokens_used=tokens_used
            )
        except Exception as e:
            error_logger.error(f"Llamafile local inference error: {e}")
            raise e
