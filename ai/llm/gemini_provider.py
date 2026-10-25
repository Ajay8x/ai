"""
AJAX AI - Google Gemini LLM Provider
Enables high-speed reasoning via Google Gemini (Gemini 2.5, Gemini 2.0 Flash, Gemini 1.5 Flash).
Supports both native Google Generative Language REST API and OpenAI-compatible endpoint.
"""

import json
import requests
from typing import List, Dict, Any, Optional
from ai.llm.base import BaseLLMProvider, LLMResponse, ToolCall
from core.logger import ajax_logger, error_logger

class GeminiProvider(BaseLLMProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        use_openai_endpoint: bool = True
    ):
        self.api_key = api_key.strip()
        self.model = model or "gemini-1.5-flash"
        self.use_openai_endpoint = use_openai_endpoint
        self.openai_base_url = "https://generativelanguage.googleapis.com/v1beta/openai"

    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> LLMResponse:
        url = f"{self.openai_base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=35)
            if resp.status_code != 200:
                error_logger.error(f"Gemini API Error: {resp.status_code} - {resp.text}")
                raise Exception(f"Gemini API Error {resp.status_code}: {resp.text}")
                
            data = resp.json()
            choice = data["choices"][0]["message"]
            content = choice.get("content") or ""
            
            tool_calls = []
            if "tool_calls" in choice and choice["tool_calls"]:
                for tc in choice["tool_calls"]:
                    fn = tc["function"]
                    try:
                        args = json.loads(fn.get("arguments", "{}"))
                    except Exception:
                        args = {}
                    tool_calls.append(ToolCall(
                        id=tc.get("id", ""),
                        function_name=fn.get("name", ""),
                        arguments=args
                    ))
                    
            tokens = data.get("usage", {}).get("total_tokens", 0)
            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                model=self.model,
                provider="gemini",
                tokens_used=tokens,
                raw_response=data
            )
        except Exception as e:
            error_logger.error(f"Error calling Gemini LLM: {str(e)}")
            raise e

    def stream_generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """Yield real-time text chunks via Gemini streaming."""
        url = f"{self.openai_base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        resp = requests.post(url, headers=headers, json=payload, stream=True, timeout=35)
        for line in resp.iter_lines():
            if line:
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta and delta["content"]:
                            yield delta["content"]
                    except Exception:
                        pass
