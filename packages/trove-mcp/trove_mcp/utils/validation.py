"""Input validation utilities for MCP tools."""

import os
from typing import Dict, Any


def validate_environment():
    """Validate that required environment variables are set."""
    required_vars = ['TROVE_API_KEY']
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(
            f"Required environment variables not set: {', '.join(missing_vars)}"
        )


def validate_search_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize search parameters."""
    # Add any search-specific validation here
    return params