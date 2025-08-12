"""Type stubs for trove.client module."""

from typing import Optional
from .config import TroveConfig
from .cache import CacheBackend
from .search import Search
from .resources.search import SearchResource
from .resources.work import WorkResource
from .resources.article import ArticleResource
from .resources.people import PeopleResource
from .resources.list import ListResource

class TroveClient:
    """Main client for accessing Trove API."""
    
    config: TroveConfig
    
    def __init__(
        self, 
        config: TroveConfig, 
        cache: Optional[CacheBackend] = None
    ) -> None: ...
    
    @classmethod
    def from_env(cls, cache: Optional[CacheBackend] = None) -> TroveClient: ...
    
    def search(self) -> Search: ...
    
    @property
    def raw_search(self) -> SearchResource: ...
    
    @property 
    def work(self) -> WorkResource: ...
    
    @property
    def newspaper(self) -> ArticleResource: ...
    
    @property
    def gazette(self) -> ArticleResource: ...
    
    @property
    def people(self) -> PeopleResource: ...
    
    @property
    def list(self) -> ListResource: ...
    
    def close(self) -> None: ...
    
    async def aclose(self) -> None: ...
    
    def __enter__(self) -> TroveClient: ...
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
    
    async def __aenter__(self) -> TroveClient: ...
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...