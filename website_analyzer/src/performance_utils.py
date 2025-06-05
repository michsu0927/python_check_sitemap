"""
Performance optimization utilities for the Website Analyzer.
Includes caching, rate limiting, memory management, and monitoring.
"""

import asyncio
import time
import hashlib
import json
import gc
import psutil
from typing import Dict, Any, Optional, List, Callable, Union
from functools import wraps
from dataclasses import dataclass
from datetime import datetime, timedelta
import aioredis
from pathlib import Path
import pickle


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_before: Optional[float] = None
    memory_after: Optional[float] = None
    memory_peak: Optional[float] = None
    cpu_percent: Optional[float] = None
    api_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0


class MemoryCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize memory cache.
        
        Args:
            max_size: Maximum number of cached items
            default_ttl: Default time-to-live in seconds
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        
    def _is_expired(self, item: Dict[str, Any]) -> bool:
        """Check if cache item is expired."""
        return time.time() > item['expires_at']
        
    def _cleanup_expired(self):
        """Remove expired items from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, item in self._cache.items()
            if current_time > item['expires_at']
        ]
        for key in expired_keys:
            del self._cache[key]
            
    def _evict_lru(self):
        """Evict least recently used items if cache is full."""
        if len(self._cache) >= self._max_size:
            # Sort by last accessed time
            lru_key = min(
                self._cache.keys(),
                key=lambda k: self._cache[k]['last_accessed']
            )
            del self._cache[lru_key]
            
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        self._cleanup_expired()
        
        if key in self._cache:
            item = self._cache[key]
            if not self._is_expired(item):
                item['last_accessed'] = time.time()
                return item['value']
            else:
                del self._cache[key]
                
        return None
        
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set item in cache."""
        self._cleanup_expired()
        self._evict_lru()
        
        ttl = ttl or self._default_ttl
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'last_accessed': time.time()
        }
        
    def delete(self, key: str) -> bool:
        """Delete item from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
        
    def clear(self) -> None:
        """Clear all cache items."""
        self._cache.clear()
        
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        self._cleanup_expired()
        return {
            'size': len(self._cache),
            'max_size': self._max_size,
            'hit_rate': getattr(self, '_hits', 0) / max(getattr(self, '_requests', 1), 1)
        }


class RedisCache:
    """Redis-based cache with async support."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", prefix: str = "wa:"):
        """
        Initialize Redis cache.
        
        Args:
            redis_url: Redis connection URL
            prefix: Key prefix for namespacing
        """
        self._redis_url = redis_url
        self._prefix = prefix
        self._redis: Optional[aioredis.Redis] = None
        
    async def connect(self):
        """Connect to Redis."""
        try:
            self._redis = await aioredis.from_url(self._redis_url)
            await self._redis.ping()
        except Exception:
            self._redis = None
            
    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        if not self._redis:
            return None
            
        try:
            data = await self._redis.get(f"{self._prefix}{key}")
            if data:
                return pickle.loads(data)
        except Exception:
            pass
            
        return None
        
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set item in cache."""
        if not self._redis:
            return False
            
        try:
            data = pickle.dumps(value)
            await self._redis.setex(f"{self._prefix}{key}", ttl, data)
            return True
        except Exception:
            return False
            
    async def delete(self, key: str) -> bool:
        """Delete item from cache."""
        if not self._redis:
            return False
            
        try:
            result = await self._redis.delete(f"{self._prefix}{key}")
            return result > 0
        except Exception:
            return False


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, max_tokens: int, refill_period: float, refill_amount: int = 1):
        """
        Initialize rate limiter.
        
        Args:
            max_tokens: Maximum number of tokens in bucket
            refill_period: Time between refills in seconds
            refill_amount: Number of tokens to add per refill
        """
        self._max_tokens = max_tokens
        self._refill_period = refill_period
        self._refill_amount = refill_amount
        self._tokens = max_tokens
        self._last_refill = time.time()
        self._lock = asyncio.Lock()
        
    async def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens acquired, False otherwise
        """
        async with self._lock:
            self._refill_tokens()
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False
            
    async def wait_for_token(self, tokens: int = 1) -> None:
        """Wait until tokens are available."""
        while not await self.acquire(tokens):
            await asyncio.sleep(0.1)
            
    def _refill_tokens(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        time_passed = now - self._last_refill
        
        if time_passed >= self._refill_period:
            tokens_to_add = int(time_passed / self._refill_period) * self._refill_amount
            self._tokens = min(self._max_tokens, self._tokens + tokens_to_add)
            self._last_refill = now


class PerformanceMonitor:
    """Performance monitoring and optimization utilities."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self._metrics: Dict[str, PerformanceMetrics] = {}
        self._memory_cache = MemoryCache()
        self._redis_cache: Optional[RedisCache] = None
        self._rate_limiters: Dict[str, RateLimiter] = {}
        
    async def setup_redis_cache(self, redis_url: str):
        """Setup Redis cache."""
        self._redis_cache = RedisCache(redis_url)
        await self._redis_cache.connect()
        
    def create_rate_limiter(self, name: str, max_tokens: int, refill_period: float) -> RateLimiter:
        """Create and register a rate limiter."""
        limiter = RateLimiter(max_tokens, refill_period)
        self._rate_limiters[name] = limiter
        return limiter
        
    def get_rate_limiter(self, name: str) -> Optional[RateLimiter]:
        """Get rate limiter by name."""
        return self._rate_limiters.get(name)
        
    async def cached_call(
        self,
        cache_key: str,
        func: Callable,
        *args,
        ttl: int = 3600,
        use_redis: bool = False,
        **kwargs
    ) -> Any:
        """
        Execute function with caching.
        
        Args:
            cache_key: Unique cache key
            func: Function to execute
            ttl: Cache TTL in seconds
            use_redis: Use Redis cache if available
            *args, **kwargs: Function arguments
            
        Returns:
            Function result (cached or fresh)
        """
        # Try cache first
        cache = self._redis_cache if use_redis and self._redis_cache else self._memory_cache
        
        if use_redis and self._redis_cache:
            result = await cache.get(cache_key)
        else:
            result = cache.get(cache_key)
            
        if result is not None:
            return result
            
        # Execute function
        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
            
        # Cache result
        if use_redis and self._redis_cache:
            await cache.set(cache_key, result, ttl)
        else:
            cache.set(cache_key, result, ttl)
            
        return result
        
    def start_monitoring(self, operation_id: str) -> PerformanceMetrics:
        """Start monitoring an operation."""
        metrics = PerformanceMetrics(
            start_time=time.time(),
            memory_before=self._get_memory_usage(),
            cpu_percent=psutil.cpu_percent()
        )
        self._metrics[operation_id] = metrics
        return metrics
        
    def stop_monitoring(self, operation_id: str) -> Optional[PerformanceMetrics]:
        """Stop monitoring an operation."""
        if operation_id not in self._metrics:
            return None
            
        metrics = self._metrics[operation_id]
        metrics.end_time = time.time()
        metrics.duration = metrics.end_time - metrics.start_time
        metrics.memory_after = self._get_memory_usage()
        metrics.memory_peak = self._get_peak_memory()
        
        return metrics
        
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
        
    def _get_peak_memory(self) -> float:
        """Get peak memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().peak_wss / 1024 / 1024 if hasattr(process.memory_info(), 'peak_wss') else 0
        
    async def optimize_memory(self):
        """Perform memory optimization."""
        # Force garbage collection
        gc.collect()
        
        # Clear expired cache entries
        self._memory_cache._cleanup_expired()
        
        # Log memory stats
        current_memory = self._get_memory_usage()
        return current_memory
        
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'memory_cache': self._memory_cache.stats()
        }
        
        if self._redis_cache:
            stats['redis_cache'] = {'connected': self._redis_cache._redis is not None}
            
        return stats
        
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        total_operations = len(self._metrics)
        completed_operations = sum(1 for m in self._metrics.values() if m.end_time is not None)
        
        if completed_operations > 0:
            avg_duration = sum(
                m.duration for m in self._metrics.values() 
                if m.duration is not None
            ) / completed_operations
            
            avg_memory = sum(
                m.memory_after for m in self._metrics.values()
                if m.memory_after is not None
            ) / completed_operations
        else:
            avg_duration = 0
            avg_memory = 0
            
        return {
            'total_operations': total_operations,
            'completed_operations': completed_operations,
            'average_duration': avg_duration,
            'average_memory_usage': avg_memory,
            'cache_stats': self.get_cache_stats(),
            'current_memory': self._get_memory_usage()
        }


def timed_operation(monitor: PerformanceMonitor):
    """Decorator for timing operations."""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            operation_id = f"{func.__name__}_{int(time.time() * 1000)}"
            monitor.start_monitoring(operation_id)
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                monitor.stop_monitoring(operation_id)
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            operation_id = f"{func.__name__}_{int(time.time() * 1000)}"
            monitor.start_monitoring(operation_id)
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                monitor.stop_monitoring(operation_id)
                
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def rate_limited(limiter_name: str, tokens: int = 1):
    """Decorator for rate limiting."""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get monitor from args or kwargs (assuming it's passed)
            monitor = None
            for arg in args:
                if isinstance(arg, PerformanceMonitor):
                    monitor = arg
                    break
                    
            if monitor:
                limiter = monitor.get_rate_limiter(limiter_name)
                if limiter:
                    await limiter.wait_for_token(tokens)
                    
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        return wrapper
    return decorator


def cache_key_from_args(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    key_data = {
        'args': [str(arg) for arg in args],
        'kwargs': {k: str(v) for k, v in kwargs.items()}
    }
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
