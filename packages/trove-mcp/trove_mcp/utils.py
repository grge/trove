"""
Utility functions for the Trove MCP Server.

This module consolidates utility functions for error handling, validation,
and other common operations used throughout the server.
"""

import os
import logging
from typing import Dict, Any, List, Optional

from trove.exceptions import (
    TroveError, TroveAPIError, AuthenticationError, 
    ResourceNotFoundError, ValidationError, RateLimitError
)

logger = logging.getLogger(__name__)


def validate_environment():
    """
    Validate that required environment variables are set.
    
    Raises:
        ValueError: If TROVE_API_KEY is not set
    """
    required_vars = ['TROVE_API_KEY']
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(
            f"Required environment variables not set: {', '.join(missing_vars)}"
        )


def map_trove_error_to_mcp(error: TroveError) -> Exception:
    """
    Map Trove SDK errors to appropriate MCP errors.
    
    This function provides consistent error mapping from Trove SDK exceptions
    to standard MCP-compatible exceptions with descriptive messages.
    
    Args:
        error: Trove SDK error to map
        
    Returns:
        Exception with appropriate error message for MCP clients
    """
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


def validate_search_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize search parameters.
    
    This function performs basic validation on search parameters to ensure
    they are within acceptable ranges and formats.
    
    Args:
        params: Raw search parameters
        
    Returns:
        Validated and normalized parameters
        
    Raises:
        ValueError: If parameters are invalid
    """
    validated = params.copy()
    
    # Validate page_size
    if 'page_size' in validated:
        page_size = validated['page_size']
        if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
            raise ValueError("page_size must be an integer between 1 and 100")
    
    # Validate categories
    if 'categories' in validated:
        valid_categories = {
            'book', 'newspaper', 'image', 'people', 'list', 
            'magazine', 'music', 'map', 'diary', 'research'
        }
        categories = validated['categories']
        if not isinstance(categories, list):
            raise ValueError("categories must be a list")
        
        invalid_categories = set(categories) - valid_categories
        if invalid_categories:
            raise ValueError(f"Invalid categories: {', '.join(invalid_categories)}")
    
    # Validate record_level
    if 'record_level' in validated:
        if validated['record_level'] not in ['brief', 'full']:
            raise ValueError("record_level must be 'brief' or 'full'")
    
    # Validate sort_by
    if 'sort_by' in validated:
        valid_sorts = ['relevance', 'date_asc', 'date_desc']
        if validated['sort_by'] not in valid_sorts:
            raise ValueError(f"sort_by must be one of: {', '.join(valid_sorts)}")
    
    return validated


def validate_record_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate parameters for individual record retrieval.
    
    Args:
        params: Raw record parameters
        
    Returns:
        Validated parameters
        
    Raises:
        ValueError: If parameters are invalid
    """
    validated = params.copy()
    
    # Validate record_id
    if 'record_id' in validated:
        record_id = validated['record_id']
        if not isinstance(record_id, str) or not record_id.strip():
            raise ValueError("record_id must be a non-empty string")
        validated['record_id'] = record_id.strip()
    
    # Validate record_level
    if 'record_level' in validated:
        if validated['record_level'] not in ['brief', 'full']:
            raise ValueError("record_level must be 'brief' or 'full'")
    
    # Validate include_fields
    if 'include_fields' in validated and validated['include_fields'] is not None:
        include_fields = validated['include_fields']
        if isinstance(include_fields, str):
            validated['include_fields'] = [include_fields]
        elif not isinstance(include_fields, list):
            raise ValueError("include_fields must be a string or list of strings")
    
    return validated


def get_category_info() -> List[Dict[str, Any]]:
    """
    Get information about available Trove search categories.
    
    Returns:
        List of category information dictionaries
    """
    return [
        {
            "code": "book",
            "name": "Books",
            "description": "Books and other published works",
            "supported_filters": ["decade", "year", "format", "language", "online"]
        },
        {
            "code": "newspaper",
            "name": "Newspapers",
            "description": "Newspaper articles",
            "supported_filters": ["decade", "year", "state", "title", "illustrated"]
        },
        {
            "code": "image",
            "name": "Images",
            "description": "Images and photographs",
            "supported_filters": ["decade", "year", "format", "online"]
        },
        {
            "code": "people",
            "name": "People",
            "description": "People and organizations",
            "supported_filters": ["format"]
        },
        {
            "code": "list",
            "name": "Lists",
            "description": "User-created lists",
            "supported_filters": []
        },
        {
            "code": "magazine",
            "name": "Magazines",
            "description": "Magazine and journal articles",
            "supported_filters": ["decade", "year", "title"]
        },
        {
            "code": "music",
            "name": "Music",
            "description": "Musical works",
            "supported_filters": ["decade", "year", "format"]
        },
        {
            "code": "map",
            "name": "Maps",
            "description": "Maps and geographical materials",
            "supported_filters": ["decade", "year", "format"]
        }
    ]


def safe_get_attribute(obj: Any, attr: str, default: Any = None) -> Any:
    """
    Safely get an attribute from an object with fallback.
    
    This handles both model objects and dict-like objects.
    
    Args:
        obj: Object to get attribute from
        attr: Attribute name
        default: Default value if attribute not found
        
    Returns:
        Attribute value or default
    """
    if hasattr(obj, attr):
        return getattr(obj, attr)
    elif hasattr(obj, 'get') and callable(obj.get):
        return obj.get(attr, default)
    else:
        return default


def format_error_message(error: Exception, context: str = "") -> str:
    """
    Format an error message for consistent logging and reporting.
    
    Args:
        error: Exception to format
        context: Additional context about where the error occurred
        
    Returns:
        Formatted error message
    """
    if context:
        return f"{context}: {str(error)}"
    return str(error)


def log_tool_call(tool_name: str, arguments: Dict[str, Any], success: bool = True):
    """
    Log a tool call for debugging and monitoring.
    
    Args:
        tool_name: Name of the tool called
        arguments: Arguments passed to the tool
        success: Whether the call was successful
    """
    # Sanitize sensitive information from logs
    safe_args = {}
    for key, value in arguments.items():
        if key.lower() in ['api_key', 'token', 'password']:
            safe_args[key] = "[REDACTED]"
        elif isinstance(value, str) and len(value) > 100:
            safe_args[key] = value[:97] + "..."
        else:
            safe_args[key] = value
    
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"Tool call {tool_name} {status}: {safe_args}")