"""Ergonomic search interface for Trove API v3.

This module provides a fluent, immutable search builder API that makes common
research workflows more intuitive while maintaining full access to the 
underlying API power.
"""

from __future__ import annotations
from typing import Dict, Any, List, Union, Optional, Iterator, AsyncIterator
from dataclasses import dataclass, field, replace
import copy

from .params import SearchParameters, SortBy, RecLevel
from .resources.search import SearchResource, SearchResult
from .exceptions import ValidationError, TroveAPIError


@dataclass(frozen=True)
class SearchFilter:
    """Immutable search filter representation."""
    param_name: str
    values: List[str]
    operator: str = "eq"  # Future: support for other operators


@dataclass(frozen=True) 
class SearchSpec:
    """Immutable search specification."""
    categories: List[str] = field(default_factory=list)
    query: Optional[str] = None
    filters: List[SearchFilter] = field(default_factory=list)
    page_size: int = 20
    sort_by: SortBy = SortBy.RELEVANCE
    record_level: RecLevel = RecLevel.BRIEF
    include_fields: List[str] = field(default_factory=list)
    facets: List[str] = field(default_factory=list)
    bulk_harvest: bool = False
    
    def to_parameters(self) -> SearchParameters:
        """Convert to raw SearchParameters object."""
        params = SearchParameters()
        
        # Basic parameters
        params.category = self.categories
        params.q = self.query
        params.n = self.page_size
        params.sortby = self.sort_by
        params.reclevel = self.record_level
        params.bulkHarvest = self.bulk_harvest
        params.include = self.include_fields
        params.facet = self.facets
        
        # Apply filters
        for filter_spec in self.filters:
            # Map filter parameter names to SearchParameters attributes
            attr_name = filter_spec.param_name.replace('-', '_')
            if hasattr(params, attr_name):
                current_value = getattr(params, attr_name)
                if isinstance(current_value, list):
                    # Extend the list with new values
                    setattr(params, attr_name, current_value + filter_spec.values)
                else:
                    # For single-value boolean fields, use the first value
                    if attr_name in ['l_firstAustralians', 'l_culturalSensitivity', 'l_australian', 'l_contribcollection']:
                        setattr(params, attr_name, filter_spec.values[0] if filter_spec.values else None)
                    else:
                        setattr(params, attr_name, filter_spec.values)
            else:
                # Store in otherLimits for unknown parameters
                api_name = filter_spec.param_name
                params.otherLimits[api_name] = ','.join(filter_spec.values)
                
        return params


class Search:
    """Fluent, immutable search builder for Trove API.
    
    This class provides an ergonomic interface for building search queries
    while maintaining full access to the underlying API power.
    
    Examples:
        # Basic search
        search = (Search(search_resource)
                 .text("Australian history")
                 .in_("book")
                 .page_size(50))
        
        # Filtered search  
        search = (Search(search_resource)
                 .text("federation")
                 .in_("newspaper")
                 .decade("190")
                 .state("NSW", "VIC")
                 .illustrated()
                 .sort_by("date_desc"))
                 
        # Research workflow
        for record in search.records():
            print(f"Found: {record.get('title', record.get('heading'))}")
            if some_condition:
                break
    """
    
    def __init__(self, search_resource: SearchResource, spec: Optional[SearchSpec] = None):
        self._search_resource = search_resource
        self._spec = spec or SearchSpec()
        
    # Core search building methods
    
    def text(self, query: str) -> Search:
        """Set the search query text.
        
        Args:
            query: Search query with optional field indexes (e.g. "title:history")
            
        Returns:
            New Search instance with query set
            
        Examples:
            search.text("Australian literature")
            search.text('title:"Prime Ministers" AND creator:Smith')
            search.text("subject:politics NOT decade:199*")
        """
        new_spec = replace(self._spec, query=query)
        return Search(self._search_resource, new_spec)
        
    def in_(self, *categories: str) -> Search:
        """Set search categories.
        
        Args:
            *categories: Category codes (book, newspaper, image, etc.)
            
        Returns:
            New Search instance with categories set
            
        Examples:
            search.in_("book")
            search.in_("book", "image", "magazine")
            search.in_("all")  # Search all categories
        """
        # Validate categories
        valid_categories = {
            'all', 'book', 'diary', 'image', 'list', 
            'magazine', 'music', 'newspaper', 'people', 'research'
        }
        invalid = set(categories) - valid_categories
        if invalid:
            raise ValidationError(f"Invalid categories: {', '.join(invalid)}")
            
        new_spec = replace(self._spec, categories=list(categories))
        return Search(self._search_resource, new_spec)
        
    def page_size(self, n: int) -> Search:
        """Set number of results per page.
        
        Args:
            n: Number of results (1-100)
            
        Returns:
            New Search instance with page size set
        """
        if n < 0 or n > 100:
            raise ValidationError("Page size must be between 0 and 100")
            
        new_spec = replace(self._spec, page_size=n)
        return Search(self._search_resource, new_spec)
        
    def sort_by(self, sort_order: Union[str, SortBy]) -> Search:
        """Set sort order for results.
        
        Args:
            sort_order: Sort order (relevance, date_desc, date_asc)
            
        Returns:
            New Search instance with sort order set
        """
        if isinstance(sort_order, str):
            # Map friendly names to enum values
            sort_mapping = {
                'relevance': SortBy.RELEVANCE,
                'date_desc': SortBy.DATE_DESC,
                'date_asc': SortBy.DATE_ASC,
                'newest': SortBy.DATE_DESC,
                'oldest': SortBy.DATE_ASC
            }
            if sort_order not in sort_mapping:
                raise ValidationError(f"Invalid sort order: {sort_order}")
            sort_order = sort_mapping[sort_order]
            
        new_spec = replace(self._spec, sort_by=sort_order)
        return Search(self._search_resource, new_spec)
        
    def with_reclevel(self, reclevel: Union[str, RecLevel]) -> Search:
        """Set record detail level.
        
        Args:
            reclevel: Detail level (brief or full)
            
        Returns:
            New Search instance with record level set
        """
        if isinstance(reclevel, str):
            reclevel = RecLevel(reclevel.lower())
            
        new_spec = replace(self._spec, record_level=reclevel)
        return Search(self._search_resource, new_spec)
        
    def with_facets(self, *facets: str) -> Search:
        """Request facet information.
        
        Args:
            *facets: Facet names to request
            
        Returns:
            New Search instance with facets set
            
        Examples:
            search.with_facets("decade", "format")
            search.with_facets("state", "category", "illustrated")
        """
        new_spec = replace(self._spec, facets=list(facets))
        return Search(self._search_resource, new_spec)
        
    def include(self, *fields: str) -> Search:
        """Include optional fields in results.
        
        Args:
            *fields: Fields to include (tags, comments, etc.)
            
        Returns:
            New Search instance with include fields set
        """
        new_spec = replace(self._spec, include_fields=list(fields))
        return Search(self._search_resource, new_spec)
        
    def harvest(self, enabled: bool = True) -> Search:
        """Enable bulk harvest mode for systematic data collection.
        
        Args:
            enabled: Whether to enable bulk harvest mode
            
        Returns:
            New Search instance with harvest mode set
        """
        new_spec = replace(self._spec, bulk_harvest=enabled)
        return Search(self._search_resource, new_spec)
        
    # Filter methods (ergonomic wrappers for common l-* parameters)
    
    def where(self, param: str, *values: str) -> Search:
        """Add arbitrary filter parameter.
        
        Args:
            param: Parameter name (with or without l- prefix)
            *values: Parameter values
            
        Returns:
            New Search instance with filter added
            
        Examples:
            search.where("decade", "200", "199")  
            search.where("l-availability", "y")
            search.where("format", "Book", "Map")
        """
        # Normalize parameter name
        if not param.startswith('l-'):
            param = f"l-{param}"
            
        filter_spec = SearchFilter(param, list(values))
        
        filters = list(self._spec.filters)
        filters.append(filter_spec)
        new_spec = replace(self._spec, filters=filters)
        return Search(self._search_resource, new_spec)
        
    def decade(self, *decades: str) -> Search:
        """Filter by publication decade(s).
        
        Args:
            *decades: Decade values (e.g. "200" for 2000s)
            
        Returns:
            New Search instance with decade filter
            
        Examples:
            search.decade("200")  # 2000s
            search.decade("200", "199")  # 2000s and 1990s
        """
        return self.where("decade", *decades)
        
    def year(self, *years: str) -> Search:
        """Filter by publication year(s).
        
        Args:
            *years: Year values (YYYY format)
            
        Returns:
            New Search instance with year filter
        """
        return self.where("year", *years)
        
    def format(self, *formats: str) -> Search:
        """Filter by format(s).
        
        Args:
            *formats: Format values (Book, Map, etc.)
            
        Returns:
            New Search instance with format filter
        """
        return self.where("format", *formats)
        
    def availability(self, *availability: str) -> Search:
        """Filter by availability.
        
        Args:
            *availability: Availability values (y, y/f, etc.)
            
        Returns:
            New Search instance with availability filter
        """
        return self.where("availability", *availability)
        
    def online(self) -> Search:
        """Filter for online-available items."""
        return self.availability("y")
        
    def free_online(self) -> Search:
        """Filter for freely available online items."""
        return self.availability("y/f")
        
    def state(self, *states: str) -> Search:
        """Filter by state (for newspapers).
        
        Args:
            *states: State codes (NSW, VIC, etc.)
            
        Returns:
            New Search instance with state filter
        """
        return self.where("state", *states)
        
    def illustrated(self, is_illustrated: bool = True) -> Search:
        """Filter by illustration status.
        
        Args:
            is_illustrated: Whether items should be illustrated
            
        Returns:
            New Search instance with illustration filter
        """
        return self.where("illustrated", str(is_illustrated).lower())
        
    def first_australians(self) -> Search:
        """Filter for First Australians content."""
        return self.where("firstAustralians", "y")
        
    def australian_content(self) -> Search:
        """Filter for Australian content."""
        return self.where("australian", "y")
        
    def culturally_sensitive(self) -> Search:
        """Filter for culturally sensitive content."""
        return self.where("culturalSensitivity", "y")
        
    # Execution methods
    
    def first_page(self) -> SearchResult:
        """Execute search and return first page of results.
        
        Returns:
            SearchResult with first page data
            
        Raises:
            ValidationError: Invalid search parameters
            TroveAPIError: API request failed
        """
        if not self._spec.categories:
            raise ValidationError("At least one category must be specified")
            
        params = self._spec.to_parameters()
        params.validate()
        
        return self._search_resource.page(params=params)
        
    def pages(self) -> Iterator[SearchResult]:
        """Iterate through all pages of results.
        
        This method only works with single-category searches to avoid
        pagination complexity. For multi-category searches, use first_page()
        and handle pagination manually.
        
        Yields:
            SearchResult objects for each page
            
        Raises:
            ValidationError: Multi-category search attempted
            TroveAPIError: API request failed
            
        Examples:
            for page in search.in_("book").text("history").pages():
                print(f"Page has {len(page.categories[0]['records']['work'])} results")
                if processed_enough:
                    break
        """
        if len(self._spec.categories) != 1:
            raise ValidationError(
                "pages() only supports single-category searches. "
                "Use first_page() for multi-category searches, or specify exactly one category."
            )
            
        params = self._spec.to_parameters()
        yield from self._search_resource.iter_pages(params=params)
        
    def records(self) -> Iterator[Dict[str, Any]]:
        """Iterate through individual records.
        
        This method only works with single-category searches.
        
        Yields:
            Individual record dictionaries
            
        Raises:
            ValidationError: Multi-category search attempted
            TroveAPIError: API request failed
            
        Examples:
            for record in search.in_("newspaper").state("NSW").records():
                print(f"Article: {record.get('heading')}")
                if found_what_we_need:
                    break
        """
        if len(self._spec.categories) != 1:
            raise ValidationError(
                "records() only supports single-category searches. "
                "Use first_page() for multi-category searches, or specify exactly one category."
            )
            
        params = self._spec.to_parameters()
        yield from self._search_resource.iter_records(params=params)
        
    def count(self) -> int:
        """Get total number of matching results without retrieving them.
        
        Returns:
            Total number of matching results across all categories
        """
        # Use n=0 to get count without results
        count_search = self.page_size(0)
        result = count_search.first_page()
        return result.total_results
        
    # Async versions
    
    async def afirst_page(self) -> SearchResult:
        """Async version of first_page."""
        if not self._spec.categories:
            raise ValidationError("At least one category must be specified")
            
        params = self._spec.to_parameters()
        params.validate()
        
        return await self._search_resource.apage(params=params)
        
    async def apages(self) -> AsyncIterator[SearchResult]:
        """Async version of pages."""
        if len(self._spec.categories) != 1:
            raise ValidationError(
                "apages() only supports single-category searches."
            )
            
        params = self._spec.to_parameters()
        async for page in self._search_resource.aiter_pages(params=params):
            yield page
            
    async def arecords(self) -> AsyncIterator[Dict[str, Any]]:
        """Async version of records."""
        async for page in self.apages():
            category_data = page.categories[0]
            category_code = self._spec.categories[0]
            
            # Extract records based on category
            records = self._search_resource._extract_records_from_category(
                category_data, category_code
            )
            
            for record in records:
                yield record
                
    # Utility methods
    
    def explain(self) -> Dict[str, Any]:
        """Get explanation of the search query for debugging.
        
        Returns:
            Dictionary with search parameters and metadata
        """
        params = self._spec.to_parameters()
        
        return {
            'categories': self._spec.categories,
            'query': self._spec.query,
            'filters': [
                {'param': f.param_name, 'values': f.values} 
                for f in self._spec.filters
            ],
            'page_size': self._spec.page_size,
            'sort_by': self._spec.sort_by.value,
            'record_level': self._spec.record_level.value,
            'include_fields': self._spec.include_fields,
            'facets': self._spec.facets,
            'bulk_harvest': self._spec.bulk_harvest,
            'compiled_params': params.to_query_params()
        }
        
    def __repr__(self) -> str:
        """String representation for debugging."""
        parts = []
        
        if self._spec.query:
            parts.append(f"text={repr(self._spec.query)}")
        if self._spec.categories:
            parts.append(f"categories={self._spec.categories}")
        if self._spec.filters:
            filter_parts = [f"{f.param_name}={f.values}" for f in self._spec.filters]
            parts.append(f"filters=[{', '.join(filter_parts)}]")
        if self._spec.page_size != 20:
            parts.append(f"page_size={self._spec.page_size}")
        if self._spec.sort_by != SortBy.RELEVANCE:
            parts.append(f"sort_by={self._spec.sort_by.value}")
            
        params_str = ', '.join(parts)
        return f"Search({params_str})"


# Convenience factory function
def search(search_resource: SearchResource) -> Search:
    """Create a new Search builder instance.
    
    Args:
        search_resource: SearchResource instance from transport layer
        
    Returns:
        New Search builder instance
        
    Examples:
        from trove import search, TroveConfig, TroveTransport
        
        config = TroveConfig.from_env()
        transport = TroveTransport(config, cache)
        search_resource = SearchResource(transport)
        
        results = (search(search_resource)
                  .text("Australian poetry")
                  .in_("book")
                  .decade("200")
                  .first_page())
    """
    return Search(search_resource)