"""
AJAX AI - OpenAI & Compatible Endpoints Provider
Supports OpenAI, Groq, DeepSeek, OpenRouter, Together AI, and local OpenAI-compatible APIs (vLLM, LM Studio, etc.).
"""

import json
import requests
from typing import List, Dict, Any, Optional
from ai.llm.base import BaseLLMProvider, LLMResponse, ToolCall
from core.logger import ajax_logger, error_logger

class OpenAICompatibleProvider(BaseLLMProvider):
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        provider_name: str = "openai"
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.provider_name = provider_name

    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> LLMResponse:
        url = f"{self.base_url}/chat/completions"
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
            resp = requests.post(url, headers=headers, json=payload, timeout=45)
            if resp.status_code != 200:
                error_logger.error(f"LLM API Error ({self.provider_name}): {resp.status_code} - {resp.text}")
                raise Exception(f"API Error {resp.status_code}: {resp.text}")
                
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
                provider=self.provider_name,
                tokens_used=tokens,
                raw_response=data
            )
        except Exception as e:
            error_logger.error(f"Error calling {self.provider_name} LLM: {str(e)}")
            raise e
