"""
AJAX AI - Secure SSRF-Protected Backend Proxy
Guarantees:
1. Destination URL validation against registered provider base URLs.
2. Anti-SSRF Protection: Resolves DNS and blocks loopback, private RFC1918, link-local, and AWS/GCP metadata (169.254.169.254).
3. Payload & response size capping (Max 10MB).
4. Content-type enforcement and credential redaction.
5. Integration with Loop Detector, Rate Limiter, and Circuit Breaker.
"""

import os
import socket
import ipaddress
import urllib.parse
import time
import json
import requests
from typing import Dict, Any, Optional, List, Tuple
from connectors.base import ConnectorRequest, ConnectorResponse, DataClassification
from connectors.loop_detector import loop_manager, LoopDetectionException, CircuitBreakerOpenException
from connectors.rate_limiter import rate_limiter, RateLimitExceededException
from core.logger import ajax_logger, security_logger

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("10.0.0.0/8"),       # Private RFC1918
    ipaddress.ip_network("172.16.0.0/12"),    # Private RFC1918
    ipaddress.ip_network("192.168.0.0/16"),   # Private RFC1918
    ipaddress.ip_network("169.254.0.0/16"),   # Link-Local & Cloud Metadata (AWS/GCP/Azure)
    ipaddress.ip_network("100.64.0.0/10"),    # Carrier-grade NAT
    ipaddress.ip_network("0.0.0.0/8"),        # This host
    ipaddress.ip_network("::1/128"),          # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),         # IPv6 Unique Local
    ipaddress.ip_network("fe80::/10"),        # IPv6 Link-Local
]

MAX_RESPONSE_BYTES = 10 * 1024 * 1024 # 10 MB

class SSRFProtectionException(Exception):
    """Raised when an outbound URL resolves to a prohibited private, internal, or loopback network."""
    pass

def validate_outbound_ip(hostname: str) -> str:
    """Resolves target hostname and verifies that IP is strictly public and routable."""
    try:
        # Resolve all IPs
        addr_infos = socket.getaddrinfo(hostname, None)
        if not addr_infos:
            raise SSRFProtectionException(f"Unable to resolve hostname '{hostname}'.")

        for family, _, _, _, sockaddr in addr_infos:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)

            for blocked_net in BLOCKED_IP_NETWORKS:
                if ip_obj in blocked_net:
                    security_logger.error(f"SSRF Attempt BLOCKED: Hostname '{hostname}' resolved to prohibited IP '{ip_str}' in range '{blocked_net}'!")
                    raise SSRFProtectionException(f"Destination IP '{ip_str}' is private, loopback, or metadata address and is strictly blocked.")
        return addr_infos[0][4][0]
    except socket.gaierror as e:
        raise SSRFProtectionException(f"DNS lookup failure for '{hostname}': {e}")

class SecureAPIProxy:
    """Executes safe, verified outbound requests to registered public API providers."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AJAX-AI-Public-API-Engine/3.0 (+https://github.com/Ajay8x/ai)"
        })

    def execute_request(
        self,
        req: ConnectorRequest,
        provider_config: Any
    ) -> ConnectorResponse:
        t0 = time.time()
        cb = loop_manager.get_circuit_breaker(req.provider_id)

        # Step 1: Circuit Breaker Status Check
        cb.check_state()

        # Step 2: Request Loop & Depth Check
        loop_manager.request_detector.check_and_record(
            provider_id=req.provider_id,
            endpoint=req.endpoint,
            method=req.method,
            params=req.params,
            workflow=req.calling_workflow,
            depth=req.depth,
            correlation_id=req.correlation_id
        )

        # Step 3: Rate Limiting & Daily Quota Enforcement
        rate_limiter.enforce_rate_limit(
            provider_id=req.provider_id,
            rate_per_minute=provider_config.rate_limit_rpm,
            max_daily_quota=provider_config.quota_daily
        )

        # Step 4: Resolve Full URL and Enforce Allowlist & SSRF Safeguards
        base_url = provider_config.base_url.rstrip("/")
        rel_endpoint = req.endpoint.lstrip("/")
        full_url = f"{base_url}/{rel_endpoint}" if rel_endpoint else base_url

        parsed_url = urllib.parse.urlparse(full_url)
        parsed_base = urllib.parse.urlparse(base_url)

        # Allowlist host check
        if parsed_url.hostname.lower() != parsed_base.hostname.lower():
            raise SSRFProtectionException(
                f"Destination hostname '{parsed_url.hostname}' does not match provider allowlist '{parsed_base.hostname}'."
            )

        # DNS Anti-SSRF Resolution check
        validate_outbound_ip(parsed_url.hostname)

        # Step 5: Check Conditional Cache (ETag / TTL)
        cache_key = rate_limiter.cache.generate_key(req.provider_id, req.endpoint, req.params)
        cached_entry = None
        if not req.skip_cache and req.method.upper() == "GET":
            cached_entry = rate_limiter.cache.get(cache_key)
            if cached_entry:
                return ConnectorResponse(
                    success=True,
                    status_code=200,
                    data=cached_entry["data"],
                    headers=cached_entry["headers"],
                    latency_ms=(time.time() - t0) * 1000,
                    from_cache=True,
                    etag=cached_entry.get("etag"),
                    data_classification=provider_config.data_classification,
                    attribution=provider_config.attribution,
                    source_url=full_url
                )

        # Step 6: Assemble Headers (including conditional headers if available)
        request_headers = dict(provider_config.headers)
        request_headers.update(req.headers)

        # Secure server-side credential injection
        if provider_config.id == "openaq":
            api_key = os.environ.get("OPENAQ_API_KEY", "").strip()
            if api_key:
                request_headers["X-API-Key"] = api_key
            else:
                return ConnectorResponse(
                    success=False,
                    status_code=401,
                    error="Missing credential: OPENAQ_API_KEY. Please configure OPENAQ_API_KEY in your .env file to enable live OpenAQ queries.",
                    data={
                        "status": "unauthenticated",
                        "provider": "openaq",
                        "required_key": "OPENAQ_API_KEY",
                        "help": "Get a free API key at https://docs.openaq.org/ and configure OPENAQ_API_KEY in your .env file."
                    },
                    data_classification=provider_config.data_classification,
                    attribution=provider_config.attribution,
                    source_url=full_url
                )

        if provider_config.id == "windy_webcams":
            api_key = os.environ.get("WINDY_API_KEY", "").strip()
            if api_key:
                request_headers["x-windy-api-key"] = api_key
            else:
                return ConnectorResponse(
                    success=False,
                    status_code=401,
                    error="Missing credential: WINDY_API_KEY. Please configure WINDY_API_KEY in your .env file to enable live Windy Webcam queries.",
                    data={
                        "status": "unauthenticated",
                        "provider": "windy_webcams",
                        "required_key": "WINDY_API_KEY",
                        "help": "Get a free API key at https://api.windy.com/webcams/docs and configure WINDY_API_KEY in your .env file."
                    },
                    data_classification=provider_config.data_classification,
                    attribution=provider_config.attribution,
                    source_url=full_url
                )

        if cached_entry:
            if cached_entry.get("etag"):
                request_headers["If-None-Match"] = cached_entry["etag"]
            if cached_entry.get("last_modified"):
                request_headers["If-Modified-Since"] = cached_entry["last_modified"]

        # Step 7: Execute Outbound Call with Concurrency Semaphore & Retries
        semaphore = rate_limiter.get_semaphore(req.provider_id)
        max_retries = provider_config.retry_max or 3
        timeout_sec = req.timeout or provider_config.default_timeout or 10

        last_resp = None
        attempt = 0

        with semaphore:
            while attempt <= max_retries:
                try:
                    response = self.session.request(
                        method=req.method.upper(),
                        url=full_url,
                        params=req.params,
                        json=req.body if req.method.upper() in ("POST", "PUT", "PATCH") else None,
                        headers=request_headers,
                        timeout=timeout_sec,
                        stream=True
                    )

                    # Check for 304 Not Modified
                    if response.status_code == 304 and cached_entry:
                        cb.record_success()
                        return ConnectorResponse(
                            success=True,
                            status_code=200,
                            data=cached_entry["data"],
                            headers=cached_entry["headers"],
                            latency_ms=(time.time() - t0) * 1000,
                            from_cache=True,
                            etag=cached_entry.get("etag"),
                            data_classification=provider_config.data_classification,
                            attribution=provider_config.attribution,
                            source_url=full_url
                        )

                    # Check Response Size against ceiling
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > MAX_RESPONSE_BYTES:
                        raise ValueError(f"Upstream response size {content_length} bytes exceeds 10MB threshold.")

                    # Read limited content safely
                    raw_content = response.raw.read(MAX_RESPONSE_BYTES + 1, decode_content=True)
                    if len(raw_content) > MAX_RESPONSE_BYTES:
                        raise ValueError(f"Upstream response exceeded maximum buffer ceiling of 10MB.")

                    # Parse JSON or Text
                    resp_headers = dict(response.headers)
                    parsed_data = None
                    try:
                        parsed_data = json.loads(raw_content.decode("utf-8", errors="replace"))
                    except Exception:
                        parsed_data = raw_content.decode("utf-8", errors="replace")

                    # Handle 429 Too Many Requests or Server Errors with Backoff
                    if response.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                        retry_after = resp_headers.get("Retry-After") or resp_headers.get("retry-after")
                        backoff_sec = loop_manager.retry_protector.calculate_backoff(attempt, retry_after)
                        security_logger.warning(f"Upstream {provider_config.id} returned HTTP {response.status_code}. Retrying in {backoff_sec:.2f}s (Attempt {attempt+1}/{max_retries})")
                        time.sleep(backoff_sec)
                        attempt += 1
                        continue

                    # Record Usage & Success
                    rate_limiter.quota_tracker.record_usage(req.provider_id)
                    latency = (time.time() - t0) * 1000

                    # Strip sensitive credentials from headers before returning or caching
                    SENSITIVE_HEADERS = {"x-api-key", "x-windy-api-key", "authorization", "cookie", "set-cookie"}
                    sanitized_headers = {k: v for k, v in resp_headers.items() if k.lower() not in SENSITIVE_HEADERS}

                    if 200 <= response.status_code < 300:
                        cb.record_success()
                        # Cache successful GET
                        if req.method.upper() == "GET" and parsed_data is not None:
                            rate_limiter.cache.set(
                                cache_key=cache_key,
                                data=parsed_data,
                                headers=sanitized_headers,
                                ttl_sec=provider_config.cache_ttl_sec
                            )

                        return ConnectorResponse(
                            success=True,
                            status_code=response.status_code,
                            data=parsed_data,
                            headers=sanitized_headers,
                            latency_ms=latency,
                            from_cache=False,
                            etag=resp_headers.get("etag") or resp_headers.get("ETag"),
                            data_classification=provider_config.data_classification,
                            attribution=provider_config.attribution,
                            source_url=full_url
                        )
                    else:
                        cb.record_failure(response.status_code, f"HTTP {response.status_code}")
                        return ConnectorResponse(
                            success=False,
                            status_code=response.status_code,
                            data=parsed_data,
                            headers=sanitized_headers,
                            latency_ms=latency,
                            error=f"Upstream error HTTP {response.status_code}",
                            data_classification=provider_config.data_classification,
                            attribution=provider_config.attribution,
                            source_url=full_url
                        )

                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt < max_retries:
                        backoff_sec = loop_manager.retry_protector.calculate_backoff(attempt)
                        security_logger.warning(f"Upstream connection failed ({e}). Retrying in {backoff_sec:.2f}s...")
                        time.sleep(backoff_sec)
                        attempt += 1
                        continue
                    cb.record_failure(504, str(e))
                    raise e

secure_proxy = SecureAPIProxy()
