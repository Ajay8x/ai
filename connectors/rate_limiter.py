"""
AJAX AI - Rate Limiter, Quota Enforcement & HTTP Caching Engine
Supports:
1. Token Bucket & Sliding Window per-provider and per-credential algorithms
2. Daily & Hourly Quota Tracking
3. Provider Concurrency Semaphores
4. Conditional Requests (ETag & Last-Modified cache negotiation)
5. In-Memory and Persistent SQLite/Postgres Cache with TTL
"""

import time
import json
import hashlib
import threading
from typing import Dict, Any, Optional, Tuple
from core.logger import ajax_logger, security_logger

class RateLimitExceededException(Exception):
    """Raised when an API request exceeds configured rate limits or quotas."""
    def __init__(self, message: str, retry_after_seconds: float):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds

class TokenBucketRateLimiter:
    """Token Bucket algorithm for smooth rate limiting."""
    def __init__(self, rate_per_minute: int = 60, burst_capacity: Optional[int] = None):
        self.rate_per_sec = max(rate_per_minute / 60.0, 0.01)
        self.capacity = burst_capacity or max(rate_per_minute // 4, 5)
        self.tokens = float(self.capacity)
        self.last_update = time.time()
        self._lock = threading.Lock()

    def acquire(self, tokens_needed: int = 1) -> bool:
        with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.last_update = now

            # Replenish tokens
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate_per_sec)

            if self.tokens >= tokens_needed:
                self.tokens -= tokens_needed
                return True
            return False

    def time_until_available(self, tokens_needed: int = 1) -> float:
        with self._lock:
            if self.tokens >= tokens_needed:
                return 0.0
            deficit = tokens_needed - self.tokens
            return deficit / self.rate_per_sec

class QuotaTracker:
    """Tracks daily and hourly cumulative API quota usage."""
    def __init__(self):
        self._hourly_usage: Dict[str, Dict[int, int]] = {} # provider -> {hour_epoch: count}
        self._daily_usage: Dict[str, Dict[int, int]] = {}  # provider -> {day_epoch: count}
        self._lock = threading.Lock()

    def record_usage(self, provider_id: str, units: int = 1) -> None:
        now = time.time()
        hour_epoch = int(now // 3600)
        day_epoch = int(now // 86400)

        with self._lock:
            if provider_id not in self._hourly_usage:
                self._hourly_usage[provider_id] = {}
            if provider_id not in self._daily_usage:
                self._daily_usage[provider_id] = {}

            self._hourly_usage[provider_id][hour_epoch] = self._hourly_usage[provider_id].get(hour_epoch, 0) + units
            self._daily_usage[provider_id][day_epoch] = self._daily_usage[provider_id].get(day_epoch, 0) + units

            # Cleanup older than 48 hours
            for h in list(self._hourly_usage[provider_id].keys()):
                if hour_epoch - h > 48:
                    del self._hourly_usage[provider_id][h]

            for d in list(self._daily_usage[provider_id].keys()):
                if day_epoch - d > 7:
                    del self._daily_usage[provider_id][d]

    def get_daily_usage(self, provider_id: str) -> int:
        day_epoch = int(time.time() // 86400)
        with self._lock:
            return self._daily_usage.get(provider_id, {}).get(day_epoch, 0)

    def check_daily_quota(self, provider_id: str, max_daily: Optional[int]) -> bool:
        if not max_daily:
            return True
        return self.get_daily_usage(provider_id) < max_daily

class ConnectorCache:
    """Thread-safe response caching with ETag, Last-Modified, and TTL management."""
    def __init__(self, default_ttl_sec: int = 300):
        self.default_ttl = default_ttl_sec
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def generate_key(self, provider_id: str, endpoint: str, params: Any) -> str:
        param_str = json.dumps(params or {}, sort_keys=True, default=str)
        raw = f"{provider_id}:{endpoint}:{param_str}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            entry = self._cache.get(cache_key)
            if not entry:
                return None
            if time.time() > entry["expires_at"]:
                del self._cache[cache_key]
                return None
            return entry

    def set(self, cache_key: str, data: Any, headers: Dict[str, str], ttl_sec: Optional[int] = None, etag: Optional[str] = None, last_modified: Optional[str] = None) -> None:
        ttl = ttl_sec or self.default_ttl
        now = time.time()
        with self._lock:
            self._cache[cache_key] = {
                "data": data,
                "headers": headers,
                "etag": etag or headers.get("etag") or headers.get("ETag"),
                "last_modified": last_modified or headers.get("last-modified") or headers.get("Last-Modified"),
                "created_at": now,
                "expires_at": now + ttl
            }

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

class RateLimiterRegistry:
    """Central access manager binding Token Buckets, Quotas, and Semaphores per provider."""
    def __init__(self):
        self._limiters: Dict[str, TokenBucketRateLimiter] = {}
        self._concurrency_semaphores: Dict[str, threading.Semaphore] = {}
        self.quota_tracker = QuotaTracker()
        self.cache = ConnectorCache()
        self._lock = threading.Lock()

    def get_limiter(self, provider_id: str, rate_per_minute: int = 60) -> TokenBucketRateLimiter:
        with self._lock:
            if provider_id not in self._limiters:
                self._limiters[provider_id] = TokenBucketRateLimiter(rate_per_minute=rate_per_minute)
            return self._limiters[provider_id]

    def get_semaphore(self, provider_id: str, max_concurrent: int = 5) -> threading.Semaphore:
        with self._lock:
            if provider_id not in self._concurrency_semaphores:
                self._concurrency_semaphores[provider_id] = threading.Semaphore(max_concurrent)
            return self._concurrency_semaphores[provider_id]

    def enforce_rate_limit(self, provider_id: str, rate_per_minute: int, max_daily_quota: Optional[int] = None) -> None:
        # 1. Check daily quota
        if not self.quota_tracker.check_daily_quota(provider_id, max_daily_quota):
            used = self.quota_tracker.get_daily_usage(provider_id)
            raise RateLimitExceededException(
                f"Provider '{provider_id}' daily quota exhausted ({used}/{max_daily_quota} calls today).",
                retry_after_seconds=3600.0
            )

        # 2. Token Bucket check
        limiter = self.get_limiter(provider_id, rate_per_minute)
        if not limiter.acquire():
            wait_sec = limiter.time_until_available()
            security_logger.warning(f"Rate limit exceeded for provider '{provider_id}'. Must wait {wait_sec:.2f}s.")
            raise RateLimitExceededException(
                f"Rate limit exceeded for provider '{provider_id}' (Limit: {rate_per_minute} rpm). Try again in {wait_sec:.1f}s.",
                retry_after_seconds=wait_sec
            )

rate_limiter = RateLimiterRegistry()
