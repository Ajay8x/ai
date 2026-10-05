"""
AJAX AI - Ollama Local Provider
Enables offline and local execution via Ollama API.
"""

import json
import requests
from typing import List, Dict, Any, Optional
from ai.llm.base import BaseLLMProvider, LLMResponse, ToolCall
from core.logger import ajax_logger, error_logger

class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3:latest"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> LLMResponse:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            resp = requests.post(url, json=payload, timeout=60)
            if resp.status_code != 200:
                raise Exception(f"Ollama Error {resp.status_code}: {resp.text}")
                
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            return LLMResponse(
                content=content,
                tool_calls=[],
                model=self.model,
                provider="ollama",
                tokens_used=data.get("eval_count", 0),
                raw_response=data
            )
        except Exception as e:
            error_logger.error(f"Error calling Ollama: {str(e)}")
            raise e
