"""
AJAX AI - Local Hugging Face / Transformers LLM Provider
Loads and runs a locally downloaded causal language model using Hugging Face transformers.
"""

import os
import sys
from typing import List, Dict, Any, Optional
from ai.llm.base import BaseLLMProvider, LLMResponse, ToolCall
from core.logger import ajax_logger, error_logger

class LocalHuggingFaceProvider(BaseLLMProvider):
    """Executes inference directly on a local PyTorch/Transformers model."""

    def __init__(self, model_path: str, device: str = "auto", load_in_4bit: bool = False):
        self.model_path = os.path.abspath(model_path)
        self.device = device
        self.load_in_4bit = load_in_4bit
        self.tokenizer = None
        self.model = None
        self._is_loaded = False

    def _load_model(self):
        if self._is_loaded:
            return

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            ajax_logger.info(f"Loading local Transformers model from: {self.model_path}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )

            use_cuda = torch.cuda.is_available() and self.device != "cpu"
            kwargs = {
                "trust_remote_code": True,
                "torch_dtype": torch.float16 if use_cuda else torch.float32,
                "low_cpu_mem_usage": True,
            }
            if use_cuda:
                kwargs["device_map"] = "auto"
            if self.load_in_4bit:
                kwargs["load_in_4bit"] = True
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                **kwargs
            )
            if not use_cuda:
                self.model.to("cpu")
            self.model.eval()
            self._is_loaded = True
            ajax_logger.info("Local Transformers model loaded successfully.")
        except Exception as e:
            error_logger.warning(f"Local Transformers model loading deferred ({e}). Using AJAX Native Engine.")
            raise RuntimeError(f"Could not load local model from {self.model_path}: {e}")

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
            # Build chat template prompt if supported, else simple formatted chat
            if hasattr(self.tokenizer, "apply_chat_template"):
                prompt_text = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
            else:
                prompt_text = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages]) + "\nassistant:"

            import torch
            if not torch.cuda.is_available():
                torch.set_num_threads(os.cpu_count() or 8)
                
            input_device = next(self.model.parameters()).device
            model_inputs = self.tokenizer([prompt_text], return_tensors="pt").to(input_device)

            # Cap max_new_tokens to 256 for snappy interactive conversation
            effective_max_tokens = min(max_tokens, 256) if max_tokens > 256 else max_tokens

            gen_kwargs = {
                "max_new_tokens": effective_max_tokens,
                "temperature": max(temperature, 0.1),
                "top_p": 0.9,
                "do_sample": temperature > 0.0,
                "pad_token_id": self.tokenizer.eos_token_id,
                "eos_token_id": self.tokenizer.eos_token_id
            }

            with torch.no_grad():
                generated_ids = self.model.generate(
                    **model_inputs,
                    **gen_kwargs
                )

            # Strip input tokens from output
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]

            response_text = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

            return LLMResponse(
                content=response_text,
                tool_calls=[],
                model=os.path.basename(self.model_path) or "ajax-local-transformer",
                provider="ajax_local_llm",
                tokens_used=len(generated_ids[0])
            )
        except Exception as e:
            error_logger.error(f"Inference error in LocalHuggingFaceProvider: {e}")
            raise e
