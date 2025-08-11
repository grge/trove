"""Trove SDK - Python library for Trove API v3.

This library provides both synchronous and asynchronous access to Australia's 
National Library Trove digital collection through a clean, well-typed interface.

Example:
    Basic usage with environment variable:
    
    >>> import os
    >>> os.environ['TROVE_API_KEY'] = 'your_api_key_here'
    >>> 
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

__version__ = "1.0.0"

# Core components
# Cache backends
from .cache import CacheBackend, MemoryCache, NoCache, SqliteCache, SearchCacheBackend, create_cache
from .config import TroveConfig
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    CacheError,
    ConfigurationError,
    NetworkError,
    RateLimitError,
    ResourceNotFoundError,
    TroveAPIError,
    TroveError,
    ValidationError,
)

# Parameters and search
from .params import SearchParameters, ParameterBuilder, build_limits
# Rate limiting
from .rate_limit import RateLimiter, TokenBucket
# Resources
from .resources import (
    ResourceFactory,
    SearchResource, SearchResult, PaginationState,
    WorkResource, NewspaperResource, GazetteResource,
    PeopleResource, ListResource,
    NewspaperTitleResource, MagazineTitleResource, GazetteTitleResource,
    BaseResource, RecLevel, Encoding
)
from .transport import TroveTransport

__all__ = [
    # Core
    "TroveConfig",
    "TroveTransport",
    # Parameters and Search
    "SearchParameters",
    "ParameterBuilder", 
    "build_limits",
    # Resources
    "ResourceFactory",
    "SearchResource",
    "SearchResult",
    "PaginationState",
    "WorkResource",
    "NewspaperResource", 
    "GazetteResource",
    "PeopleResource",
    "ListResource",
    "NewspaperTitleResource",
    "MagazineTitleResource",
    "GazetteTitleResource",
    "BaseResource",
    "RecLevel",
    "Encoding",
    # Exceptions
    "TroveError",
    "ConfigurationError",
    "AuthenticationError",
    "AuthorizationError",
    "ResourceNotFoundError",
    "RateLimitError",
    "TroveAPIError",
    "NetworkError",
    "ValidationError",
    "CacheError",
    # Cache
    "CacheBackend",
    "MemoryCache",
    "SqliteCache",
    "SearchCacheBackend",
    "NoCache",
    "create_cache",
    # Rate limiting
    "RateLimiter",
    "TokenBucket",
    # Version
    "__version__",
]
