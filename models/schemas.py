"""
AJAX AI - MVC Model: Request/Response Schemas & Data Transfer Objects
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    query: str = Field(..., description="User query or instruction")
    conversation_id: Optional[str] = Field(None, description="Active conversation session ID")
    modality: Optional[str] = Field("api", description="Interaction modality: api, text, voice")
    web_search: Optional[bool] = Field(False, description="Whether to force live web search")
    language: Optional[str] = Field("en", description="Preferred response language: 'en' or 'hi'")

class ChatResponse(BaseModel):
    response: str
    intent: str
    confidence: float
    tool_called: Optional[Any] = None
    tool_result: Optional[Any] = None
    needs_confirmation: Optional[bool] = False

class UploadRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255, description="Name of the file being uploaded")
    # 15 MB default binary limit plus base64 overhead. The controller applies
    # the final environment-specific MAX_UPLOAD_SIZE_MB check after decoding.
    content_base64: str = Field(..., max_length=21_000_000, description="Base64 encoded file payload")

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
