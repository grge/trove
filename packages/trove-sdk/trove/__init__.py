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
from .params import SearchParameters, build_limits
from .search import Search, SearchFilter, SearchSpec, search
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


class TroveClient:
    """High-level client providing both raw and ergonomic access to Trove API.
    
    Examples:
        # Basic setup
        client = TroveClient.from_env()
        
        # Ergonomic search
        results = (client.search()
                  .text("Australian literature")
                  .in_("book")
                  .decade("200")
                  .first_page())
                  
        # Raw search for advanced use cases
        raw_results = client.raw_search.page(
            category=['book', 'image'],
            q='Sydney',
            l_decade=['200'],
            facet=['format', 'availability']
        )
        
        # Individual record access
        work = client.resources.get_work_resource().get('123456')
    """
    
    def __init__(self, config: TroveConfig):
        self.config = config
        self.cache = create_cache(config.cache_backend)
        self.transport = TroveTransport(config, self.cache)
        
        # Raw access
        self.raw_search = SearchResource(self.transport)
        self.resources = ResourceFactory(self.transport)
        
    @classmethod
    def from_env(cls) -> 'TroveClient':
        """Create client from environment variables."""
        config = TroveConfig.from_env()
        return cls(config)
        
    @classmethod  
    def from_api_key(cls, api_key: str, **kwargs) -> 'TroveClient':
        """Create client from API key."""
        config = TroveConfig(api_key=api_key, **kwargs)
        return cls(config)
        
    def search(self) -> Search:
        """Create a new ergonomic search builder."""
        return Search(self.raw_search)
        
    def close(self):
        """Close HTTP connections."""
        self.transport.close()
        
    async def aclose(self):
        """Close async HTTP connections."""
        await self.transport.aclose()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()


__all__ = [
    # Core
    "TroveConfig",
    "TroveTransport",
    "TroveClient",
    # Parameters and Search
    "SearchParameters", 
    "build_limits",
    "Search",
    "SearchFilter",
    "SearchSpec",
    "search",
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
