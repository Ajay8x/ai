"""
AJAX AI - MVC Model: Request/Response Schemas & Data Transfer Objects
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    query: str = Field(..., description="User query or instruction")
    conversation_id: Optional[str] = Field(None, description="Active conversation session ID")
    modality: Optional[str] = Field("api", description="Interaction modality: api, text, voice")

class ChatResponse(BaseModel):
    response: str
    intent: str
    confidence: float
    tool_called: Optional[Any] = None
    tool_result: Optional[Any] = None
    needs_confirmation: Optional[bool] = False

class UploadRequest(BaseModel):
    filename: str = Field(..., description="Name of the file being uploaded")
    content_base64: str = Field(..., description="Base64 encoded file payload")

class UploadResponse(BaseModel):
    success: bool
    filename: str
    chunks: int
    message: str

class MemoryRequest(BaseModel):
    key: str
    value: str
    category: Optional[str] = "general"

class ToolExecRequest(BaseModel):
    tool_name: str
    parameters: Optional[Dict[str, Any]] = None
    confirmed: Optional[bool] = False
