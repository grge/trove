"""Resource modules for Trove API endpoints."""

from typing import Dict

from .search import SearchResource, SearchResult, PaginationState
from .base import BaseResource, RecLevel, Encoding
from .work import WorkResource
from .article import ArticleResource, NewspaperResource, GazetteResource
from .people import PeopleResource  
from .list import ListResource
from .titles import (
    BaseTitleResource, 
    NewspaperTitleResource, 
    MagazineTitleResource, 
    GazetteTitleResource
)
from ..transport import TroveTransport


class ResourceFactory:
    """Factory for creating resource instances."""
    
    def __init__(self, transport: TroveTransport):
        """Initialize resource factory.
        
        Args:
            transport: Transport layer for API communication
        """
        self.transport = transport
        self._resources: Dict[str, BaseResource] = {}
        
    def get_search_resource(self) -> SearchResource:
        """Get search resource instance."""
        if 'search' not in self._resources:
            self._resources['search'] = SearchResource(self.transport)
        return self._resources['search']
        
    def get_work_resource(self) -> WorkResource:
        """Get work resource instance."""
        if 'work' not in self._resources:
            self._resources['work'] = WorkResource(self.transport)
        return self._resources['work']
        
    def get_newspaper_resource(self) -> NewspaperResource:
        """Get newspaper article resource instance."""
        if 'newspaper' not in self._resources:
            self._resources['newspaper'] = NewspaperResource(self.transport)
        return self._resources['newspaper']
        
    def get_gazette_resource(self) -> GazetteResource:
        """Get gazette article resource instance."""
        if 'gazette' not in self._resources:
            self._resources['gazette'] = GazetteResource(self.transport)
        return self._resources['gazette']
        
    def get_people_resource(self) -> PeopleResource:
        """Get people/organization resource instance."""
        if 'people' not in self._resources:
            self._resources['people'] = PeopleResource(self.transport)
        return self._resources['people']
        
    def get_list_resource(self) -> ListResource:
        """Get list resource instance."""
        if 'list' not in self._resources:
            self._resources['list'] = ListResource(self.transport)
        return self._resources['list']
        
    def get_newspaper_title_resource(self) -> NewspaperTitleResource:
        """Get newspaper title resource instance."""
        if 'newspaper_title' not in self._resources:
            self._resources['newspaper_title'] = NewspaperTitleResource(self.transport)
        return self._resources['newspaper_title']
        
    def get_magazine_title_resource(self) -> MagazineTitleResource:
        """Get magazine title resource instance."""
        if 'magazine_title' not in self._resources:
            self._resources['magazine_title'] = MagazineTitleResource(self.transport)
        return self._resources['magazine_title']
        
    def get_gazette_title_resource(self) -> GazetteTitleResource:
        """Get gazette title resource instance."""
        if 'gazette_title' not in self._resources:
            self._resources['gazette_title'] = GazetteTitleResource(self.transport)
        return self._resources['gazette_title']


# Convenience exports
__all__ = [
    # Base classes and enums
    'BaseResource', 'RecLevel', 'Encoding',
    
    # Resource classes
    'ResourceFactory',
    'SearchResource', 'SearchResult', 'PaginationState',
    'WorkResource', 
    'ArticleResource', 'NewspaperResource', 'GazetteResource', 
    'PeopleResource',
    'ListResource',
    'BaseTitleResource', 'NewspaperTitleResource', 'MagazineTitleResource', 'GazetteTitleResource'
]
