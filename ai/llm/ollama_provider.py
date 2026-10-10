"""
AJAX AI - Ollama Local Provider
Enables offline and local execution via Ollama API with tool calling support.
"""

import json
import requests
from typing import List, Dict, Any, Optional
from ai.llm.base import BaseLLMProvider, LLMResponse, ToolCall
from core.logger import ajax_logger, error_logger

from config.config_loader import config

class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
        self.base_url = base_url.rstrip("/")
        self.model = model or "llama3.2:3b"
        self._verify_or_select_model()

    def _verify_or_select_model(self):
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if r.status_code == 200:
                available = [m.get("name") for m in r.json().get("models", [])]
                if self.model not in available and available:
                    # Pick best match or first available
                    if "llama3.2:3b" in available:
                        self.model = "llama3.2:3b"
                    elif "gemma4:latest" in available:
                        self.model = "gemma4:latest"
                    elif "gemma3:4b" in available:
                        self.model = "gemma3:4b"
                    else:
                        self.model = available[0]
                    ajax_logger.info(f"Ollama auto-selected model: {self.model}")
        except Exception:
            pass

    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> LLMResponse:
        url = f"{self.base_url}/api/chat"
        num_ctx = int(getattr(config.llm, "ollama_num_ctx", 4096))
        num_thread = int(getattr(config.llm, "cpu_threads", 12))

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": num_ctx,
                "num_thread": num_thread
            }
        }
        
        if tools:
            payload["tools"] = tools

        try:
            resp = requests.post(url, json=payload, timeout=60)
            if resp.status_code != 200:
                raise Exception(f"Ollama Error {resp.status_code}: {resp.text}")
                
            data = resp.json()
            msg = data.get("message", {})
            content = msg.get("content", "")
            
            tool_calls = []
            if "tool_calls" in msg and msg["tool_calls"]:
                for tc in msg["tool_calls"]:
                    fn = tc.get("function", {})
                    fn_name = fn.get("name", "")
                    fn_args = fn.get("arguments", {})
                    if isinstance(fn_args, str):
                        try:
                            fn_args = json.loads(fn_args)
                        except Exception:
                            fn_args = {}
                    if isinstance(fn_args, list):
                        if fn_args and isinstance(fn_args[0], dict):
                            fn_args = fn_args[0]
                        else:
                            fn_args = {}
                    if not isinstance(fn_args, dict):
                        fn_args = {}
                        
                    tool_calls.append(ToolCall(
                        id=tc.get("id", f"call_{len(tool_calls)}"),
                        function_name=fn_name,
                        arguments=fn_args
                    ))

            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                model=self.model,
                provider="ollama",
                tokens_used=data.get("eval_count", 0),
                raw_response=data
            )
        except Exception as e:
            error_logger.error(f"Error calling Ollama: {str(e)}")
            raise e

