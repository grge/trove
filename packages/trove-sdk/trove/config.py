"""Configuration management for Trove API client."""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class TroveConfig:
    """Configuration for Trove API client.
    
    This class manages all configuration settings for the Trove SDK, including
    authentication, rate limiting, caching, and other operational parameters.
    
    Args:
        api_key: Trove API key for authentication
        base_url: Base URL for Trove API (default: https://api.trove.nla.gov.au/v3)
        default_encoding: Default response encoding (json or xml)
        rate_limit: Maximum requests per second (conservative default: 2.0)
        burst_limit: Maximum burst capacity for token bucket
        max_concurrency: Maximum concurrent requests
        max_retries: Maximum number of retry attempts
        base_backoff: Base backoff time in seconds for retries
        max_backoff: Maximum backoff time in seconds
        backoff_jitter: Whether to add jitter to backoff times
        cache_backend: Cache backend type ("memory", "sqlite", "none")
        cache_ttl_search: TTL for search results in seconds
        cache_ttl_record: TTL for individual records in seconds
        cache_ttl_coming_soon: TTL for "coming soon" records in seconds
        connect_timeout: Connection timeout in seconds
        read_timeout: Read timeout in seconds
        log_level: Logging level
        log_requests: Whether to log requests
        redact_credentials: Whether to redact credentials in logs
        
    Example:
        >>> config = TroveConfig(api_key="your_key_here")
        >>> config.validate()
        
        >>> # From environment variables
        >>> config = TroveConfig.from_env()
    """

    # Authentication
    api_key: str

    # API Settings
    base_url: str = "https://api.trove.nla.gov.au/v3/"
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
    def from_env(cls, dotenv_path: str | Path | None = None) -> 'TroveConfig':
        """Create config from environment variables with automatic .env loading.
        
        Automatically loads environment variables from .env files in this order:
        1. Current directory (.env)
        2. Parent directories (searching up to 3 levels for .env)
        3. Specific path if dotenv_path is provided
        
        Environment variables:
        - TROVE_API_KEY (required): API key for authentication
        - TROVE_BASE_URL: Base URL for API (optional)
        - TROVE_RATE_LIMIT: Rate limit in requests per second (optional)
        - TROVE_BURST_LIMIT: Burst limit for token bucket (optional)
        - TROVE_MAX_CONCURRENCY: Maximum concurrent requests (optional)
        - TROVE_CACHE_BACKEND: Cache backend type (optional)
        - TROVE_CONNECT_TIMEOUT: Connection timeout in seconds (optional)
        - TROVE_READ_TIMEOUT: Read timeout in seconds (optional)
        - TROVE_LOG_LEVEL: Logging level (optional)
        - TROVE_LOG_REQUESTS: Whether to log requests (optional)
        
        Args:
            dotenv_path: Specific path to .env file (optional)
        
        Returns:
            Configured TroveConfig instance
            
        Raises:
            ValueError: If TROVE_API_KEY is not set
            
        Example:
            >>> # Automatically loads from .env files
            >>> config = TroveConfig.from_env()
            >>> 
            >>> # Load from specific path
            >>> config = TroveConfig.from_env('/path/to/.env')
        """
        # Load .env files automatically
        if dotenv_path:
            load_dotenv(dotenv_path)
        else:
            # Try to find .env file in current directory or parent directories
            current_dir = Path.cwd()
            env_paths = [
                current_dir / '.env',
                current_dir.parent / '.env', 
                current_dir.parent.parent / '.env',
                current_dir.parent.parent.parent / '.env'  # Up to 3 levels
            ]
            
            for env_path in env_paths:
                if env_path.exists():
                    load_dotenv(env_path)
                    break
        api_key = os.environ.get('TROVE_API_KEY')
        if not api_key:
            raise ValueError(
                "TROVE_API_KEY environment variable is required. "
                "Get your API key at: https://trove.nla.gov.au/about/create-something/using-api"
            )

        # Helper function to parse boolean environment variables
        def parse_bool(value: str | None) -> bool | None:
            if value is None:
                return None
            return value.lower() in ('true', '1', 'yes', 'on')

        # Helper function to parse float environment variables
        def parse_float(value: str | None) -> float | None:
            if value is None:
                return None
            try:
                return float(value)
            except ValueError:
                return None

        # Helper function to parse int environment variables
        def parse_int(value: str | None) -> int | None:
            if value is None:
                return None
            try:
                return int(value)
            except ValueError:
                return None

        # Build config from environment with fallbacks to defaults
        config_kwargs = {'api_key': api_key}

        # Optional string parameters
        for env_var, field_name in [
            ('TROVE_BASE_URL', 'base_url'),
            ('TROVE_DEFAULT_ENCODING', 'default_encoding'),
            ('TROVE_CACHE_BACKEND', 'cache_backend'),
            ('TROVE_LOG_LEVEL', 'log_level'),
        ]:
            value = os.environ.get(env_var)
            if value is not None:
                config_kwargs[field_name] = value

        # Optional float parameters
        for env_var, field_name in [
            ('TROVE_RATE_LIMIT', 'rate_limit'),
            ('TROVE_BASE_BACKOFF', 'base_backoff'),
            ('TROVE_MAX_BACKOFF', 'max_backoff'),
            ('TROVE_CONNECT_TIMEOUT', 'connect_timeout'),
            ('TROVE_READ_TIMEOUT', 'read_timeout'),
        ]:
            value = parse_float(os.environ.get(env_var))
            if value is not None:
                config_kwargs[field_name] = value

        # Optional int parameters
        for env_var, field_name in [
            ('TROVE_BURST_LIMIT', 'burst_limit'),
            ('TROVE_MAX_CONCURRENCY', 'max_concurrency'),
            ('TROVE_MAX_RETRIES', 'max_retries'),
            ('TROVE_CACHE_TTL_SEARCH', 'cache_ttl_search'),
            ('TROVE_CACHE_TTL_RECORD', 'cache_ttl_record'),
            ('TROVE_CACHE_TTL_COMING_SOON', 'cache_ttl_coming_soon'),
        ]:
            value = parse_int(os.environ.get(env_var))
            if value is not None:
                config_kwargs[field_name] = value

        # Optional boolean parameters
        for env_var, field_name in [
            ('TROVE_BACKOFF_JITTER', 'backoff_jitter'),
            ('TROVE_LOG_REQUESTS', 'log_requests'),
            ('TROVE_REDACT_CREDENTIALS', 'redact_credentials'),
        ]:
            value = parse_bool(os.environ.get(env_var))
            if value is not None:
                config_kwargs[field_name] = value

        return cls(**config_kwargs)

    def validate(self) -> None:
        """Validate configuration values.
        
        Raises:
            ValueError: If any configuration values are invalid
            
        Example:
            >>> config = TroveConfig(api_key="test")
            >>> config.validate()  # Raises no exception
            >>> 
            >>> bad_config = TroveConfig(api_key="", rate_limit=-1.0)
            >>> bad_config.validate()  # Raises ValueError
        """
        errors = []

        # API key validation
        if not self.api_key or not self.api_key.strip():
            errors.append("API key is required and cannot be empty")

        # URL validation
        if not self.base_url or not self.base_url.strip():
            errors.append("Base URL is required and cannot be empty")
        elif not self.base_url.startswith(('http://', 'https://')):
            errors.append("Base URL must start with http:// or https://")

        # Encoding validation
        if self.default_encoding not in ('json', 'xml'):
            errors.append("Default encoding must be 'json' or 'xml'")

        # Rate limiting validation
        if self.rate_limit <= 0:
            errors.append("Rate limit must be positive")
        if self.rate_limit > 10:
            errors.append("Rate limit should not exceed 10 requests per second (be respectful)")
        if self.burst_limit <= 0:
            errors.append("Burst limit must be positive")
        if self.max_concurrency <= 0:
            errors.append("Max concurrency must be positive")
        if self.max_concurrency > 10:
            errors.append("Max concurrency should not exceed 10 (be respectful)")

        # Retry validation
        if self.max_retries < 0:
            errors.append("Max retries cannot be negative")
        if self.max_retries > 10:
            errors.append("Max retries should not exceed 10")
        if self.base_backoff <= 0:
            errors.append("Base backoff must be positive")
        if self.max_backoff <= 0:
            errors.append("Max backoff must be positive")
        if self.max_backoff < self.base_backoff:
            errors.append("Max backoff must be greater than or equal to base backoff")

        # Cache validation
        if self.cache_backend not in ('memory', 'sqlite', 'none'):
            errors.append("Cache backend must be 'memory', 'sqlite', or 'none'")
        if self.cache_ttl_search <= 0:
            errors.append("Cache TTL for search must be positive")
        if self.cache_ttl_record <= 0:
            errors.append("Cache TTL for records must be positive")
        if self.cache_ttl_coming_soon <= 0:
            errors.append("Cache TTL for coming soon records must be positive")

        # Timeout validation
        if self.connect_timeout <= 0:
            errors.append("Connect timeout must be positive")
        if self.read_timeout <= 0:
            errors.append("Read timeout must be positive")
        if self.connect_timeout > 60:
            errors.append("Connect timeout should not exceed 60 seconds")
        if self.read_timeout > 300:
            errors.append("Read timeout should not exceed 300 seconds")

        # Log level validation
        valid_log_levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"Log level must be one of: {', '.join(valid_log_levels)}")

        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))

    def get_cache_db_path(self) -> Path:
        """Get path for SQLite cache database.
        
        Returns:
            Path to SQLite cache file
            
        Example:
            >>> config = TroveConfig(api_key="test")
            >>> path = config.get_cache_db_path()
            >>> print(path)
            /home/user/.trove/cache.db
        """
        cache_dir = Path.home() / '.trove'
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / 'cache.db'

    def __post_init__(self) -> None:
        """Post-initialization validation."""
        # Automatically validate configuration when created
        self.validate()
