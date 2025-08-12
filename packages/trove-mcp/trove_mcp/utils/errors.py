"""Error mapping utilities."""

from trove.exceptions import (
    TroveError, TroveAPIError, AuthenticationError, 
    ResourceNotFoundError, ValidationError, RateLimitError
)


def map_trove_error_to_mcp(error: TroveError) -> Exception:
    """Map Trove SDK errors to MCP errors."""
    
    if isinstance(error, AuthenticationError):
        return Exception(f"Authentication failed: {error}")
    
    elif isinstance(error, ResourceNotFoundError):
        return Exception(f"Resource not found: {error}")
    
    elif isinstance(error, ValidationError):
        return Exception(f"Invalid parameters: {error}")
    
    elif isinstance(error, RateLimitError):
        return Exception(f"Rate limit exceeded: {error}")
    
    elif isinstance(error, TroveAPIError):
        status_info = f" (HTTP {error.status_code})" if error.status_code else ""
        return Exception(f"API error: {error}{status_info}")
    
    else:
        return Exception(f"Unexpected error: {error}")