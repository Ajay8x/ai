"""
AJAX AI - LLM Base Interface
Standardized interface for all language model providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator
from dataclasses import dataclass, field

@dataclass
class ToolCall:
    id: str
    function_name: str
    arguments: Dict[str, Any]

@dataclass
class LLMResponse:
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    tokens_used: int = 0
    raw_response: Optional[Any] = None

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> LLMResponse:
        """Generate response from LLM."""
        pass
