"""Test configuration and fixtures."""

import pytest
import os
from unittest.mock import Mock

from trove_mcp.server import TroveMCPServer


@pytest.fixture
def mock_trove_client():
    """Mock Trove client for testing."""
    mock_client = Mock()
    mock_client.resources = Mock()
    mock_client.search = Mock()
    mock_client.raw_search = Mock()
    return mock_client


@pytest.fixture
def test_server_config():
    """Test server configuration."""
    return {
        'rate_limit': 0.1,  # Very slow for testing
        'cache_backend': 'memory'
    }


@pytest.fixture
def mcp_server(test_server_config):
    """MCP server instance for testing."""
    # Only create if we have an API key
    if not os.environ.get('TROVE_API_KEY'):
        pytest.skip("TROVE_API_KEY not set")
    
    return TroveMCPServer(test_server_config)