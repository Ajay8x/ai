"""
AJAX AI - Local GGUF LLM Provider
Direct high-performance inference for quantized .gguf models (e.g., Qwen3-4B Thinking).
Supports CPU and GPU acceleration with automated prompt formatting and reasoning/thinking tag parsing.
"""

import os
import re
from typing import List, Dict, Any, Optional
from ai.llm.base import BaseLLMProvider, LLMResponse, ToolCall
from core.logger import ajax_logger, error_logger

class GGUFProvider(BaseLLMProvider):
    """Executes high-speed local inference directly on GGUF quantized models."""

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,
        n_threads: Optional[int] = None,
        verbose: bool = False
    ):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.n_threads = n_threads or os.cpu_count() or 4
        self.verbose = verbose
        self.llm = None
        self._is_loaded = False

    def _load_model(self):
        if self._is_loaded:
            return

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"GGUF model file not found at: {self.model_path}")

        try:
            from llama_cpp import Llama
            
            ajax_logger.info(f"Loading GGUF Model from {self.model_path} (n_ctx={self.n_ctx}, threads={self.n_threads})")
            
            # Attempt to load with GPU layers first, fallback to CPU if GPU initialization fails
            try:
                self.llm = Llama(
                    model_path=self.model_path,
                    n_ctx=self.n_ctx,
                    n_gpu_layers=self.n_gpu_layers,
                    n_threads=self.n_threads,
                    verbose=self.verbose
                )
            except Exception as gpu_err:
                ajax_logger.warning(f"GPU offloading failed ({gpu_err}), falling back to CPU mode...")
                self.llm = Llama(
                    model_path=self.model_path,
                    n_ctx=self.n_ctx,
                    n_gpu_layers=0,
                    n_threads=self.n_threads,
                    verbose=self.verbose
                )

            self._is_loaded = True
            ajax_logger.info("GGUF Model loaded successfully into memory.")
        except ImportError:
            error_msg = (
                "llama-cpp-python is required to run GGUF models. "
                "Install it using: pip install llama-cpp-python"
            )
            error_logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_logger.error(f"Failed to load GGUF model: {e}")
            raise e

    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> LLMResponse:
        self._load_model()

        try:
            # Format chat completion using llama-cpp's built-in chat handler
            formatted_messages = []
            for m in messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                formatted_messages.append({"role": role, "content": content})

            response = self.llm.create_chat_completion(
                messages=formatted_messages,
                temperature=max(temperature, 0.01),
                max_tokens=max_tokens,
                top_p=0.9,
                stop=["<|im_end|>", "<|endoftext|>"]
            )

            choice = response["choices"][0]
            raw_content = choice["message"].get("content", "")

            # Handle reasoning/thinking tokens (e.g., <think>...</think> in Qwen Thinking models)
            cleaned_content = raw_content
            thinking_content = None
            
            think_match = re.search(r"<think>(.*?)</think>", raw_content, flags=re.DOTALL)
            if think_match:
                thinking_content = think_match.group(1).strip()
                cleaned_content = re.sub(r"<think>.*?</think>", "", raw_content, flags=re.DOTALL).strip()
                if thinking_content:
                    ajax_logger.info(f"[Qwen Thinking]: {thinking_content[:150]}...")

            tokens_used = response.get("usage", {}).get("total_tokens", len(raw_content.split()))

            return LLMResponse(
                content=cleaned_content or raw_content,
                tool_calls=[],
                model=os.path.basename(self.model_path),
                provider="gguf_local",
                tokens_used=tokens_used
            )
        except Exception as e:
            error_logger.error(f"Inference error in GGUFProvider: {e}")
            raise e
