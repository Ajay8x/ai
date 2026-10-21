"""
AJAX AI - MVC Controller: Public API Connectors, Schema Mapper & Loop Detection
REST endpoints for provider execution, dynamic schema generation, graph cycle checking, and health dashboard.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from connectors.registry import connector_registry
from connectors.base import ConnectorRequest, FieldType, SchemaField
from connectors.proxy import secure_proxy, SSRFProtectionException
from connectors.loop_detector import loop_manager, LoopDetectionException, CircuitBreakerOpenException
from connectors.rate_limiter import rate_limiter, RateLimitExceededException
from connectors.schema_mapper import schema_mapper
from connectors.health import health_monitor
from connectors.providers import dispatcher
from core.logger import ajax_logger, security_logger

connectors_router = APIRouter(prefix="/api/connectors", tags=["Public API Connectors & Loop Subsystem"])

# --- Request / Response DTOs ---

class QueryConnectorRequest(BaseModel):
    action: Optional[str] = Field("default", description="Provider capability action")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Typed query parameters")

class ExecuteConnectorRequest(BaseModel):
    provider_id: str = Field(..., description="Registered provider ID")
    endpoint: str = Field("", description="Sub-endpoint path")
    method: str = Field("GET", description="HTTP Method")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="URL query parameters")
    headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="Custom headers")
    body: Optional[Any] = Field(None, description="Request JSON body")
    calling_workflow: Optional[str] = Field("api_dashboard", description="Originating workflow or user context")
    skip_cache: Optional[bool] = Field(False, description="Whether to bypass ETag / TTL cache")

class InferSchemaRequest(BaseModel):
    json_payload: Optional[Any] = Field(None, description="Sample JSON response payload")
    sample_json: Optional[Any] = Field(None, description="Sample JSON response payload alias")
    data_path: Optional[str] = Field("", description="Optional root JSONPath (e.g. $.items or $.features)")

class WorkflowValidationRequest(BaseModel):
    workflow_id: Optional[str] = Field("workflow", description="Workflow identifier")
    dependencies: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Directed edges")
    edges: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Edges alias")

# --- Endpoints ---

@connectors_router.get("/providers")
async def list_providers(category: Optional[str] = Query(None, description="Filter by category")):
    """Returns catalog of all registered API providers with official documentation, quotas, and licensing."""
    providers = connector_registry.list_all(category)
    return {
        "count": len(providers),
        "categories": connector_registry.list_categories(),
        "providers": [p.to_dict() for p in providers]
    }

@connectors_router.get("/providers/{provider_id}")
async def get_provider(provider_id: str):
    """Retrieves metadata and current circuit breaker state for a specific provider."""
    p = connector_registry.get(provider_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found.")
    cb = loop_manager.get_circuit_breaker(provider_id)
    d = p.to_dict()
    d["circuit_breaker_state"] = cb.state.value
    d["consecutive_failures"] = cb.consecutive_failures
    d["daily_usage_today"] = rate_limiter.quota_tracker.get_daily_usage(provider_id)
    return d

@connectors_router.post("/execute")
async def execute_connector(req: ExecuteConnectorRequest):
    """Safely executes an outbound request via the SSRF-protected proxy with loop detection."""
    provider = connector_registry.get(req.provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{req.provider_id}' not found in registry.")

    if not provider.enabled:
        raise HTTPException(status_code=400, detail=f"Provider '{req.provider_id}' is currently disabled.")

    c_req = ConnectorRequest(
        provider_id=req.provider_id,
        endpoint=req.endpoint,
        method=req.method,
        params=req.params or {},
        headers=req.headers or {},
        body=req.body,
        calling_workflow=req.calling_workflow or "direct_client",
        skip_cache=bool(req.skip_cache)
    )

    try:
        resp = secure_proxy.execute_request(c_req, provider)
        return resp.to_dict()
    except SSRFProtectionException as e:
        security_logger.error(f"SSRF violation blocked: {e}")
        raise HTTPException(status_code=403, detail=f"SSRF Protection: {e}")
    except LoopDetectionException as e:
        security_logger.error(f"Loop detection tripped: {e}")
        raise HTTPException(status_code=429, detail=f"Loop Detected: {e}")
    except RateLimitExceededException as e:
        raise HTTPException(status_code=429, detail=str(e), headers={"Retry-After": str(int(e.retry_after_seconds))})
    except CircuitBreakerOpenException as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        ajax_logger.error(f"Connector execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Connector error: {e}")

@connectors_router.post("/{provider_id}/query")
async def query_provider_capability(provider_id: str, req: QueryConnectorRequest):
    """Executes a high-level capability query for a specific provider with input validation and normalized response."""
    provider = connector_registry.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found.")
    if not provider.enabled:
        raise HTTPException(status_code=400, detail=f"Provider '{provider_id}' is currently disabled.")

    try:
        resp = dispatcher.dispatch(provider_id, req.action or "default", req.params or {})
        return resp.to_dict()
    except SSRFProtectionException as e:
        security_logger.error(f"SSRF violation blocked: {e}")
        raise HTTPException(status_code=403, detail=f"SSRF Protection: {e}")
    except LoopDetectionException as e:
        security_logger.error(f"Loop detection tripped: {e}")
        raise HTTPException(status_code=429, detail=f"Loop Detected: {e}")
    except RateLimitExceededException as e:
        raise HTTPException(status_code=429, detail=str(e), headers={"Retry-After": str(int(e.retry_after_seconds))})
    except CircuitBreakerOpenException as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        ajax_logger.error(f"Provider '{provider_id}' query error: {e}")
        raise HTTPException(status_code=500, detail=f"Connector error: {e}")

@connectors_router.post("/schema/infer")
async def infer_json_schema(req: InferSchemaRequest):
    """Automatically parses arbitrary JSON into a structured form schema with 14 supported types."""
    payload = req.json_payload if req.json_payload is not None else req.sample_json
    if payload is None:
        raise HTTPException(status_code=400, detail="Missing json_payload or sample_json")

    try:
        fields = schema_mapper.infer_schema(payload, data_path=req.data_path or "")
        preview = schema_mapper.generate_form_preview(fields, payload)
        return {
            "schema_version": "v1.0.0",
            "field_count": len(fields),
            "fields": [f.to_dict() for f in fields],
            "form_preview": preview
        }
    except LoopDetectionException as e:
        raise HTTPException(status_code=400, detail=f"Schema generation blocked by guard: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to infer schema: {e}")

@connectors_router.post("/workflows/validate")
@connectors_router.post("/loop/validate-workflow")
async def validate_workflow_graph(req: WorkflowValidationRequest):
    """Verifies workflow dependency DAG using DFS to ensure zero direct or multi-step circular cycles."""
    from connectors.loop_detector import WorkflowCycleDetector
    detector = WorkflowCycleDetector()
    all_edges = (req.dependencies or []) + (req.edges or [])
    for edge in all_edges:
        src = edge.get("source") or edge.get("from") or edge.get("from_step")
        tgt = edge.get("target") or edge.get("to") or edge.get("to_step")
        if src and tgt:
            detector.register_dependency(src, tgt)

    cycle_path = detector.find_cycle()
    if cycle_path:
        path_str = " ➔ ".join(cycle_path)
        return {
            "valid": False,
            "is_valid_dag": False,
            "has_cycle": True,
            "detected_cycles": [cycle_path],
            "cycle_path": cycle_path,
            "error_message": f"Circular workflow cycle detected: {path_str}. Execution blocked.",
            "message": f"Circular workflow cycle detected: {path_str}. Execution blocked."
        }
    return {
        "valid": True,
        "is_valid_dag": True,
        "has_cycle": False,
        "detected_cycles": [],
        "cycle_path": [],
        "message": "Workflow dependency graph is a valid Directed Acyclic Graph (DAG) with 0 cycles."
    }

@connectors_router.get("/health")
async def get_all_health():
    """Returns administrator health check metrics, response latencies, and circuit breaker status."""
    return {
        "health_checks": health_monitor.get_latest_health_summary()
    }

@connectors_router.post("/health/check/{provider_id}")
async def trigger_single_health_check(provider_id: str):
    """Triggers an immediate safe canary probe for a specific provider."""
    res = health_monitor.check_provider_health(provider_id)
    return res

@connectors_router.get("/circuit-breakers")
async def list_circuit_breakers():
    """Lists current state of all provider circuit breakers."""
    cb_states = {}
    for p in connector_registry.list_all():
        cb = loop_manager.get_circuit_breaker(p.id)
        cb_states[p.id] = {
            "state": cb.state.value,
            "consecutive_failures": cb.consecutive_failures,
            "last_failure_time": cb.last_failure_time
        }
    return {"circuit_breakers": cb_states}
