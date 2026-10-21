"""
AJAX AI - Mandatory Loop Detection & Workflow Cycle Prevention System
Pillars:
1. Request Loop Detection (Hashing, time windows, depth & rate thresholds)
2. Directed Graph Workflow Cycle Detection (DFS Cycle finding & path tracing)
3. Retry Loop Protection (Exponential backoff, jitter, circuit breakers, 401/403 non-retry)
4. Recursive Schema Generation Guard (Depth & sample bounds, cyclic object guard)
5. Refresh Loop Protection (Concurrency locks, overlapping refresh deduplication)
"""

import time
import json
import hashlib
import random
import threading
from typing import Dict, List, Set, Tuple, Optional, Any
from connectors.base import CircuitBreakerState
from core.logger import ajax_logger, security_logger

class LoopDetectionException(Exception):
    """Raised when a dangerous loop, cycle, or infinite retry is detected."""
    def __init__(self, message: str, loop_type: str, details: Dict[str, Any]):
        super().__init__(message)
        self.loop_type = loop_type
        self.details = details

class CircuitBreakerOpenException(Exception):
    """Raised when request is blocked because the provider circuit breaker is open."""
    pass

class RequestLoopDetector:
    """Detects rapid identical request loops within configurable sliding time windows."""
    def __init__(self, window_sec: float = 3.0, max_identical_calls: int = 5, max_depth: int = 8):
        self.window_sec = window_sec
        self.max_identical_calls = max_identical_calls
        self.max_depth = max_depth
        self._history: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def generate_fingerprint(self, provider_id: str, endpoint: str, method: str, params: Any, workflow: str) -> str:
        norm_endpoint = endpoint.strip().lower()
        param_str = json.dumps(params or {}, sort_keys=True, default=str)
        raw = f"{provider_id}|{norm_endpoint}|{method.upper()}|{param_str}|{workflow}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def check_and_record(self, provider_id: str, endpoint: str, method: str, params: Any, workflow: str, depth: int, correlation_id: str = "") -> None:
        if depth > self.max_depth:
            raise LoopDetectionException(
                f"Request depth {depth} exceeds safety ceiling of {self.max_depth}.",
                loop_type="REQUEST_DEPTH_EXCEEDED",
                details={"depth": depth, "max_depth": self.max_depth, "workflow": workflow, "correlation_id": correlation_id}
            )

        now = time.time()
        fp = self.generate_fingerprint(provider_id, endpoint, method, params, workflow)

        with self._lock:
            timestamps = self._history.get(fp, [])
            # Prune older than sliding window
            timestamps = [t for t in timestamps if now - t <= self.window_sec]
            
            if len(timestamps) >= self.max_identical_calls:
                security_logger.error(f"Request loop tripped for {provider_id}:{endpoint} ({len(timestamps)} calls in {self.window_sec}s)")
                raise LoopDetectionException(
                    f"Request Loop Detected: {len(timestamps)} identical requests to '{provider_id}:{endpoint}' in {self.window_sec} seconds.",
                    loop_type="REQUEST_RAPID_LOOP",
                    details={"provider_id": provider_id, "endpoint": endpoint, "calls": len(timestamps), "window_sec": self.window_sec}
                )

            timestamps.append(now)
            self._history[fp] = timestamps

class WorkflowCycleDetector:
    """Detects cycles in directed graphs of connectors, data flows, and automated triggers."""
    def __init__(self):
        self._adjacency_list: Dict[str, Set[str]] = {}
        self._lock = threading.Lock()

    def register_dependency(self, source_node: str, target_node: str) -> None:
        with self._lock:
            if source_node not in self._adjacency_list:
                self._adjacency_list[source_node] = set()
            self._adjacency_list[source_node].add(target_node)

    def remove_dependency(self, source_node: str, target_node: str) -> None:
        with self._lock:
            if source_node in self._adjacency_list:
                self._adjacency_list[source_node].discard(target_node)

    def set_graph(self, graph: Dict[str, List[str]]) -> None:
        with self._lock:
            self._adjacency_list = {k: set(v) for k, v in graph.items()}

    def find_cycle(self) -> Optional[List[str]]:
        """
        Uses Tarjan / DFS with visited and rec_stack to detect cycles.
        Returns the exact cycle path if found, e.g. ['A', 'B', 'C', 'A'].
        """
        with self._lock:
            visited: Set[str] = set()
            rec_stack: Set[str] = set()
            parent_map: Dict[str, str] = {}

            all_nodes = set(self._adjacency_list.keys())
            for neighbors in self._adjacency_list.values():
                all_nodes.update(neighbors)

            for node in all_nodes:
                if node not in visited:
                    cycle = self._dfs_cycle(node, visited, rec_stack, parent_map, [node])
                    if cycle:
                        return cycle
            return None

    def _dfs_cycle(self, current: str, visited: Set[str], rec_stack: Set[str], parent_map: Dict[str, str], path: List[str]) -> Optional[List[str]]:
        visited.add(current)
        rec_stack.add(current)

        for neighbor in self._adjacency_list.get(current, set()):
            if neighbor not in visited:
                parent_map[neighbor] = current
                res = self._dfs_cycle(neighbor, visited, rec_stack, parent_map, path + [neighbor])
                if res:
                    return res
            elif neighbor in rec_stack:
                # Cycle found! Extract sub-path
                if neighbor in path:
                    idx = path.index(neighbor)
                    return path[idx:] + [neighbor]
                return [current, neighbor]

        rec_stack.remove(current)
        return None

    def validate_no_cycles_or_raise(self) -> None:
        cycle_path = self.find_cycle()
        if cycle_path:
            path_str = " -> ".join(cycle_path)
            raise LoopDetectionException(
                f"Workflow Cycle Detected: {path_str}. Circular dependencies are forbidden.",
                loop_type="WORKFLOW_DEPENDENCY_CYCLE",
                details={"cycle_path": cycle_path, "path_visual": path_str}
            )

class CircuitBreaker:
    """Tracks upstream failures, trips on consecutive errors, and manages half-open probing."""
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitBreakerState.CLOSED
        self.consecutive_failures = 0
        self.last_failure_time = 0.0
        self._lock = threading.Lock()

    def record_success(self) -> None:
        with self._lock:
            self.consecutive_failures = 0
            self.state = CircuitBreakerState.CLOSED

    def record_failure(self, status_code: int = 500, error_message: str = "") -> None:
        with self._lock:
            # Don't trip breaker on 404 (resource missing is not upstream down)
            if status_code in (404,):
                return
            self.consecutive_failures += 1
            self.last_failure_time = time.time()
            if self.consecutive_failures >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                security_logger.warning(f"Circuit Breaker TRIPPED to OPEN ({self.consecutive_failures} consecutive failures: {error_message})")

    def check_state(self) -> None:
        with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.recovery_timeout:
                    self.state = CircuitBreakerState.HALF_OPEN
                    ajax_logger.info("Circuit Breaker transitioned to HALF_OPEN (probing single canary request).")
                else:
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker is OPEN. Upstream temporarily suspended ({int(self.recovery_timeout - elapsed)}s remaining in cooldown)."
                    )

class RetryLoopProtector:
    """Enforces exponential backoff with jitter and strictly prevents infinite retry loops."""
    def __init__(self, max_retries: int = 3, base_delay: float = 0.5, max_delay: float = 10.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def should_retry(self, status_code: int, attempt: int) -> bool:
        # Never retry client authentication, access denials, or unresolvable client errors
        if status_code in (400, 401, 403, 405, 422):
            return False
        # Do not exceed max retries
        if attempt >= self.max_retries:
            return False
        # Retry on timeouts, connection breaks, and server errors (500, 502, 503, 504, 429)
        return status_code in (429, 500, 502, 503, 504) or status_code == 0

    def calculate_backoff(self, attempt: int, retry_after_header: Optional[str] = None) -> float:
        if retry_after_header:
            try:
                seconds = float(retry_after_header)
                return min(seconds, self.max_delay)
            except ValueError:
                pass

        # Exponential backoff: base * 2^(attempt) + Full Jitter
        exp = self.base_delay * (2 ** attempt)
        jitter = random.uniform(0, exp)
        return min(self.max_delay, jitter)

class RecursiveSchemaGuard:
    """Guards against cyclic structures or deeply nested JSON in dynamic schema inference."""
    def __init__(self, max_depth: int = 6, max_fields: int = 150, max_array_samples: int = 25):
        self.max_depth = max_depth
        self.max_fields = max_fields
        self.max_array_samples = max_array_samples

    def validate_nesting(self, obj: Any, current_depth: int = 0, seen_ids: Optional[Set[int]] = None) -> None:
        if seen_ids is None:
            seen_ids = set()

        obj_id = id(obj)
        if obj_id in seen_ids:
            raise LoopDetectionException(
                "Circular reference detected inside JSON data object structure.",
                loop_type="CIRCULAR_OBJECT_REFERENCE",
                details={"depth": current_depth}
            )

        if current_depth > self.max_depth:
            raise LoopDetectionException(
                f"JSON schema depth {current_depth} exceeds safety maximum of {self.max_depth}.",
                loop_type="MAX_SCHEMA_DEPTH_EXCEEDED",
                details={"depth": current_depth, "max_depth": self.max_depth}
            )

        if isinstance(obj, dict):
            seen_ids.add(obj_id)
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    self.validate_nesting(v, current_depth + 1, set(seen_ids))
        elif isinstance(obj, list):
            seen_ids.add(obj_id)
            for item in obj[:self.max_array_samples]:
                if isinstance(item, (dict, list)):
                    self.validate_nesting(item, current_depth + 1, set(seen_ids))

class RefreshLoopGuard:
    """Prevents overlapping scheduled refresh executions and duplicate running tasks."""
    def __init__(self):
        self._active_jobs: Set[str] = set()
        self._lock = threading.Lock()

    def acquire_refresh_lock(self, job_key: str) -> bool:
        with self._lock:
            if job_key in self._active_jobs:
                return False
            self._active_jobs.add(job_key)
            return True

    def release_refresh_lock(self, job_key: str) -> None:
        with self._lock:
            self._active_jobs.discard(job_key)

# Global Singleton Manager for Loop Subsystem
class LoopDetectionManager:
    def __init__(self):
        self.request_detector = RequestLoopDetector()
        self.cycle_detector = WorkflowCycleDetector()
        self.retry_protector = RetryLoopProtector()
        self.schema_guard = RecursiveSchemaGuard()
        self.refresh_guard = RefreshLoopGuard()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._cb_lock = threading.Lock()

    def get_circuit_breaker(self, provider_id: str) -> CircuitBreaker:
        with self._cb_lock:
            if provider_id not in self.circuit_breakers:
                self.circuit_breakers[provider_id] = CircuitBreaker()
            return self.circuit_breakers[provider_id]

loop_manager = LoopDetectionManager()
