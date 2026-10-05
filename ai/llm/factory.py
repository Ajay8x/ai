"""
AJAX AI - LLM Factory & Multi-Tier Fallback Manager
Selects and cascades across configured LLM providers with offline fallback support.
"""

from typing import Optional, List, Dict, Any
from ai.llm.base import BaseLLMProvider, LLMResponse, ToolCall
from ai.llm.openai_provider import OpenAICompatibleProvider
from ai.llm.ollama_provider import OllamaProvider
from config.config_loader import config
from core.logger import ajax_logger, error_logger

class LocalRuleBasedFallbackProvider(BaseLLMProvider):
    """Offline fallback intelligence when cloud LLMs and local Ollama are unreachable."""
    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> LLMResponse:
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = m.get("content", "").lower()
                break
                
        # Basic smart response
        if "hello" in user_msg or "namaste" in user_msg or "hi" in user_msg:
            resp = "Namaste! I am AJAX AI. How can I help you today?"
        elif "who are you" in user_msg or "kya ho" in user_msg:
            resp = "I am AJAX (Adaptive Intelligence & Autonomous eXecution), your personal AI assistant."
        elif "help" in user_msg:
            resp = "You can ask me to open apps, search the web, control system volume, check PC status, set timers, and manage files."
        else:
            resp = "I am running in offline mode. I can execute all PC and system commands, open apps, check battery/CPU, and manage files directly."
            
        return LLMResponse(
            content=resp,
            tool_calls=[],
            model="offline_fallback",
            provider="local_rule_engine",
            tokens_used=0
        )

def get_llm_provider() -> BaseLLMProvider:
    """Instantiate the primary configured LLM provider."""
    provider_name = config.llm.provider.lower()
    
    if provider_name == "groq" and config.llm.groq_api_key:
        return OpenAICompatibleProvider(
            api_key=config.llm.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            model=config.llm.model or "llama-3.3-70b-versatile",
            provider_name="groq"
        )
    elif provider_name == "deepseek" and config.llm.deepseek_api_key:
        return OpenAICompatibleProvider(
            api_key=config.llm.deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
            model=config.llm.model or "deepseek-chat",
            provider_name="deepseek"
        )
    elif provider_name == "openrouter" and config.llm.openrouter_api_key:
        return OpenAICompatibleProvider(
            api_key=config.llm.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            model=config.llm.model or "meta-llama/llama-3.3-70b-instruct",
            provider_name="openrouter"
        )
    elif provider_name == "ollama":
        return OllamaProvider(
            base_url=config.llm.ollama_base_url,
            model=config.llm.model or "llama3:latest"
        )
    elif config.llm.api_key:
        return OpenAICompatibleProvider(
            api_key=config.llm.api_key,
            base_url="https://api.openai.com/v1",
            model=config.llm.model or "gpt-4o-mini",
            provider_name="openai"
        )
    else:
        # Fallback to offline rule engine
        return LocalRuleBasedFallbackProvider()

class ResilientLLMBrain:
    """Wrapper that tries primary provider, then secondary, then local fallback."""
    def __init__(self):
        self.primary = get_llm_provider()
        self.fallback = LocalRuleBasedFallbackProvider()

    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> LLMResponse:
        try:
            return self.primary.generate(messages, tools=tools, temperature=temperature, max_tokens=max_tokens)
        except Exception as e:
            error_logger.warning(f"Primary LLM failed ({e}). Falling back to local offline engine.")
            return self.fallback.generate(messages, tools=tools, temperature=temperature, max_tokens=max_tokens)

llm_brain = ResilientLLMBrain()
