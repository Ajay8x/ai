"""
AJAX AI - Public API Connectors: Base Models & Specifications
Enterprise-grade abstractions for public API integration, loop detection, and schema validation.
"""

import time
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Union

class DataClassification(str, Enum):
    LIVE = "live"
    PERIODIC = "periodic"
    HISTORICAL = "historical"
    STATIC_REFERENCE = "static_reference"
    SAMPLE = "sample"
    CALCULATED = "calculated"

class AuthType(str, Enum):
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC = "basic"
    CUSTOM_HEADER = "custom_header"
    OAUTH2 = "oauth2"

class CORSStatus(str, Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"

class CircuitBreakerState(str, Enum):
    CLOSED = "CLOSED"       # Normal operation
    OPEN = "OPEN"           # Tripped, blocking requests
    HALF_OPEN = "HALF_OPEN" # Probing service recovery

class FieldType(str, Enum):
    TEXT = "Text"
    TEXTAREA = "Textarea"
    NUMBER = "Number"
    BOOLEAN = "Boolean"
    DATE = "Date"
    DATETIME = "DateTime"
    EMAIL = "Email"
    URL = "URL"
    SELECT = "Select"
    MULTI_SELECT = "Multi-select"
    ARRAY = "Array"
    OBJECT = "Object"
    GEO_POINT = "GeoPoint"
    IMAGE_URL = "Image URL"

@dataclass
class APIProviderConfig:
    id: str
    name: str
    category: str
    official_docs_url: str
    base_url: str
    auth_type: AuthType = AuthType.NONE
    required_credentials: List[str] = field(default_factory=list)
    rate_limit_rpm: int = 60
    quota_daily: Optional[int] = None
    commercial_use: str = "unknown" # "permitted", "non_commercial_only", "unknown"
    license_url: str = ""
    attribution: str = ""
    cors_status: CORSStatus = CORSStatus.UNKNOWN
    backend_proxy_required: bool = True
    default_timeout: int = 10
    retry_max: int = 3
    cache_ttl_sec: int = 300
    data_classification: DataClassification = DataClassification.LIVE
    enabled: bool = True
    headers: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["auth_type"] = self.auth_type.value
        d["cors_status"] = self.cors_status.value
        d["data_classification"] = self.data_classification.value
        return d

@dataclass
class SchemaField:
    key: str
    label: str
    field_type: FieldType
    json_path: str
    required: bool = False
    description: str = ""
    default_value: Any = None
    options: List[str] = field(default_factory=list)
    sample_value: Any = None
    constraints: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["field_type"] = self.field_type.value
        return d

@dataclass
class ConnectorRequest:
    provider_id: str
    endpoint: str
    method: str = "GET"
    params: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None
    correlation_id: str = ""
    calling_workflow: str = "direct_client"
    depth: int = 0
    timeout: Optional[int] = None
    skip_cache: bool = False

@dataclass
class ConnectorResponse:
    success: bool
    status_code: int
    data: Any
    headers: Dict[str, str] = field(default_factory=dict)
    latency_ms: float = 0.0
    from_cache: bool = False
    etag: Optional[str] = None
    data_classification: DataClassification = DataClassification.LIVE
    attribution: str = ""
    source_url: str = ""
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "status_code": self.status_code,
            "data": self.data,
            "latency_ms": self.latency_ms,
            "from_cache": self.from_cache,
            "data_classification": self.data_classification.value,
            "attribution": self.attribution,
            "source_url": self.source_url,
            "error": self.error,
            "timestamp": self.timestamp
        }
