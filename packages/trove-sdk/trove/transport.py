"""HTTP transport layer for Trove API.

This module provides the core HTTP transport functionality for the Trove SDK,
including authentication, rate limiting, caching, retry logic, and error handling.
"""

import logging
from typing import Any
from urllib.parse import urlencode, urljoin

import httpx

from . import __version__
from .cache import CacheBackend
from .config import TroveConfig
from .exceptions import (
    NetworkError,
    RateLimitError,
    is_retryable_error,
    map_http_exception,
)
from .rate_limit import ExponentialBackoff, RateLimiter
from .errors import get_error_handler
from .performance import get_performance_monitor, ConnectionPool, RequestOptimizer
from .logging import transport_logger

logger = logging.getLogger(__name__)


class TroveTransport:
    """HTTP transport layer for Trove API with rate limiting and caching.
    
    This class handles all HTTP communication with the Trove API, including:
    - Authentication via X-API-KEY header
    - Rate limiting to prevent API abuse
    - Response caching to reduce API calls
    - Automatic retries with exponential backoff
    - Comprehensive error handling
    
    Args:
        config: Configuration object with API settings
        cache: Cache backend for storing responses
        
    Example:
        >>> from trove import TroveConfig, TroveTransport
        >>> from trove.cache import MemoryCache
        >>> 
        >>> config = TroveConfig.from_env()
        >>> cache = MemoryCache()
        >>> transport = TroveTransport(config, cache)
        >>> 
        >>> # Make a search request
        >>> response = transport.get('/result', {
        ...     'category': 'book',
        ...     'q': 'Australian history',
        ...     'n': 5
        ... })
        >>> 
        >>> transport.close()
    """

    def __init__(self, config: TroveConfig, cache: CacheBackend):
        self.config = config
        self.cache = cache
        self.rate_limiter = RateLimiter(
            rate=config.rate_limit,
            burst=config.burst_limit,
            max_concurrency=config.max_concurrency
        )
        self.backoff = ExponentialBackoff(
            base_delay=config.base_backoff,
            max_delay=config.max_backoff,
            jitter=config.backoff_jitter
        )

        # Enhanced connection pooling
        connection_pool = ConnectionPool(
            pool_connections=config.max_concurrency,
            pool_maxsize=config.max_concurrency
        )
        pool_limits = connection_pool.configure_httpx_limits()
        
        # Configure httpx client
        self._client = httpx.Client(
            timeout=httpx.Timeout(
                connect=config.connect_timeout,
                read=config.read_timeout,
                write=config.read_timeout,
                pool=config.read_timeout
            ),
            limits=httpx.Limits(**pool_limits)
        )

        # Async client for async operations
        self._aclient = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=config.connect_timeout,
                read=config.read_timeout,
                write=config.read_timeout,
                pool=config.read_timeout
            ),
            limits=httpx.Limits(**pool_limits)
        )
        
        # Performance monitoring
        self.monitor = get_performance_monitor()

    def _build_url(self, endpoint: str) -> str:
        """Build full URL for API endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Full URL for the endpoint
        """
        # Ensure base_url ends with slash and endpoint doesn't start with slash
        # This prevents urljoin from dropping the version path component
        base_url = self.config.base_url.rstrip('/') + '/'
        endpoint = endpoint.lstrip('/')
        return urljoin(base_url, endpoint)

    def _build_headers(self) -> dict[str, str]:
        """Build request headers with authentication.
        
        Returns:
            Dictionary of HTTP headers including authentication
        """
        headers = {
            'X-API-KEY': self.config.api_key,
            'User-Agent': f'trove-sdk-python/{__version__}',
            'Accept': 'application/json' if self.config.default_encoding == 'json' else 'application/xml'
        }
        return headers

    def _build_cache_key(self, method: str, url: str, params: dict[str, Any]) -> str:
        """Build normalized cache key.
        
        Creates a consistent cache key by normalizing parameters and excluding
        sensitive information like API keys.
        
        Args:
            method: HTTP method
            url: Request URL
            params: Request parameters
            
        Returns:
            Normalized cache key string
        """
        # Exclude credentials from cache key
        cache_params = params.copy()
        cache_params.pop('key', None)  # Remove API key from cache key if present

        # Sort parameters for consistent keys
        param_str = urlencode(sorted(cache_params.items()))
        cache_key = f"{method}:{url}:{param_str}:{self.config.default_encoding}"

        return cache_key

    def _determine_ttl(self, endpoint: str, response_data: Any) -> int:
        """Determine appropriate TTL based on endpoint and response content.
        
        Different types of data have different caching lifetimes:
        - Search results: Short TTL (15 minutes)
        - Individual records: Long TTL (7 days)
        - "Coming soon" records: Very short TTL (1 hour)
        
        Args:
            endpoint: API endpoint that was called
            response_data: Response data to analyze
            
        Returns:
            TTL in seconds
        """
        if '/result' in endpoint:
            return self.config.cache_ttl_search
        elif any(status in str(response_data) for status in ['coming soon', 'currently unavailable']):
            return self.config.cache_ttl_coming_soon
        else:
            return self.config.cache_ttl_record

    def _parse_response(self, response: httpx.Response) -> dict[str, Any]:
        """Parse response based on content type.
        
        Args:
            response: HTTP response object
            
        Returns:
            Parsed response data
        """
        content_type = response.headers.get('content-type', '')

        if 'application/json' in content_type:
            return response.json()
        elif 'application/xml' in content_type:
            # For now, return raw XML - Stage 6 will add proper XML parsing
            return {'xml_content': response.text, 'content_type': 'xml'}
        else:
            return {'raw_content': response.text, 'content_type': content_type}

    def _handle_http_error(self, error: httpx.HTTPStatusError) -> None:
        """Handle HTTP errors and convert to appropriate exceptions.
        
        Args:
            error: HTTP status error from httpx
            
        Raises:
            Appropriate TroveError subclass based on status code
        """
        response = error.response

        # Try to parse error response
        try:
            if 'application/json' in response.headers.get('content-type', ''):
                error_data = response.json()
                description = error_data.get('description', str(error))
            else:
                description = response.text or str(error)
        except Exception:
            description = str(error)

        # Handle rate limiting specially
        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After')
            raise RateLimitError(description, retry_after=retry_after)
        else:
            # Use exception mapping for other status codes
            exception = map_http_exception(
                status_code=response.status_code,
                message=description,
                response_data=error_data if 'error_data' in locals() else None
            )
            raise exception

    def _redact_credentials(self, params: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive information from parameters for logging.
        
        Args:
            params: Request parameters
            
        Returns:
            Parameters with sensitive information redacted
        """
        safe_params = params.copy()
        if 'key' in safe_params:
            safe_params['key'] = '***redacted***'
        return safe_params

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make GET request with rate limiting and caching.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters as key-value pairs
            
        Returns:
            Parsed response data as dictionary
            
        Raises:
            AuthenticationError: Invalid or missing API key
            AuthorizationError: Access denied
            ResourceNotFoundError: Requested resource not found
            RateLimitError: Rate limit exceeded
            TroveAPIError: Other API errors
            NetworkError: Network connectivity issues
            
        Example:
            >>> response = transport.get('/result', {
            ...     'category': 'book', 
            ...     'q': 'Australian history',
            ...     'n': 10
            ... })
        """
        params = params or {}
        url = self._build_url(endpoint)
        headers = self._build_headers()

        # Optimize parameters for performance
        params = RequestOptimizer.optimize_search_params(params)
        
        # Check cache first
        cache_key = self._build_cache_key('GET', url, params)
        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            logger.debug(f"Cache hit for {cache_key}")
            self.monitor.record_cache_hit()
            return cached_response
        
        self.monitor.record_cache_miss()

        # Retry loop with exponential backoff
        last_exception = None
        request_id = f"{endpoint}_{id(params)}"
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Rate limit the request
                if not self.rate_limiter.acquire(timeout=30.0):
                    self.monitor.record_rate_limit_delay()
                    raise RateLimitError("Timeout waiting for rate limit permission")

                try:
                    if self.config.log_requests:
                        safe_params = self._redact_credentials(params) if self.config.redact_credentials else params
                        transport_logger.info(
                            f"HTTP GET request",
                            endpoint=endpoint,
                            url=url,
                            params=safe_params,
                            attempt=attempt + 1,
                            request_id=request_id
                        )

                    # Start timing the request
                    self.monitor.start_request(request_id)
                    response = self._client.get(url, params=params, headers=headers)
                    response.raise_for_status()

                    # Parse response based on content type
                    response_data = self._parse_response(response)

                    # End timing and record successful request
                    self.monitor.end_request(request_id)

                    # Cache successful responses
                    ttl = self._determine_ttl(endpoint, response_data)
                    self.cache.set(cache_key, response_data, ttl=ttl)

                    return response_data

                finally:
                    self.rate_limiter.release()

            except httpx.HTTPStatusError as e:
                try:
                    self._handle_http_error(e)
                except Exception as parsed_error:
                    # Enhance error with context
                    context = {
                        'endpoint': endpoint,
                        'params': params,
                        'operation': 'HTTP GET request',
                        'attempt': attempt + 1,
                        'max_retries': self.config.max_retries
                    }
                    
                    enhanced_error = get_error_handler().wrap_api_error(parsed_error, context)
                    last_exception = enhanced_error
                    
                    # Record error for monitoring
                    self.monitor.record_error()

                    # Don't retry non-retryable errors
                    if not is_retryable_error(enhanced_error):
                        raise enhanced_error

                    # Don't retry on last attempt
                    if attempt == self.config.max_retries:
                        raise enhanced_error

                    # Sleep before retry
                    self.backoff.sleep(attempt)

            except httpx.RequestError as e:
                network_error = NetworkError(f"Network error: {e}")
                
                # Enhance error with context
                context = {
                    'endpoint': endpoint,
                    'params': params,
                    'operation': 'HTTP GET request',
                    'attempt': attempt + 1,
                    'max_retries': self.config.max_retries
                }
                
                enhanced_error = get_error_handler().wrap_api_error(network_error, context)
                last_exception = enhanced_error
                
                # Record error for monitoring
                self.monitor.record_error()

                # Don't retry on last attempt
                if attempt == self.config.max_retries:
                    raise enhanced_error

                # Sleep before retry
                self.backoff.sleep(attempt)

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        else:
            raise NetworkError("All retry attempts failed")

    async def aget(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Async version of get method.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters as key-value pairs
            
        Returns:
            Parsed response data as dictionary
            
        Raises:
            Same exceptions as get() method
            
        Example:
            >>> response = await transport.aget('/result', {
            ...     'category': 'book', 
            ...     'q': 'Australian history',
            ...     'n': 10
            ... })
        """
        params = params or {}
        url = self._build_url(endpoint)
        headers = self._build_headers()

        # Check cache first
        cache_key = self._build_cache_key('GET', url, params)
        cached_response = await self.cache.aget(cache_key)
        if cached_response is not None:
            logger.debug(f"Cache hit for {cache_key}")
            return cached_response

        # Retry loop with exponential backoff
        last_exception = None
        for attempt in range(self.config.max_retries + 1):
            try:
                # Rate limit the request
                if not await self.rate_limiter.aacquire(timeout=30.0):
                    raise RateLimitError("Timeout waiting for rate limit permission")

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

                finally:
                    self.rate_limiter.arelease()

            except httpx.HTTPStatusError as e:
                try:
                    self._handle_http_error(e)
                except Exception as parsed_error:
                    # Enhance error with context
                    context = {
                        'endpoint': endpoint,
                        'params': params,
                        'operation': 'Async HTTP GET request',
                        'attempt': attempt + 1,
                        'max_retries': self.config.max_retries
                    }
                    
                    enhanced_error = get_error_handler().wrap_api_error(parsed_error, context)
                    last_exception = enhanced_error

                    # Don't retry non-retryable errors
                    if not is_retryable_error(enhanced_error):
                        raise enhanced_error

                    # Don't retry on last attempt
                    if attempt == self.config.max_retries:
                        raise enhanced_error

                    # Sleep before retry
                    await self.backoff.async_sleep(attempt)

            except httpx.RequestError as e:
                network_error = NetworkError(f"Network error: {e}")
                
                # Enhance error with context
                context = {
                    'endpoint': endpoint,
                    'params': params,
                    'operation': 'Async HTTP GET request',
                    'attempt': attempt + 1,
                    'max_retries': self.config.max_retries
                }
                
                enhanced_error = get_error_handler().wrap_api_error(network_error, context)
                last_exception = enhanced_error

                # Don't retry on last attempt
                if attempt == self.config.max_retries:
                    raise enhanced_error

                # Sleep before retry
                await self.backoff.async_sleep(attempt)

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        else:
            raise NetworkError("All retry attempts failed")

    def close(self) -> None:
        """Close HTTP clients.
        
        Should be called when the transport is no longer needed to clean up
        connections and resources.
        
        Example:
            >>> transport = TroveTransport(config, cache)
            >>> try:
            ...     # Use transport
            ...     pass
            ... finally:
            ...     transport.close()
        """
        self._client.close()

    async def aclose(self) -> None:
        """Close async HTTP client.
        
        Should be called when the async transport is no longer needed to clean up
        connections and resources.
        
        Example:
            >>> transport = TroveTransport(config, cache)
            >>> try:
            ...     # Use async transport
            ...     pass
            ... finally:
            ...     await transport.aclose()
        """
        await self._aclient.aclose()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.aclose()
