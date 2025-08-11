"""Exception hierarchy for Trove SDK.

This module defines all exceptions that can be raised by the Trove SDK,
providing a clear hierarchy for error handling and specific error types
for different failure modes.
"""

from typing import Any


class TroveError(Exception):
    """Base exception for all Trove SDK errors.
    
    This is the root exception class that all other Trove SDK exceptions
    inherit from. Catch this exception to handle all SDK-related errors.
    
    Example:
        >>> try:
        ...     # Some Trove SDK operation
        ...     pass
        ... except TroveError as e:
        ...     print(f"Trove SDK error: {e}")
    """
    pass


class ConfigurationError(TroveError):
    """Configuration-related errors.
    
    Raised when there are issues with SDK configuration such as missing
    or invalid configuration values.
    
    Example:
        >>> from trove.config import TroveConfig
        >>> try:
        ...     config = TroveConfig(api_key="")  # Empty API key
        ...     config.validate()
        ... except ConfigurationError as e:
        ...     print(f"Configuration error: {e}")
    """
    pass


class AuthenticationError(TroveError):
    """Authentication-related errors (HTTP 401).
    
    Raised when the API key is invalid, missing, or expired.
    Usually corresponds to HTTP 401 Unauthorized responses.
    
    Example:
        >>> # This would be raised internally by the transport layer
        >>> raise AuthenticationError("Invalid API key provided")
    """
    pass


class AuthorizationError(TroveError):
    """Authorization-related errors (HTTP 403).
    
    Raised when the API key is valid but access to the requested
    resource is forbidden. Usually corresponds to HTTP 403 Forbidden responses.
    
    Example:
        >>> # This would be raised internally by the transport layer  
        >>> raise AuthorizationError("Access to this resource is forbidden")
    """
    pass


class ResourceNotFoundError(TroveError):
    """Resource not found errors (HTTP 404).
    
    Raised when the requested resource (work, article, etc.) cannot be found.
    Usually corresponds to HTTP 404 Not Found responses.
    
    Example:
        >>> # This would be raised when requesting a non-existent work
        >>> raise ResourceNotFoundError("Work with ID 12345 not found")
    """
    pass


class RateLimitError(TroveError):
    """Rate limiting errors (HTTP 429).
    
    Raised when the rate limit has been exceeded. Contains optional
    retry_after information when provided by the server.
    
    Args:
        message: Error message
        retry_after: Optional retry-after value from server (seconds or HTTP date string)
        
    Attributes:
        retry_after: Time to wait before retrying, if provided by server
        
    Example:
        >>> try:
        ...     # Some API operation that hits rate limit
        ...     pass
        ... except RateLimitError as e:
        ...     if e.retry_after:
        ...         print(f"Rate limited. Retry after: {e.retry_after}")
    """

    def __init__(self, message: str, retry_after: str | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class TroveAPIError(TroveError):
    """General API errors from Trove service.
    
    Raised for various API errors that don't fit into more specific categories.
    Contains detailed information about the error including status code and
    response data when available.
    
    Args:
        message: Error message
        status_code: HTTP status code, if available
        response_data: Raw response data from the API, if available
        
    Attributes:
        status_code: HTTP status code from the error response
        response_data: Parsed response data from the API error
        
    Example:
        >>> try:
        ...     # Some API operation that fails
        ...     pass
        ... except TroveAPIError as e:
        ...     print(f"API error {e.status_code}: {e}")
        ...     if e.response_data:
        ...         print(f"Response: {e.response_data}")
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class NetworkError(TroveError):
    """Network connectivity errors.
    
    Raised when there are network-level issues such as connection timeouts,
    DNS resolution failures, or other network connectivity problems.
    
    Example:
        >>> try:
        ...     # Some API operation with network issues
        ...     pass
        ... except NetworkError as e:
        ...     print(f"Network error: {e}")
        ...     # Maybe implement retry logic
    """
    pass


class ValidationError(TroveError):
    """Parameter validation errors.
    
    Raised when input parameters fail validation before being sent to the API.
    This helps catch errors early and provides clear feedback about invalid inputs.
    
    Example:
        >>> # This would be raised for invalid search parameters
        >>> raise ValidationError("Invalid category: 'invalid_category'")
    """
    pass


class CacheError(TroveError):
    """Cache-related errors.
    
    Raised when there are issues with cache operations such as SQLite
    database errors, serialization failures, or other cache backend problems.
    
    Example:
        >>> try:
        ...     # Some cache operation
        ...     pass
        ... except CacheError as e:
        ...     print(f"Cache error: {e}")
        ...     # Continue without caching
    """
    pass


# Convenience exception mapping for HTTP status codes
HTTP_EXCEPTION_MAP = {
    401: AuthenticationError,
    403: AuthorizationError,
    404: ResourceNotFoundError,
    429: RateLimitError,
}


def map_http_exception(
    status_code: int,
    message: str,
    response_data: dict[str, Any] | None = None,
    **kwargs: Any
) -> TroveError:
    """Map HTTP status code to appropriate exception.
    
    This function provides a convenient way to create the appropriate
    exception type based on an HTTP status code.
    
    Args:
        status_code: HTTP status code
        message: Error message
        response_data: Optional response data from the API
        **kwargs: Additional keyword arguments for specific exception types
        
    Returns:
        Appropriate TroveError subclass instance
        
    Example:
        >>> error = map_http_exception(401, "Unauthorized")
        >>> isinstance(error, AuthenticationError)
        True
        >>> 
        >>> rate_limit_error = map_http_exception(
        ...     429, 
        ...     "Too many requests", 
        ...     retry_after="60"
        ... )
        >>> isinstance(rate_limit_error, RateLimitError)
        True
    """
    exception_class = HTTP_EXCEPTION_MAP.get(status_code, TroveAPIError)

    if exception_class == RateLimitError:
        # RateLimitError has special handling for retry_after
        retry_after = kwargs.get('retry_after')
        return exception_class(message, retry_after=retry_after)
    elif exception_class in (AuthenticationError, AuthorizationError, ResourceNotFoundError):
        # These exception types don't take additional parameters
        return exception_class(message)
    else:
        # TroveAPIError and others take status_code and response_data
        return exception_class(message, status_code=status_code, response_data=response_data)


def is_retryable_error(exception: Exception) -> bool:
    """Check if an exception represents a retryable error.
    
    Determines whether a given exception represents a temporary failure
    that might succeed if retried (e.g., network errors, rate limiting)
    vs permanent failures (e.g., authentication errors, not found errors).
    
    Args:
        exception: Exception to check
        
    Returns:
        True if the error is potentially retryable, False otherwise
        
    Example:
        >>> network_error = NetworkError("Connection timeout")
        >>> is_retryable_error(network_error)
        True
        >>> 
        >>> auth_error = AuthenticationError("Invalid API key")
        >>> is_retryable_error(auth_error)
        False
    """
    # Retryable errors: network issues, rate limiting, general API errors
    retryable_types = (NetworkError, RateLimitError, TroveAPIError)

    # Non-retryable errors: authentication, authorization, not found, validation
    non_retryable_types = (
        AuthenticationError,
        AuthorizationError,
        ResourceNotFoundError,
        ValidationError,
        ConfigurationError
    )

    if isinstance(exception, non_retryable_types):
        return False
    elif isinstance(exception, retryable_types):
        return True
    else:
        # For unknown exception types, be conservative and don't retry
        return False
