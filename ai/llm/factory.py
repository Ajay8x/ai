"""
AJAX AI - LLM Factory & Multi-Tier Fallback Manager
Selects and cascades across configured LLM providers with offline fallback support.
"""

import os
from typing import Optional, List, Dict, Any
from ai.llm.base import BaseLLMProvider, LLMResponse, ToolCall
from ai.llm.openai_provider import OpenAICompatibleProvider
from ai.llm.ollama_provider import OllamaProvider
from config.config_loader import config
from core.logger import ajax_logger, error_logger

class LocalRuleBasedFallbackProvider(BaseLLMProvider):
    """Offline fallback intelligence when cloud LLMs and local engines are unreachable."""
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
                user_msg = m.get("content", "").strip()
                break
                
        user_lower = user_msg.lower()

        # 1. Math calculation fallback
        from tools.calculator_tool import CalculatorTool
        calc = CalculatorTool()
        calc_res = calc.execute(expression=user_msg)
        if calc_res.success:
            return LLMResponse(
                content=str(calc_res.output),
                tool_calls=[],
                model="local_math_engine",
                provider="local_rule_engine",
                tokens_used=1
            )

        import re

        # 2. Conversational greetings (strict word boundaries)
        if any(re.search(r'\b' + re.escape(w) + r'\b', user_lower) for w in ["good morning", "shubh prabhat"]):
            resp = "Good morning! Hope you have a productive day ahead. How can I assist you today?"
        elif any(re.search(r'\b' + re.escape(w) + r'\b', user_lower) for w in ["good afternoon", "good evening", "shubh sandhya"]):
            resp = "Good evening! How can I assist you today?"
        elif any(re.search(r'\b' + re.escape(w) + r'\b', user_lower) for w in ["who are you", "kya ho", "your name", "who created you"]):
            resp = "I am AJAX (Adaptive Intelligence & Autonomous eXecution), your autonomous personal AI assistant created by Ajay Singh."
        elif any(re.search(r'\b' + re.escape(w) + r'\b', user_lower) for w in ["hello", "namaste", "hi", "hey"]):
            resp = "Namaste! I am AJAX AI. How can I help you today?"
        elif any(re.search(r'\b' + re.escape(w) + r'\b', user_lower) for w in ["how are you", "kaise ho"]):
            resp = "I am running smoothly with optimal performance and sub-second response speed! How can I assist you?"
        elif any(re.search(r'\b' + re.escape(w) + r'\b', user_lower) for w in ["help", "madad", "kya kar sakte ho", "what can you do"]):
            resp = "I can control your PC (open/close apps, volume, battery, screenshots), solve math, search Wikipedia and web, set timers/alarms, query local knowledge, and remember your preferences."
        else:
            resp = ""
            # 3. Check RAG vector store for indexed knowledge
            try:
                from ai.rag.store import rag_store
                rag_results = rag_store.query(user_msg, top_k=2)
                if rag_results:
                    chunks = [d.get("chunk", "") for d in rag_results]
                    joined = "\n\n".join(chunks)
                    resp = f"{joined[:600]}..." if len(joined) > 600 else joined
            except Exception:
                pass

            if not resp:
                clean_query = re.sub(r'^(what is|who is|explain|tell me about|how does|what are|kya hai|kya hota hai|batao|search for)\s+', '', user_lower).strip()
                target_search = clean_query or user_msg

                # 4. Try Wikipedia
                try:
                    from tools.web_tools import WikipediaTool
                    wiki_res = WikipediaTool().execute(query=target_search, sentences=3)
                    if wiki_res.success and wiki_res.output:
                        resp = str(wiki_res.output)
                except Exception:
                    pass

            # 5. Try live DuckDuckGo web search
            if not resp:
                try:
                    from duckduckgo_search import DDGS
                    with DDGS() as ddgs:
                        results = list(ddgs.text(user_msg, max_results=2))
                        if results:
                            snippets = [r.get("body", "").strip() for r in results if r.get("body")]
                            if snippets:
                                resp = "\n\n".join(snippets[:2])
                except Exception:
                    pass

            if not resp:
                resp = f"I am ready to assist with '{user_msg}'. You can ask me to open apps, run calculations, control system volume, check battery/CPU, search Wikipedia, and manage files."
            
        return LLMResponse(
            content=resp,
            tool_calls=[],
            model="offline_rag_engine",
            provider="local_rule_engine",
            tokens_used=len(resp.split())
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
    elif provider_name in ["qwen3.5-9b", "qwen3.5", "qwen9b", "qwen-9b", "qwen", "local_hf", "transformers"]:
        base_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_path = config.llm.local_model_path or os.path.join(base_root, "models", "qwen3.5-9b")
        if not os.path.isabs(model_path):
            model_path = os.path.join(base_root, model_path)
        from ai.llm.local_hf_provider import LocalHuggingFaceProvider
        return LocalHuggingFaceProvider(
            model_path=model_path,
            device="auto"
        )
    elif provider_name in ["llamafile", "qwen3-4b", "qwen3", "thinking"]:
        from ai.llm.llamafile_provider import LlamafileProvider
        model_path = config.llm.local_model_path or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "qwen3-4b-thinking-2507.Q4_K_M.gguf")
        return LlamafileProvider(model_path=model_path)
    elif provider_name in ["gguf", "llama_cpp"]:
        from ai.llm.gguf_provider import GGUFProvider
        model_path = config.llm.local_model_path or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "qwen3-4b-thinking-2507.Q4_K_M.gguf")
        return GGUFProvider(model_path=model_path)
    elif provider_name in ["local"]:
        base_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_path = config.llm.local_model_path or os.path.join(base_root, "models", "qwen3.5-9b")
        if not os.path.isabs(model_path):
            model_path = os.path.join(base_root, model_path)
        if os.path.exists(model_path):
            from ai.llm.local_hf_provider import LocalHuggingFaceProvider
            return LocalHuggingFaceProvider(model_path=model_path, device="auto")
        
        gguf_candidate = os.path.join(base_root, "qwen3-4b-thinking-2507.Q4_K_M.gguf")
        if os.path.exists(gguf_candidate):
            from ai.llm.llamafile_provider import LlamafileProvider
            return LlamafileProvider(model_path=gguf_candidate)
    elif config.llm.api_key:
        return OpenAICompatibleProvider(
            api_key=config.llm.api_key,
            base_url="https://api.openai.com/v1",
            model=config.llm.model or "gpt-4o-mini",
            provider_name="openai"
        )
    else:
        # Check if local GGUF model and llamafile exist before falling back to rule engine
        base_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        gguf_path = os.path.join(base_root, "qwen3-4b-thinking-2507.Q4_K_M.gguf")
        if os.path.exists(gguf_path):
            from ai.llm.llamafile_provider import LlamafileProvider
            return LlamafileProvider(model_path=gguf_path)
        
        # Fallback to offline rule engine
        return LocalRuleBasedFallbackProvider()

class ResilientLLMBrain:
    """Wrapper that tries primary provider, then secondary, then local fallback."""
    def __init__(self):
        self.primary = get_llm_provider()
        self.fallback = LocalRuleBasedFallbackProvider()
        self._primary_disabled = False

    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> LLMResponse:
        if not self._primary_disabled:
            try:
                return self.primary.generate(messages, tools=tools, temperature=temperature, max_tokens=max_tokens)
            except Exception as e:
                error_logger.warning(f"Primary LLM unavailable ({e}). Switching to high-speed local engine.")
                self._primary_disabled = True

        return self.fallback.generate(messages, tools=tools, temperature=temperature, max_tokens=max_tokens)

llm_brain = ResilientLLMBrain()
