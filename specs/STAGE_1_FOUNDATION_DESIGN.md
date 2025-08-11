# Stage 1 - Foundation Design Document

## Overview

Stage 1 establishes the core infrastructure for the Trove SDK: transport layer, authentication, rate limiting, caching, and error handling. This foundation must be robust as all subsequent stages depend on it.

## Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  Config  │  Exceptions  │  Transport  │ Rate Limiter │Cache │
├──────────┴──────────────┴─────────────┴──────────────┴──────┤
│                      httpx (HTTP Client)                    │
├─────────────────────────────────────────────────────────────┤
│                    Trove API v3 Endpoints                   │
└─────────────────────────────────────────────────────────────┘
```

## Detailed Component Design

### 1. Configuration Management (`trove/config.py`)

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path
import os

@dataclass
class TroveConfig:
    """Configuration for Trove API client."""
    
    # Authentication
    api_key: str
    
    # API Settings  
    base_url: str = "https://api.trove.nla.gov.au/v3"
    default_encoding: str = "json"
    
    # Rate Limiting
    rate_limit: float = 2.0  # requests per second (conservative)
    burst_limit: int = 5     # burst capacity
    max_concurrency: int = 3 # max concurrent requests
    
    # Retry/Backoff
    max_retries: int = 3
    base_backoff: float = 1.0  # seconds
    max_backoff: float = 60.0  # seconds
    backoff_jitter: bool = True
    
    # Caching
    cache_backend: str = "memory"  # "memory", "sqlite", "none"
    cache_ttl_search: int = 900    # 15 minutes for search results
    cache_ttl_record: int = 604800 # 7 days for individual records
    cache_ttl_coming_soon: int = 3600  # 1 hour for "coming soon" records
    
    # Timeouts  
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    
    # Logging
    log_level: str = "INFO"
    log_requests: bool = False
    redact_credentials: bool = True

    @classmethod
    def from_env(cls) -> 'TroveConfig':
        """Create config from environment variables."""
        api_key = os.environ.get('TROVE_API_KEY')
        if not api_key:
            raise ValueError("TROVE_API_KEY environment variable is required")
        
        return cls(
            api_key=api_key,
            base_url=os.environ.get('TROVE_BASE_URL', cls.base_url),
            rate_limit=float(os.environ.get('TROVE_RATE_LIMIT', cls.rate_limit)),
            # ... other env vars
        )

    def validate(self) -> None:
        """Validate configuration values."""
        if not self.api_key:
            raise ValueError("API key is required")
        if self.rate_limit <= 0:
            raise ValueError("Rate limit must be positive")
        # ... other validations
```

### 2. Transport Layer (`trove/transport.py`)

```python
import httpx
from typing import Dict, Any, Optional, Union
from urllib.parse import urljoin, urlencode
import logging
from .config import TroveConfig
from .rate_limit import RateLimiter
from .cache import CacheBackend
from .exceptions import TroveAPIError, RateLimitError, NetworkError

logger = logging.getLogger(__name__)

class TroveTransport:
    """HTTP transport layer for Trove API with rate limiting and caching."""
    
    def __init__(self, config: TroveConfig, cache: CacheBackend):
        self.config = config
        self.cache = cache
        self.rate_limiter = RateLimiter(
            rate=config.rate_limit,
            burst=config.burst_limit,
            max_concurrency=config.max_concurrency
        )
        
        # Configure httpx client
        self._client = httpx.Client(
            timeout=httpx.Timeout(
                connect=config.connect_timeout,
                read=config.read_timeout
            ),
            limits=httpx.Limits(max_connections=config.max_concurrency)
        )
        
        # Async client for async operations
        self._aclient = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=config.connect_timeout,  
                read=config.read_timeout
            ),
            limits=httpx.Limits(max_connections=config.max_concurrency)
        )

    def _build_url(self, endpoint: str) -> str:
        """Build full URL for API endpoint."""
        return urljoin(self.config.base_url, endpoint.lstrip('/'))

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers with authentication."""
        headers = {
            'X-API-KEY': self.config.api_key,
            'User-Agent': 'trove-sdk-python/1.0.0',
            'Accept': 'application/json' if self.config.default_encoding == 'json' else 'application/xml'
        }
        return headers

    def _build_cache_key(self, method: str, url: str, params: Dict[str, Any]) -> str:
        """Build normalized cache key."""
        # Exclude credentials and vary by important headers
        cache_params = params.copy()
        cache_params.pop('key', None)  # Remove API key from cache key
        
        # Sort parameters for consistent keys
        param_str = urlencode(sorted(cache_params.items()))
        cache_key = f"{method}:{url}:{param_str}:{self.config.default_encoding}"
        
        return cache_key

    def _determine_ttl(self, endpoint: str, response_data: Any) -> int:
        """Determine appropriate TTL based on endpoint and response content."""
        if '/result' in endpoint:
            return self.config.cache_ttl_search
        elif any(status in str(response_data) for status in ['coming soon', 'currently unavailable']):
            return self.config.cache_ttl_coming_soon
        else:
            return self.config.cache_ttl_record

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request with rate limiting and caching."""
        params = params or {}
        url = self._build_url(endpoint)
        headers = self._build_headers()
        
        # Check cache first
        cache_key = self._build_cache_key('GET', url, params)
        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            logger.debug(f"Cache hit for {cache_key}")
            return cached_response

        # Rate limit the request
        self.rate_limiter.acquire()
        
        try:
            if self.config.log_requests:
                safe_params = self._redact_credentials(params) if self.config.redact_credentials else params
                logger.info(f"GET {url} params={safe_params}")
            
            response = self._client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            # Parse response based on content type
            response_data = self._parse_response(response)
            
            # Cache successful responses
            ttl = self._determine_ttl(endpoint, response_data)
            self.cache.set(cache_key, response_data, ttl=ttl)
            
            return response_data
            
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except httpx.RequestError as e:
            raise NetworkError(f"Network error: {e}") from e

    async def aget(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Async version of get method."""
        params = params or {}
        url = self._build_url(endpoint)
        headers = self._build_headers()
        
        # Check cache first
        cache_key = self._build_cache_key('GET', url, params)
        cached_response = await self.cache.aget(cache_key)
        if cached_response is not None:
            logger.debug(f"Cache hit for {cache_key}")
            return cached_response

        # Rate limit the request
        await self.rate_limiter.aacquire()
        
        try:
            if self.config.log_requests:
                safe_params = self._redact_credentials(params) if self.config.redact_credentials else params
                logger.info(f"GET {url} params={safe_params}")
            
            response = await self._aclient.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            # Parse response based on content type
            response_data = self._parse_response(response)
            
            # Cache successful responses
            ttl = self._determine_ttl(endpoint, response_data)
            await self.cache.aset(cache_key, response_data, ttl=ttl)
            
            return response_data
            
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except httpx.RequestError as e:
            raise NetworkError(f"Network error: {e}") from e

    def _parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Parse response based on content type."""
        content_type = response.headers.get('content-type', '')
        
        if 'application/json' in content_type:
            return response.json()
        elif 'application/xml' in content_type:
            # For now, return raw XML - Stage 6 will add proper XML parsing
            return {'xml_content': response.text, 'content_type': 'xml'}
        else:
            return {'raw_content': response.text, 'content_type': content_type}

    def _handle_http_error(self, error: httpx.HTTPStatusError) -> None:
        """Handle HTTP errors and convert to appropriate exceptions."""
        response = error.response
        
        # Try to parse error response
        try:
            if 'application/json' in response.headers.get('content-type', ''):
                error_data = response.json()
                description = error_data.get('description', str(error))
            else:
                description = response.text or str(error)
        except:
            description = str(error)
        
        if response.status_code == 429:
            # Handle rate limiting
            retry_after = response.headers.get('Retry-After')
            raise RateLimitError(description, retry_after=retry_after)
        else:
            raise TroveAPIError(
                message=description,
                status_code=response.status_code,
                response_data=error_data if 'error_data' in locals() else None
            )

    def _redact_credentials(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive information from parameters for logging."""
        safe_params = params.copy()
        if 'key' in safe_params:
            safe_params['key'] = '***redacted***'
        return safe_params

    def close(self) -> None:
        """Close HTTP clients."""
        self._client.close()

    async def aclose(self) -> None:
        """Close async HTTP client."""
        await self._aclient.aclose()
```

### 3. Rate Limiter (`trove/rate_limit.py`)

```python
import asyncio
import time
from typing import Optional
import threading
from dataclasses import dataclass

@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""
    rate: float  # tokens per second
    capacity: int  # max tokens
    tokens: float
    last_update: float
    
    def __post_init__(self):
        self.tokens = min(self.tokens, self.capacity)
        
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        now = time.time()
        elapsed = now - self.last_update
        
        # Add tokens based on elapsed time
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
        
    def time_to_tokens(self, tokens: int = 1) -> float:
        """Calculate time until requested tokens are available."""
        if self.tokens >= tokens:
            return 0.0
        needed = tokens - self.tokens
        return needed / self.rate

class RateLimiter:
    """Rate limiter using token bucket algorithm with concurrency control."""
    
    def __init__(self, rate: float, burst: int, max_concurrency: int):
        self.bucket = TokenBucket(
            rate=rate,
            capacity=burst, 
            tokens=burst,
            last_update=time.time()
        )
        self.max_concurrency = max_concurrency
        self.active_requests = 0
        self._lock = threading.Lock()
        self._async_semaphore = asyncio.Semaphore(max_concurrency)
        
    def acquire(self) -> None:
        """Acquire permission for a request (blocking)."""
        with self._lock:
            # Wait for available slot
            while self.active_requests >= self.max_concurrency:
                time.sleep(0.1)
            
            # Wait for available token
            while not self.bucket.consume():
                wait_time = self.bucket.time_to_tokens()
                time.sleep(min(wait_time, 0.1))
            
            self.active_requests += 1
            
    def release(self) -> None:
        """Release request slot."""
        with self._lock:
            self.active_requests = max(0, self.active_requests - 1)
            
    async def aacquire(self) -> None:
        """Async acquire permission for a request."""
        async with self._async_semaphore:
            # Wait for available token
            while True:
                with self._lock:
                    if self.bucket.consume():
                        break
                    wait_time = self.bucket.time_to_tokens()
                
                await asyncio.sleep(min(wait_time, 0.1))
```

### 4. Cache Backend (`trove/cache.py`)

```python
import time
import sqlite3
import json
import threading
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from pathlib import Path

class CacheBackend(ABC):
    """Abstract cache backend interface."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
        
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in cache with TTL."""
        pass
        
    @abstractmethod
    async def aget(self, key: str) -> Optional[Any]:
        """Async get value from cache."""
        pass
        
    @abstractmethod
    async def aset(self, key: str, value: Any, ttl: int) -> None:
        """Async set value in cache with TTL."""
        pass

class MemoryCache(CacheBackend):
    """In-memory cache with TTL support."""
    
    def __init__(self):
        self._cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)
        self._lock = threading.RLock()
        
    def _is_expired(self, expiry_time: float) -> bool:
        """Check if cache entry is expired."""
        return time.time() > expiry_time
        
    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        now = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items() 
            if now > expiry
        ]
        for key in expired_keys:
            self._cache.pop(key, None)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        with self._lock:
            if key not in self._cache:
                return None
                
            value, expiry_time = self._cache[key]
            if self._is_expired(expiry_time):
                del self._cache[key]
                return None
                
            return value
    
    def set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in memory cache."""
        expiry_time = time.time() + ttl
        with self._lock:
            self._cache[key] = (value, expiry_time)
            
            # Periodic cleanup (every 100 sets)
            if len(self._cache) % 100 == 0:
                self._cleanup_expired()
    
    async def aget(self, key: str) -> Optional[Any]:
        """Async get (same as sync for memory cache)."""
        return self.get(key)
        
    async def aset(self, key: str, value: Any, ttl: int) -> None:
        """Async set (same as sync for memory cache)."""
        self.set(key, value, ttl)

class SqliteCache(CacheBackend):
    """SQLite-based persistent cache."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / '.trove' / 'cache.db'
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()
        
    def _init_db(self) -> None:
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    expiry_time REAL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expiry_time 
                ON cache_entries(expiry_time)
            """)
            
    def _cleanup_expired(self, conn: sqlite3.Connection) -> None:
        """Remove expired entries."""
        now = time.time()
        conn.execute("DELETE FROM cache_entries WHERE expiry_time < ?", (now,))
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from SQLite cache."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT value, expiry_time FROM cache_entries WHERE key = ?",
                    (key,)
                )
                row = cursor.fetchone()
                
                if row is None:
                    return None
                    
                value_json, expiry_time = row
                if time.time() > expiry_time:
                    # Clean up expired entry
                    conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                    return None
                    
                return json.loads(value_json)
                
    def set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in SQLite cache."""
        expiry_time = time.time() + ttl
        value_json = json.dumps(value)
        
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cache_entries (key, value, expiry_time)
                    VALUES (?, ?, ?)
                """, (key, value_json, expiry_time))
                
                # Periodic cleanup (every 100 sets)
                if hash(key) % 100 == 0:
                    self._cleanup_expired(conn)
    
    async def aget(self, key: str) -> Optional[Any]:
        """Async get (uses sync implementation)."""
        return self.get(key)
        
    async def aset(self, key: str, value: Any, ttl: int) -> None:
        """Async set (uses sync implementation)."""
        self.set(key, value, ttl)

def create_cache(backend_type: str, **kwargs) -> CacheBackend:
    """Factory function for creating cache backends."""
    if backend_type == "memory":
        return MemoryCache()
    elif backend_type == "sqlite":
        return SqliteCache(**kwargs)
    elif backend_type == "none":
        return NoCache()
    else:
        raise ValueError(f"Unknown cache backend: {backend_type}")

class NoCache(CacheBackend):
    """No-op cache backend."""
    
    def get(self, key: str) -> Optional[Any]:
        return None
        
    def set(self, key: str, value: Any, ttl: int) -> None:
        pass
        
    async def aget(self, key: str) -> Optional[Any]:
        return None
        
    async def aset(self, key: str, value: Any, ttl: int) -> None:
        pass
```

### 5. Exception Hierarchy (`trove/exceptions.py`)

```python
from typing import Optional, Any, Dict

class TroveError(Exception):
    """Base exception for all Trove SDK errors."""
    pass

class ConfigurationError(TroveError):
    """Configuration-related errors."""
    pass

class AuthenticationError(TroveError):
    """Authentication-related errors (401)."""
    pass

class AuthorizationError(TroveError):
    """Authorization-related errors (403)."""
    pass

class ResourceNotFoundError(TroveError):
    """Resource not found errors (404)."""
    pass

class RateLimitError(TroveError):
    """Rate limiting errors (429)."""
    
    def __init__(self, message: str, retry_after: Optional[str] = None):
        super().__init__(message)
        self.retry_after = retry_after

class TroveAPIError(TroveError):
    """General API errors from Trove service."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class NetworkError(TroveError):
    """Network connectivity errors."""
    pass

class ValidationError(TroveError):
    """Parameter validation errors."""
    pass

class CacheError(TroveError):
    """Cache-related errors."""
    pass

# Convenience exception mapping
HTTP_EXCEPTION_MAP = {
    401: AuthenticationError,
    403: AuthorizationError,  
    404: ResourceNotFoundError,
    429: RateLimitError,
}

def map_http_exception(status_code: int, message: str, **kwargs) -> TroveError:
    """Map HTTP status code to appropriate exception."""
    exception_class = HTTP_EXCEPTION_MAP.get(status_code, TroveAPIError)
    return exception_class(message, **kwargs)
```

## Testing Strategy

### Unit Tests

```python
# test_transport.py
import pytest
import httpx
from unittest.mock import Mock, patch
from trove.transport import TroveTransport
from trove.config import TroveConfig
from trove.cache import MemoryCache
from trove.exceptions import RateLimitError, TroveAPIError

@pytest.fixture
def config():
    return TroveConfig(api_key="test_key")

@pytest.fixture
def transport(config):
    cache = MemoryCache()
    return TroveTransport(config, cache)

def test_build_headers(transport):
    headers = transport._build_headers()
    assert headers['X-API-KEY'] == 'test_key'
    assert 'User-Agent' in headers

def test_cache_key_generation(transport):
    key1 = transport._build_cache_key('GET', '/result', {'q': 'test', 'category': 'book'})
    key2 = transport._build_cache_key('GET', '/result', {'category': 'book', 'q': 'test'})
    assert key1 == key2  # Order shouldn't matter

@patch('httpx.Client.get')
def test_rate_limit_error_handling(mock_get, transport):
    # Mock 429 response
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.headers = {'Retry-After': '60'}
    mock_response.json.return_value = {'description': 'Rate limit exceeded'}
    
    mock_get.side_effect = httpx.HTTPStatusError(
        "Rate limit exceeded", 
        request=Mock(), 
        response=mock_response
    )
    
    with pytest.raises(RateLimitError) as exc_info:
        transport.get('/result', {'category': 'book'})
    
    assert exc_info.value.retry_after == '60'
```

### Integration Tests

```python
# test_integration.py
import pytest
import os
from trove.config import TroveConfig
from trove.transport import TroveTransport  
from trove.cache import MemoryCache

@pytest.mark.integration
class TestTroveIntegration:
    """Integration tests requiring real API key."""
    
    @pytest.fixture(scope="class")
    def config(self):
        api_key = os.environ.get('TROVE_API_KEY')
        if not api_key:
            pytest.skip("TROVE_API_KEY not set")
        return TroveConfig(api_key=api_key, rate_limit=1.0)  # Conservative rate
    
    @pytest.fixture
    def transport(self, config):
        cache = MemoryCache()
        return TroveTransport(config, cache)
    
    def test_basic_search(self, transport):
        """Test basic search functionality."""
        response = transport.get('/result', {
            'category': 'book',
            'q': 'test',
            'n': 1,
            'encoding': 'json'
        })
        
        assert 'category' in response
        assert len(response['category']) > 0
        
    def test_caching_behavior(self, transport):
        """Test that identical requests are cached."""
        params = {'category': 'book', 'q': 'cache_test', 'n': 1}
        
        # First request
        start_time = time.time()
        response1 = transport.get('/result', params)
        first_duration = time.time() - start_time
        
        # Second request (should be cached)
        start_time = time.time()
        response2 = transport.get('/result', params)  
        second_duration = time.time() - start_time
        
        assert response1 == response2
        assert second_duration < first_duration  # Cache should be faster
        
    def test_rate_limiting(self, transport):
        """Test that rate limiting works."""
        start_time = time.time()
        
        # Make multiple requests
        for i in range(3):
            transport.get('/result', {'category': 'book', 'q': f'test{i}', 'n': 1})
        
        duration = time.time() - start_time
        # Should take at least 2 seconds due to rate limiting (1 req/sec + initial)
        assert duration >= 1.5
```

## Documentation Requirements

### API Documentation

All classes and methods must have comprehensive docstrings:

```python
def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Make authenticated GET request to Trove API.
    
    Args:
        endpoint: API endpoint path (e.g., '/result', '/work/123')
        params: Query parameters as key-value pairs
        
    Returns:
        Parsed response data as dictionary
        
    Raises:
        AuthenticationError: Invalid or missing API key
        RateLimitError: Rate limit exceeded
        TroveAPIError: Other API errors
        NetworkError: Network connectivity issues
        
    Example:
        >>> transport = TroveTransport(config, cache)
        >>> response = transport.get('/result', {
        ...     'category': 'book', 
        ...     'q': 'Australian history',
        ...     'n': 10
        ... })
        >>> print(len(response['category']))
        1
    """
```

### Usage Examples

```python
# examples/basic_usage.py
from trove.config import TroveConfig
from trove.transport import TroveTransport
from trove.cache import MemoryCache

# Configure the client
config = TroveConfig.from_env()
cache = MemoryCache()
transport = TroveTransport(config, cache)

try:
    # Make a basic search
    response = transport.get('/result', {
        'category': 'book',
        'q': 'Australian history', 
        'n': 5,
        'encoding': 'json'
    })
    
    print(f"Found {response['category'][0]['records']['total']} results")
    
    for work in response['category'][0]['records']['work']:
        print(f"- {work['title']}")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    transport.close()
```

## Definition of Done

Stage 1 is complete when:

- ✅ **All components implemented** - Config, Transport, RateLimit, Cache, Exceptions
- ✅ **Basic API call working** - Can successfully call `/v3/result` 
- ✅ **Authentication working** - `X-API-KEY` header authentication
- ✅ **Rate limiting working** - Prevents 429 errors under normal usage
- ✅ **Caching working** - Identical requests served from cache
- ✅ **Error handling complete** - All documented error codes handled
- ✅ **Tests passing** - >90% coverage, integration tests with real API
- ✅ **Documentation complete** - All classes/methods documented
- ✅ **CI pipeline green** - Linting, type checking, tests pass
- ✅ **Examples working** - Basic usage examples execute successfully

## Dependencies

### Runtime Dependencies
- `httpx>=0.24.0` - HTTP client with sync/async support
- `pydantic>=2.0.0` - Data validation (for config)

### Development Dependencies  
- `pytest>=7.0.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `coverage>=7.0.0` - Code coverage
- `black>=23.0.0` - Code formatting
- `mypy>=1.0.0` - Type checking
- `ruff>=0.0.275` - Fast linting

## Performance Targets

- **Cold start time**: <500ms for first API call
- **Cached response time**: <10ms for cache hits
- **Memory usage**: <50MB for typical workload
- **Rate limit compliance**: Never exceed 2 req/sec sustained

This foundation provides a robust, well-tested base for all subsequent stages while maintaining the conservative, defensive approach required for production use.