"""
Production utilities for streaming responses, rate limiting, and error handling.
"""

from typing import AsyncGenerator, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import time
from utils_logger import log_event, log_error


class StreamingResponseHandler:
    """Handles streaming responses to clients."""
    
    def __init__(self, chunk_size: int = 50):
        self.chunk_size = chunk_size
    
    async def stream_response(
        self,
        full_response: str,
        user_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response in chunks.
        
        Args:
            full_response: Complete response text
            user_id: User ID for logging
            
        Yields:
            JSON lines format: data: {"chunk": "text"}\n\n
        """
        import json
        
        chars_sent = 0
        start_time = time.time()
        
        try:
            for i in range(0, len(full_response), self.chunk_size):
                chunk = full_response[i:i + self.chunk_size]
                chars_sent += len(chunk)
                
                # Add small latency for realistic streaming
                await asyncio.sleep(0.01)
                
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            elapsed = time.time() - start_time
            
            log_event("STREAM_COMPLETE", user_id, {
                "total_chars": len(full_response),
                "chunks": (len(full_response) + self.chunk_size - 1) // self.chunk_size,
                "elapsed_seconds": elapsed,
            })
        
        except Exception as e:
            log_error("STREAM_ERROR", user_id, e)
            yield f"data: {json.dumps({'error': 'Stream interrupted'})}\n\n"


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list[float]] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed under rate limit.
        
        Args:
            identifier: User ID, IP address, or other identifier
            
        Returns:
            Tuple of (allowed, info_dict)
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        # Remove old requests outside window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check if allowed
        request_count = len(self.requests[identifier])
        allowed = request_count < self.max_requests
        
        if allowed:
            self.requests[identifier].append(now)
        
        info = {
            "allowed": allowed,
            "current_requests": request_count,
            "max_requests": self.max_requests,
            "reset_in_seconds": self.window_seconds - (now - self.requests[identifier][0] if self.requests[identifier] else 0),
        }
        
        if not allowed:
            log_event("RATE_LIMIT_EXCEEDED", identifier, info)
        
        return allowed, info


class ErrorHandler:
    """Centralized error handling."""
    
    @staticmethod
    def handle_llm_error(error: Exception, user_id: str | None = None) -> str:
        """Convert LLM errors to user-friendly messages."""
        error_str = str(error).lower()
        
        if "api_key" in error_str or "authentication" in error_str:
            return "Service temporarily unavailable. Please try again later."
        elif "rate_limit" in error_str:
            return "Server is busy. Please wait a moment and try again."
        elif "timeout" in error_str:
            return "Request took too long. Please try with a shorter message."
        else:
            return "I encountered an error. Please rephrase your question."
    
    @staticmethod
    def handle_tool_error(error: Exception, tool_name: str, user_id: str | None = None) -> str:
        """Convert tool execution errors."""
        log_error(f"TOOL_ERROR_{tool_name}", user_id, error)
        return f"I encountered an error while using the {tool_name} tool. Please try again."


class ValidationHelper:
    """Request validation utilities."""
    
    @staticmethod
    def validate_message(message: str, max_length: int = 2000) -> tuple[bool, str | None]:
        """
        Validate user message.
        
        Args:
            message: Message to validate
            max_length: Maximum length in characters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not message or not message.strip():
            return False, "Message cannot be empty"
        
        if len(message) > max_length:
            return False, f"Message too long (max {max_length} characters)"
        
        # Check for potential injection attacks
        if ";" in message or "DROP" in message.upper():
            return False, "Invalid message format"
        
        return True, None
    
    @staticmethod
    def validate_language(language: str) -> bool:
        """Validate language code."""
        allowed = ["en", "ar_fusha", "ar_jordanian"]
        return language in allowed or language.startswith("ar")


class CacheManager:
    """Simple in-memory cache for frequent queries."""
    
    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, tuple[Any, float]] = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Any | None:
        """Get cached value if not expired."""
        if key not in self.cache:
            return None
        
        value, timestamp = self.cache[key]
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Cache a value."""
        self.cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Clear all cache."""
        self.cache.clear()


# Global instances
_rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
_cache_manager = CacheManager(ttl_seconds=3600)


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    return _rate_limiter


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance."""
    return _cache_manager


# Import asyncio for streaming
import asyncio
