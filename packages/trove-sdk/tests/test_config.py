"""Unit tests for TroveConfig class."""

import os
from unittest.mock import patch

import pytest

from trove.config import TroveConfig


class TestTroveConfig:
    """Test cases for TroveConfig class."""

    def test_basic_config_creation(self):
        """Test creating a basic configuration."""
        config = TroveConfig(api_key="test_key")
        assert config.api_key == "test_key"
        assert config.base_url == "https://api.trove.nla.gov.au/v3/"
        assert config.default_encoding == "json"
        assert config.rate_limit == 2.0

    def test_config_validation_success(self):
        """Test successful configuration validation."""
        config = TroveConfig(api_key="test_key")
        # Should not raise any exception
        config.validate()

    def test_config_validation_empty_api_key(self):
        """Test validation fails with empty API key."""
        # Use __post_init__ = False to bypass automatic validation
        with pytest.raises(ValueError, match="API key is required"):
            TroveConfig(api_key="")

    def test_config_validation_invalid_rate_limit(self):
        """Test validation fails with invalid rate limit."""
        with pytest.raises(ValueError, match="Rate limit must be positive"):
            TroveConfig(api_key="test", rate_limit=-1.0)

    def test_config_validation_invalid_encoding(self):
        """Test validation fails with invalid encoding."""
        with pytest.raises(ValueError, match="Default encoding must be"):
            TroveConfig(api_key="test", default_encoding="invalid")

    def test_config_validation_invalid_cache_backend(self):
        """Test validation fails with invalid cache backend."""
        with pytest.raises(ValueError, match="Cache backend must be"):
            TroveConfig(api_key="test", cache_backend="invalid")

    def test_from_env_missing_api_key(self):
        """Test from_env fails when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="TROVE_API_KEY environment variable is required"):
                # Use a non-existent path to prevent automatic .env loading
                TroveConfig.from_env(dotenv_path="/nonexistent/.env")

    def test_from_env_basic_config(self):
        """Test from_env with basic API key."""
        with patch.dict(os.environ, {'TROVE_API_KEY': 'env_test_key'}):
            config = TroveConfig.from_env()
            assert config.api_key == 'env_test_key'
            assert config.rate_limit == 2.0  # Default value

    def test_from_env_with_overrides(self):
        """Test from_env with environment variable overrides."""
        env_vars = {
            'TROVE_API_KEY': 'env_test_key',
            'TROVE_BASE_URL': 'https://custom.api.example.com',
            'TROVE_RATE_LIMIT': '5.0',
            'TROVE_BURST_LIMIT': '10',
            'TROVE_CACHE_BACKEND': 'sqlite',
            'TROVE_LOG_LEVEL': 'DEBUG',
            'TROVE_LOG_REQUESTS': 'true',
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = TroveConfig.from_env()
            assert config.api_key == 'env_test_key'
            assert config.base_url == 'https://custom.api.example.com'
            assert config.rate_limit == 5.0
            assert config.burst_limit == 10
            assert config.cache_backend == 'sqlite'
            assert config.log_level == 'DEBUG'
            assert config.log_requests is True

    def test_from_env_boolean_parsing(self):
        """Test boolean environment variable parsing."""
        test_cases = [
            ('true', True),
            ('True', True),
            ('1', True),
            ('yes', True),
            ('on', True),
            ('false', False),
            ('False', False),
            ('0', False),
            ('no', False),
            ('off', False),
        ]

        for env_value, expected in test_cases:
            env_vars = {
                'TROVE_API_KEY': 'test_key',
                'TROVE_LOG_REQUESTS': env_value,
            }

            with patch.dict(os.environ, env_vars, clear=True):
                config = TroveConfig.from_env()
                assert config.log_requests is expected, f"Failed for {env_value}"

    def test_from_env_invalid_numeric_values(self):
        """Test from_env ignores invalid numeric values."""
        env_vars = {
            'TROVE_API_KEY': 'test_key',
            'TROVE_RATE_LIMIT': 'invalid_float',
            'TROVE_BURST_LIMIT': 'invalid_int',
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = TroveConfig.from_env()
            # Should fall back to defaults when parsing fails
            assert config.rate_limit == 2.0  # Default
            assert config.burst_limit == 5   # Default

    def test_cache_db_path(self):
        """Test cache database path generation."""
        config = TroveConfig(api_key="test_key")
        path = config.get_cache_db_path()
        assert path.name == "cache.db"
        assert ".trove" in str(path)

    def test_config_edge_cases(self):
        """Test edge cases in configuration validation."""
        # Very high rate limit should trigger warning
        with pytest.raises(ValueError, match="Rate limit should not exceed"):
            TroveConfig(api_key="test", rate_limit=15.0)

        # Very high concurrency should trigger warning
        with pytest.raises(ValueError, match="Max concurrency should not exceed"):
            TroveConfig(api_key="test", max_concurrency=15)

        # Backoff times should be sensible
        with pytest.raises(ValueError, match="Max backoff must be greater than"):
            TroveConfig(api_key="test", base_backoff=10.0, max_backoff=5.0)

    def test_config_immutability_after_validation(self):
        """Test that config can be modified after creation."""
        config = TroveConfig(api_key="test_key")

        # Should be able to modify fields
        config.rate_limit = 1.5
        assert config.rate_limit == 1.5

        # But validation should catch invalid changes
        config.rate_limit = -1.0
        with pytest.raises(ValueError):
            config.validate()
