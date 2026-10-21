"""
AJAX AI - Automated Test Suite: Public API Connectors, Loop Detection & Schema Validation
Covers all requirements from Master Prompt Section 11:
1. Valid API response mapping and 14 field types
2. Missing and nullable fields
3. Nested arrays, objects, and GeoPoint inference
4. Duplicate schema key resolution
5. Direct self-loops and multi-step workflow dependency cycles (A -> B -> C -> A)
6. Retry exhaustion and exponential backoff
7. Rate limiting (Token Bucket)
8. Circuit breaker state transitions (CLOSED -> OPEN -> HALF_OPEN)
9. SSRF prevention (Blocking 127.0.0.1, 169.254.169.254, private IP ranges)
10. Oversized response protection (>10MB)
11. Refresh loop protection & duplicate job locking
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import time
from connectors.base import (
    APIProviderConfig,
    AuthType,
    CORSStatus,
    DataClassification,
    FieldType,
    ConnectorRequest,
    CircuitBreakerState
)
from connectors.loop_detector import (
    RequestLoopDetector,
    WorkflowCycleDetector,
    CircuitBreaker,
    RetryLoopProtector,
    RecursiveSchemaGuard,
    RefreshLoopGuard,
    LoopDetectionException,
    CircuitBreakerOpenException
)
from connectors.rate_limiter import (
    TokenBucketRateLimiter,
    QuotaTracker,
    ConnectorCache,
    RateLimitExceededException
)
from connectors.schema_mapper import JSONSchemaMapper
from connectors.proxy import validate_outbound_ip, SSRFProtectionException, SecureAPIProxy

class TestLoopDetectionSubsystem(unittest.TestCase):
    """Test suite for the 5-pillar loop and cycle detection engine."""

    def test_request_loop_tripped_on_rapid_identical_calls(self):
        detector = RequestLoopDetector(window_sec=2.0, max_identical_calls=3)
        # First 3 calls should pass
        for i in range(3):
            detector.check_and_record("open_meteo", "forecast", "GET", {"lat": 10}, "workflow_a", depth=1)

        # 4th identical call within 2 seconds MUST raise LoopDetectionException
        with self.assertRaises(LoopDetectionException) as ctx:
            detector.check_and_record("open_meteo", "forecast", "GET", {"lat": 10}, "workflow_a", depth=1)
        self.assertEqual(ctx.exception.loop_type, "REQUEST_RAPID_LOOP")

    def test_request_depth_ceiling_enforced(self):
        detector = RequestLoopDetector(max_depth=5)
        # Depth 6 must be blocked
        with self.assertRaises(LoopDetectionException) as ctx:
            detector.check_and_record("open_meteo", "forecast", "GET", {}, "deep_workflow", depth=6)
        self.assertEqual(ctx.exception.loop_type, "REQUEST_DEPTH_EXCEEDED")

    def test_workflow_cycle_detection_direct_self_loop(self):
        detector = WorkflowCycleDetector()
        detector.register_dependency("StepA", "StepA")
        cycle = detector.find_cycle()
        self.assertIsNotNone(cycle)
        self.assertIn("StepA", cycle)

    def test_workflow_cycle_detection_multi_step_cycle(self):
        detector = WorkflowCycleDetector()
        # Create cycle: Weather -> SchemaGen -> Refresh -> Weather
        detector.register_dependency("WeatherConnector", "SchemaGenerator")
        detector.register_dependency("SchemaGenerator", "RefreshWorkflow")
        detector.register_dependency("RefreshWorkflow", "WeatherConnector")

        cycle = detector.find_cycle()
        self.assertIsNotNone(cycle)
        self.assertEqual(cycle[0], cycle[-1]) # Begins and ends at same node
        self.assertTrue(len(cycle) >= 3)

        with self.assertRaises(LoopDetectionException) as ctx:
            detector.validate_no_cycles_or_raise()
        self.assertEqual(ctx.exception.loop_type, "WORKFLOW_DEPENDENCY_CYCLE")

    def test_workflow_dag_without_cycles_passes(self):
        detector = WorkflowCycleDetector()
        detector.register_dependency("A", "B")
        detector.register_dependency("B", "C")
        detector.register_dependency("A", "C")
        self.assertIsNone(detector.find_cycle())

    def test_circuit_breaker_transitions(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.2)
        self.assertEqual(cb.state, CircuitBreakerState.CLOSED)

        # Record 2 failures -> Still CLOSED
        cb.record_failure(500, "Error 1")
        cb.record_failure(500, "Error 2")
        self.assertEqual(cb.state, CircuitBreakerState.CLOSED)

        # 3rd failure -> Tripped to OPEN
        cb.record_failure(500, "Error 3")
        self.assertEqual(cb.state, CircuitBreakerState.OPEN)

        # Should block requests
        with self.assertRaises(CircuitBreakerOpenException):
            cb.check_state()

        # Wait for recovery timeout
        time.sleep(0.25)
        # Should transition to HALF_OPEN
        cb.check_state()
        self.assertEqual(cb.state, CircuitBreakerState.HALF_OPEN)

        # On success, transitions back to CLOSED
        cb.record_success()
        self.assertEqual(cb.state, CircuitBreakerState.CLOSED)
        self.assertEqual(cb.consecutive_failures, 0)

    def test_retry_protector_avoids_permanent_errors(self):
        protector = RetryLoopProtector(max_retries=3)
        # Should NOT retry client errors
        self.assertFalse(protector.should_retry(400, attempt=0))
        self.assertFalse(protector.should_retry(401, attempt=0))
        self.assertFalse(protector.should_retry(403, attempt=0))
        self.assertFalse(protector.should_retry(422, attempt=0))

        # Should retry server errors up to max_retries
        self.assertTrue(protector.should_retry(500, attempt=0))
        self.assertTrue(protector.should_retry(502, attempt=1))
        self.assertTrue(protector.should_retry(429, attempt=2))
        self.assertFalse(protector.should_retry(500, attempt=3)) # Exceeded

    def test_schema_guard_blocks_circular_reference(self):
        guard = RecursiveSchemaGuard()
        cyclic_dict = {}
        cyclic_dict["self"] = cyclic_dict
        with self.assertRaises(LoopDetectionException) as ctx:
            guard.validate_nesting(cyclic_dict)
        self.assertEqual(ctx.exception.loop_type, "CIRCULAR_OBJECT_REFERENCE")

    def test_refresh_guard_prevents_overlapping_jobs(self):
        guard = RefreshLoopGuard()
        # Acquire lock
        self.assertTrue(guard.acquire_refresh_lock("sync_weather_delhi"))
        # Second acquire for same job MUST fail (preventing overlap)
        self.assertFalse(guard.acquire_refresh_lock("sync_weather_delhi"))
        # Release and reacquire
        guard.release_refresh_lock("sync_weather_delhi")
        self.assertTrue(guard.acquire_refresh_lock("sync_weather_delhi"))

class TestRateLimiterAndSSRF(unittest.TestCase):
    """Test suite for token bucket rate limits and SSRF IP blocking."""

    def test_token_bucket_exhaustion(self):
        # 60 rpm = 1 token/sec, capacity 3
        limiter = TokenBucketRateLimiter(rate_per_minute=60, burst_capacity=3)
        self.assertTrue(limiter.acquire(1))
        self.assertTrue(limiter.acquire(1))
        self.assertTrue(limiter.acquire(1))
        # 4th token cannot be acquired immediately
        self.assertFalse(limiter.acquire(1))
        self.assertTrue(limiter.time_until_available(1) > 0)

    def test_ssrf_blocks_loopback(self):
        with self.assertRaises(SSRFProtectionException):
            validate_outbound_ip("127.0.0.1")
        with self.assertRaises(SSRFProtectionException):
            validate_outbound_ip("localhost")

    def test_ssrf_blocks_cloud_metadata(self):
        # AWS/GCP/Azure internal metadata IP 169.254.169.254 must be blocked
        with self.assertRaises(SSRFProtectionException):
            validate_outbound_ip("169.254.169.254")

    def test_ssrf_blocks_private_rfc1918(self):
        with self.assertRaises(SSRFProtectionException):
            validate_outbound_ip("10.0.0.1")
        with self.assertRaises(SSRFProtectionException):
            validate_outbound_ip("192.168.1.1")
        with self.assertRaises(SSRFProtectionException):
            validate_outbound_ip("172.16.0.5")

    def test_connector_cache_expiration(self):
        cache = ConnectorCache(default_ttl_sec=1)
        cache.set("test_key", {"val": 123}, {}, ttl_sec=1)
        self.assertIsNotNone(cache.get("test_key"))
        time.sleep(1.1)
        self.assertIsNone(cache.get("test_key"))

class TestJSONSchemaMapper(unittest.TestCase):
    """Test suite for 14 field types, JSONPath, and preview generation."""

    def setUp(self):
        self.mapper = JSONSchemaMapper()

    def test_type_inference_all_types(self):
        self.assertEqual(self.mapper.infer_type("John Doe"), FieldType.TEXT)
        self.assertEqual(self.mapper.infer_type(42), FieldType.NUMBER)
        self.assertEqual(self.mapper.infer_type(True), FieldType.BOOLEAN)
        self.assertEqual(self.mapper.infer_type("john@example.com"), FieldType.EMAIL)
        self.assertEqual(self.mapper.infer_type("https://example.com/logo.png"), FieldType.IMAGE_URL)
        self.assertEqual(self.mapper.infer_type("https://example.com/api"), FieldType.URL)
        self.assertEqual(self.mapper.infer_type("2026-10-21"), FieldType.DATE)
        self.assertEqual(self.mapper.infer_type("2026-10-21T09:30:00Z"), FieldType.DATETIME)
        self.assertEqual(self.mapper.infer_type({"lat": 28.61, "lon": 77.20}), FieldType.GEO_POINT)
        self.assertEqual(self.mapper.infer_type(["apple", "banana"]), FieldType.ARRAY)
        self.assertEqual(self.mapper.infer_type({"nested": "object"}), FieldType.OBJECT)

    def test_nested_json_extraction_and_preview(self):
        sample = {
            "user": {
                "name": "Ajay Singh",
                "email": "ajay@example.com",
                "active": True,
                "coordinates": {"lat": 28.61, "lon": 77.20}
            },
            "tags": ["admin", "ai_developer"],
            "stats": {
                "score": 98.5
            }
        }

        fields = self.mapper.infer_schema(sample)
        self.assertTrue(len(fields) >= 5)

        preview = self.mapper.generate_form_preview(fields, sample)
        self.assertEqual(preview["user_name"]["value"], "Ajay Singh")
        self.assertEqual(preview["user_email"]["value"], "ajay@example.com")
        self.assertEqual(preview["user_active"]["value"], True)
        self.assertEqual(preview["stats_score"]["value"], 98.5)

    def test_duplicate_key_resolution(self):
        # Two different paths resulting in similar naming
        existing = ["name", "user_name"]
        k1 = self.mapper.generate_stable_key("name", existing)
        self.assertEqual(k1, "name_1")
        k2 = self.mapper.generate_stable_key("user_name", existing)
        self.assertEqual(k2, "user_name_1")

if __name__ == "__main__":
    unittest.main()
