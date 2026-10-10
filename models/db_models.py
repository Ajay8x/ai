"""
AJAX AI - MVC Model: Database Entities & Data Models
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class ConversationModel:
    id: str
    title: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_archived: int = 0
    is_pinned: int = 0

@dataclass
class MessageModel:
    id: str
    conversation_id: str
    role: str
    content: str
    modality: str = "text"
    tokens: int = 0
    created_at: Optional[str] = None

@dataclass
class MemoryModel:
    id: str
    category: str
    key_text: str
    value_text: str
    source: str = "chat"
    confidence: float = 1.0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class ToolExecutionModel:
    id: str
    tool_name: str
    parameters_json: str
    result_json: str
    status: str
    duration_ms: float = 0.0
    created_at: Optional[str] = None
