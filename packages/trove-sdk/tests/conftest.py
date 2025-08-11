"""Pytest configuration and fixtures for Trove SDK tests."""

import os
from pathlib import Path
from unittest.mock import Mock

import pytest
from dotenv import load_dotenv

from trove.cache import MemoryCache
from trove.config import TroveConfig

# Load .env file automatically for tests
# Look for .env in the repository root (3 levels up from tests/)
env_path = Path(__file__).parent.parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)


@pytest.fixture
def test_config():
    """Create a test configuration with minimal settings."""
    return TroveConfig(
        api_key="test_api_key_12345",
        rate_limit=10.0,  # Higher rate for testing
        burst_limit=10,
        max_concurrency=5,
        cache_backend="memory"
    )


@pytest.fixture
def memory_cache():
    """Create a fresh memory cache instance for testing."""
    return MemoryCache()


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client for unit tests."""
    return Mock()


@pytest.fixture
def integration_config():
    """Create config for integration tests (requires real API key)."""
    api_key = os.environ.get('TROVE_API_KEY')
    if not api_key:
        pytest.skip("TROVE_API_KEY environment variable not set")

    return TroveConfig(
        api_key=api_key,
        rate_limit=1.0,  # Be conservative for real API
        burst_limit=2,
        max_concurrency=2
    )
