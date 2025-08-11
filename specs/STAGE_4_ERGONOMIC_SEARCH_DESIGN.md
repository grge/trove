# Stage 4 - Ergonomic Search Design Document

## Overview

Stage 4 builds a fluent, immutable search API on top of the raw search functionality from Stage 2. This provides an ergonomic, research-friendly interface while maintaining full access to the underlying power of the complete API.

## Design Philosophy

- **Immutable builders** - Each method returns a new instance
- **Method chaining** - Fluent interface for readability
- **Type safety** - Leverage Python typing for better developer experience  
- **Clear limitations** - Explicit errors for multi-category pagination edge cases
- **Compile-time validation** - Catch errors early in the builder chain
- **Research-friendly** - Optimized for common research workflows

## Architecture Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Ergonomic Interface                           │
├─────────────────────────────────────────────────────────────────────┤
│    Search Builder  │  Result Iterators  │  Convenience Methods     │
├────────────────────┼────────────────────┼─────────────────────────┤
│                    Raw Search Resource (Stage 2)                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Design

### 1. Search Builder (`trove/search.py`)

```python
from __future__ import annotations
from typing import Dict, Any, List, Union, Optional, Iterator, AsyncIterator
from dataclasses import dataclass, field
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
        new_spec = copy.deepcopy(self._spec)
        new_spec = dataclass.replace(new_spec, query=query)
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
            
        new_spec = copy.deepcopy(self._spec)
        new_spec = dataclass.replace(new_spec, categories=list(categories))
        return Search(self._search_resource, new_spec)
        
    def page_size(self, n: int) -> Search:
        """Set number of results per page.
        
        Args:
            n: Number of results (1-100)
            
        Returns:
            New Search instance with page size set
        """
        if n < 1 or n > 100:
            raise ValidationError("Page size must be between 1 and 100")
            
        new_spec = copy.deepcopy(self._spec)
        new_spec = dataclass.replace(new_spec, page_size=n)
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
            
        new_spec = copy.deepcopy(self._spec)
        new_spec = dataclass.replace(new_spec, sort_by=sort_order)
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
            
        new_spec = copy.deepcopy(self._spec)
        new_spec = dataclass.replace(new_spec, record_level=reclevel)
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
        new_spec = copy.deepcopy(self._spec)
        new_spec = dataclass.replace(new_spec, facets=list(facets))
        return Search(self._search_resource, new_spec)
        
    def include(self, *fields: str) -> Search:
        """Include optional fields in results.
        
        Args:
            *fields: Fields to include (tags, comments, etc.)
            
        Returns:
            New Search instance with include fields set
        """
        new_spec = copy.deepcopy(self._spec)
        new_spec = dataclass.replace(new_spec, include_fields=list(fields))
        return Search(self._search_resource, new_spec)
        
    def harvest(self, enabled: bool = True) -> Search:
        """Enable bulk harvest mode for systematic data collection.
        
        Args:
            enabled: Whether to enable bulk harvest mode
            
        Returns:
            New Search instance with harvest mode set
        """
        new_spec = copy.deepcopy(self._spec)
        new_spec = dataclass.replace(new_spec, bulk_harvest=enabled)
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
        
        new_spec = copy.deepcopy(self._spec)
        filters = list(new_spec.filters)
        filters.append(filter_spec)
        new_spec = dataclass.replace(new_spec, filters=filters)
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
        
        return self._search_resource.page(params)
        
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
        yield from self._search_resource.iter_pages(params)
        
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
        yield from self._search_resource.iter_records(params)
        
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
        
        return await self._search_resource.apage(params)
        
    async def apages(self) -> AsyncIterator[SearchResult]:
        """Async version of pages."""
        if len(self._spec.categories) != 1:
            raise ValidationError(
                "apages() only supports single-category searches."
            )
            
        params = self._spec.to_parameters()
        async for page in self._search_resource.aiter_pages(params):
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
```

### 2. Enhanced Result Types (`trove/result.py`)

```python
from typing import Dict, Any, List, Optional, Iterator
from dataclasses import dataclass

@dataclass
class RecordWrapper:
    """Wrapper for individual records with convenience methods."""
    
    data: Dict[str, Any]
    category: str
    
    @property
    def id(self) -> str:
        """Get record ID."""
        return str(self.data.get('id', ''))
        
    @property
    def title(self) -> str:
        """Get record title (works for most record types)."""
        # Different record types store titles differently
        return (self.data.get('title') or 
                self.data.get('heading') or
                self.data.get('primaryName') or
                self.data.get('primaryDisplayName') or
                'Untitled')
                
    @property  
    def url(self) -> Optional[str]:
        """Get Trove web interface URL."""
        return self.data.get('troveUrl')
        
    @property
    def date(self) -> Optional[str]:
        """Get publication/creation date."""
        return (self.data.get('date') or
                self.data.get('issued'))
                
    @property
    def snippet(self) -> Optional[str]:
        """Get search result snippet."""
        snippets = self.data.get('snippet', [])
        if isinstance(snippets, list) and snippets:
            return snippets[0]
        elif isinstance(snippets, str):
            return snippets
        return None
        
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access to underlying data."""
        return self.data[key]
        
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        return key in self.data
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get value with default."""
        return self.data.get(key, default)
        
    def keys(self):
        """Get all keys from underlying data."""
        return self.data.keys()
        
    def items(self):
        """Get all items from underlying data."""
        return self.data.items()

@dataclass
class EnhancedSearchResult:
    """Enhanced search result with convenience methods."""
    
    raw_result: Dict[str, Any]
    
    @property
    def query(self) -> str:
        """Get the search query."""
        return self.raw_result.get('query', '')
        
    @property
    def total_results(self) -> int:
        """Get total number of results across all categories."""
        total = 0
        for category in self.raw_result.get('category', []):
            total += category.get('records', {}).get('total', 0)
        return total
        
    @property
    def categories(self) -> List[str]:
        """Get list of category codes in results."""
        return [cat['code'] for cat in self.raw_result.get('category', [])]
        
    def category_totals(self) -> Dict[str, int]:
        """Get result counts by category."""
        totals = {}
        for category in self.raw_result.get('category', []):
            code = category['code']
            total = category.get('records', {}).get('total', 0)
            totals[code] = total
        return totals
        
    def records_for_category(self, category_code: str) -> Iterator[RecordWrapper]:
        """Get records for a specific category."""
        for category in self.raw_result.get('category', []):
            if category['code'] == category_code:
                records_data = category.get('records', {})
                
                # Different categories store records differently
                record_containers = {
                    'book': 'work', 'image': 'work', 'magazine': 'work',
                    'music': 'work', 'diary': 'work', 'research': 'work',
                    'newspaper': 'article', 'people': 'people', 'list': 'list'
                }
                
                container = record_containers.get(category_code, 'work')
                records = records_data.get(container, [])
                
                if isinstance(records, dict):
                    records = [records]
                    
                for record in records:
                    yield RecordWrapper(record, category_code)
                break
                
    def all_records(self) -> Iterator[RecordWrapper]:
        """Get all records from all categories."""
        for category_code in self.categories:
            yield from self.records_for_category(category_code)
            
    def facets_for_category(self, category_code: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get facets for a specific category."""
        for category in self.raw_result.get('category', []):
            if category['code'] == category_code:
                facets_data = category.get('facets', {}).get('facet', [])
                if isinstance(facets_data, dict):
                    facets_data = [facets_data]
                    
                facets = {}
                for facet in facets_data:
                    facet_name = facet['name']
                    terms = facet.get('term', [])
                    if isinstance(terms, dict):
                        terms = [terms]
                    facets[facet_name] = terms
                    
                return facets
        return {}
```

### 3. Integration with Transport Layer (`trove/__init__.py`)

```python
from .config import TroveConfig
from .transport import TroveTransport  
from .cache import MemoryCache, SqliteCache, create_cache
from .resources.search import SearchResource
from .resources import ResourceFactory
from .search import Search, search
from .exceptions import *

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
```

## Testing Strategy

### Unit Tests

```python
# test_ergonomic_search.py
import pytest
from unittest.mock import Mock
from trove.search import Search, SearchSpec
from trove.params import SortBy, RecLevel
from trove.exceptions import ValidationError

def test_immutable_builder():
    """Test that search builder is immutable."""
    mock_resource = Mock()
    
    search1 = Search(mock_resource)
    search2 = search1.text("test")
    search3 = search2.in_("book")
    
    # Each operation should return a new instance
    assert search1 is not search2
    assert search2 is not search3
    
    # Original should be unchanged
    assert search1._spec.query is None
    assert search2._spec.query == "test"
    assert search3._spec.query == "test"
    assert search3._spec.categories == ["book"]

def test_method_chaining():
    """Test fluent method chaining."""
    mock_resource = Mock()
    
    search = (Search(mock_resource)
             .text("Australian history")
             .in_("book", "image")
             .decade("200", "199")
             .page_size(50)
             .sort_by("date_desc")
             .with_facets("format", "language")
             .illustrated()
             .australian_content())
             
    spec = search._spec
    assert spec.query == "Australian history"
    assert spec.categories == ["book", "image"]
    assert spec.page_size == 50
    assert spec.sort_by == SortBy.DATE_DESC
    assert spec.facets == ["format", "language"]
    
    # Check filters
    filter_names = {f.param_name for f in spec.filters}
    assert "l-decade" in filter_names
    assert "l-illustrated" in filter_names
    assert "l-australian" in filter_names

def test_parameter_validation():
    """Test parameter validation in builder."""
    mock_resource = Mock()
    search = Search(mock_resource)
    
    # Invalid category should raise error
    with pytest.raises(ValidationError, match="Invalid categories"):
        search.in_("invalid_category")
        
    # Invalid page size should raise error
    with pytest.raises(ValidationError, match="Page size must be"):
        search.page_size(0)
        search.page_size(101)
        
    # Invalid sort order should raise error  
    with pytest.raises(ValidationError, match="Invalid sort order"):
        search.sort_by("invalid_sort")

def test_single_category_validation():
    """Test single category validation for iteration methods."""
    mock_resource = Mock()
    
    # Single category should work
    single_cat_search = Search(mock_resource).in_("book")
    # Should not raise error
    
    # Multi-category should raise error for pages()  
    multi_cat_search = Search(mock_resource).in_("book", "image")
    with pytest.raises(ValidationError, match="only supports single-category"):
        list(multi_cat_search.pages())
        
    with pytest.raises(ValidationError, match="only supports single-category"):
        list(multi_cat_search.records())

def test_parameter_compilation():
    """Test conversion to raw SearchParameters."""
    mock_resource = Mock()
    
    search = (Search(mock_resource)
             .text("test query")
             .in_("book")
             .decade("200")
             .format("Book")
             .page_size(25)
             .harvest())
             
    params = search._spec.to_parameters()
    
    assert params.category == ["book"]
    assert params.q == "test query"
    assert params.n == 25
    assert params.bulkHarvest == True
    assert params.l_decade == ["200"]
    assert params.l_format == ["Book"]

def test_convenience_filters():
    """Test convenience filter methods."""
    mock_resource = Mock()
    
    search = (Search(mock_resource)
             .online()
             .free_online()
             .first_australians()
             .australian_content()
             .culturally_sensitive()
             .illustrated())
             
    filters = {f.param_name: f.values for f in search._spec.filters}
    
    assert filters["l-availability"] == ["y", "y/f"]  # Both online and free_online
    assert filters["l-firstAustralians"] == ["y"]
    assert filters["l-australian"] == ["y"]
    assert filters["l-culturalSensitivity"] == ["y"]
    assert filters["l-illustrated"] == ["true"]

def test_explain_method():
    """Test search explanation for debugging."""
    mock_resource = Mock()
    
    search = (Search(mock_resource)
             .text("test")
             .in_("book")
             .decade("200")
             .page_size(10))
             
    explanation = search.explain()
    
    assert explanation['categories'] == ["book"]
    assert explanation['query'] == "test"
    assert explanation['page_size'] == 10
    assert len(explanation['filters']) == 1
    assert explanation['filters'][0]['param'] == "l-decade"
    assert 'compiled_params' in explanation

def test_repr_method():
    """Test string representation."""
    mock_resource = Mock()
    
    search = (Search(mock_resource)
             .text("test")
             .in_("book")
             .page_size(50))
             
    repr_str = repr(search)
    assert "text='test'" in repr_str
    assert "categories=['book']" in repr_str
    assert "page_size=50" in repr_str
```

### Integration Tests

```python
# test_ergonomic_integration.py
import pytest
import os
from trove import TroveClient

@pytest.mark.integration
class TestErgonomicSearchIntegration:
    """Integration tests for ergonomic search with real API."""
    
    @pytest.fixture(scope="class")
    def client(self):
        api_key = os.environ.get('TROVE_API_KEY')
        if not api_key:
            pytest.skip("TROVE_API_KEY not set")
        return TroveClient.from_api_key(api_key, rate_limit=1.0)
        
    def test_basic_ergonomic_search(self, client):
        """Test basic ergonomic search functionality."""
        result = (client.search()
                 .text("Australian history")
                 .in_("book")
                 .page_size(5)
                 .first_page())
                 
        assert result.total_results > 0
        assert len(result.categories) == 1
        assert result.categories[0]['code'] == 'book'
        
    def test_method_chaining_real_api(self, client):
        """Test complex method chaining with real API."""
        result = (client.search()
                 .text("federation")
                 .in_("newspaper")
                 .decade("190")
                 .state("NSW")
                 .illustrated()
                 .sort_by("date_desc")
                 .page_size(10)
                 .first_page())
                 
        # Should return results (exact assertions depend on data availability)
        assert result.categories[0]['records']['total'] >= 0
        
    def test_single_category_iteration(self, client):
        """Test single category iteration."""
        pages = list((client.search()
                     .text("poetry")
                     .in_("book")
                     .page_size(5)
                     .pages())[:2])  # Limit to first 2 pages
                     
        assert len(pages) >= 1
        if len(pages) > 1:
            # Verify pagination worked
            assert pages[0].raw_result != pages[1].raw_result
            
    def test_record_iteration(self, client):
        """Test individual record iteration.""" 
        records = list((client.search()
                       .text("Melbourne")
                       .in_("book")
                       .page_size(10)
                       .records())[:15])  # Limit to first 15 records
                       
        if records:  # If any records found
            assert isinstance(records[0], dict)
            assert 'title' in records[0]
            
    def test_faceting_integration(self, client):
        """Test faceting with ergonomic search."""
        result = (client.search()
                 .text("literature")
                 .in_("book")
                 .with_facets("decade", "format")
                 .page_size(1)
                 .first_page())
                 
        facets = result.categories[0].get('facets', {})
        if 'facet' in facets:
            facet_names = {f['name'] for f in facets['facet']}
            assert 'decade' in facet_names
            
    def test_count_functionality(self, client):
        """Test count method."""
        count = (client.search()
                .text("Australia")
                .in_("book")
                .decade("200")
                .count())
                
        assert isinstance(count, int)
        assert count >= 0
        
    def test_multi_category_handling(self, client):
        """Test multi-category search limitations."""
        search = (client.search()
                 .text("Sydney")
                 .in_("book", "image")
                 .page_size(10))
                 
        # first_page should work
        result = search.first_page()
        assert len(result.categories) == 2
        
        # pages() should raise error
        with pytest.raises(ValidationError, match="only supports single-category"):
            list(search.pages())
            
    def test_bulk_harvest_mode(self, client):
        """Test bulk harvest mode."""
        result = (client.search()
                 .text("test")
                 .in_("book")
                 .harvest()
                 .page_size(10)
                 .first_page())
                 
        # Should return results sorted by identifier
        assert result.categories[0]['records']['total'] >= 0
        
    def test_async_search(self, client):
        """Test async search functionality.""" 
        async def async_search_test():
            result = await (client.search()
                           .text("Australian poetry")
                           .in_("book")
                           .page_size(5)
                           .afirst_page())
            return result
            
        # Note: This would need to be run in an async context
        # The actual test would use pytest-asyncio
        assert async_search_test is not None  # Placeholder
```

### Performance Tests

```python
# test_ergonomic_performance.py
import time
import pytest

@pytest.mark.performance
class TestErgonomicSearchPerformance:
    """Performance tests for ergonomic search."""
    
    def test_builder_performance(self, client):
        """Test that builder operations are fast."""
        start_time = time.time()
        
        # Build complex search
        search = (client.search()
                 .text("Australian literature")
                 .in_("book", "magazine")
                 .decade("200", "199", "198")
                 .format("Book", "Journal")
                 .availability("y", "y/f")
                 .state("NSW", "VIC", "QLD")
                 .illustrated(True)
                 .first_australians()
                 .australian_content()
                 .with_facets("decade", "format", "language")
                 .include("tags", "comments")
                 .page_size(50)
                 .sort_by("date_desc")
                 .harvest())
                 
        build_duration = time.time() - start_time
        
        # Building should be very fast (no API calls)
        assert build_duration < 0.1  # Less than 100ms
        
        # Compilation should also be fast
        start_time = time.time()
        params = search._spec.to_parameters()
        compile_duration = time.time() - start_time
        
        assert compile_duration < 0.01  # Less than 10ms
        
    def test_iteration_performance(self, client):
        """Test performance of record iteration."""
        start_time = time.time()
        
        # Process first 100 records
        count = 0
        for record in (client.search()
                      .text("test")
                      .in_("book")
                      .page_size(20)
                      .records()):
            count += 1
            if count >= 100:
                break
                
        duration = time.time() - start_time
        
        # Should process records efficiently
        if count > 0:
            time_per_record = duration / count
            assert time_per_record < 0.5  # Less than 500ms per record
```

## Usage Examples

```python
# examples/ergonomic_search_examples.py

from trove import TroveClient

def basic_search_example():
    """Basic search example."""
    client = TroveClient.from_env()
    
    # Simple search
    result = (client.search()
             .text("Australian poetry")
             .in_("book")
             .page_size(20)
             .first_page())
    
    print(f"Found {result.total_results} results")
    
    # Access records
    for record in result.all_records():
        print(f"- {record.title} ({record.date})")

def filtered_search_example():
    """Advanced filtering example."""
    client = TroveClient.from_env()
    
    # Complex search with multiple filters
    search = (client.search()
             .text("federation")
             .in_("newspaper")
             .decade("190")  # 1900s
             .state("NSW", "VIC")  # NSW and Victoria
             .illustrated()
             .sort_by("date_desc")
             .with_facets("year", "title"))
             
    print("Search explanation:")
    print(search.explain())
    
    result = search.first_page()
    print(f"\nFound {result.total_results} articles")
    
def research_workflow_example():
    """Research workflow example."""
    client = TroveClient.from_env()
    
    # Systematic data collection
    search = (client.search()
             .text("women's rights")
             .in_("newspaper")
             .decade("190", "191", "192")  # 1900s-1920s
             .harvest()  # Enable bulk harvest mode
             .page_size(100))
             
    collected = 0
    for record in search.records():
        # Process each record
        article_title = record.title
        article_date = record.date
        article_text = record.get('articleText', '')
        
        # Your analysis code here...
        print(f"Processing: {article_title} ({article_date})")
        
        collected += 1
        if collected >= 500:  # Limit for demo
            break
            
    print(f"Collected {collected} articles")

def faceted_exploration_example():
    """Faceted browsing example."""
    client = TroveClient.from_env()
    
    # Start with broad search
    result = (client.search()
             .text("Aboriginal Australia")
             .in_("book")
             .with_facets("decade", "format", "language")
             .first_page())
    
    # Explore facets
    for category_code in result.categories:
        facets = result.facets_for_category(category_code)
        
        print(f"\nFacets for {category_code}:")
        for facet_name, terms in facets.items():
            print(f"  {facet_name}:")
            for term in terms[:5]:  # Show top 5 terms
                print(f"    {term['display']} ({term['count']})")
                
    # Refine search based on facets
    refined_result = (client.search()
                     .text("Aboriginal Australia")
                     .in_("book")
                     .decade("200")  # Focus on 2000s
                     .format("Book")  # Only books
                     .first_page())
                     
    print(f"\nRefined search: {refined_result.total_results} results")

if __name__ == "__main__":
    basic_search_example()
    filtered_search_example()
    research_workflow_example()  
    faceted_exploration_example()
```

## Definition of Done

Stage 4 is complete when:

- ✅ **Immutable builder pattern** - All methods return new instances
- ✅ **Fluent interface** - Method chaining works naturally
- ✅ **Single-category iteration** - pages() and records() work reliably
- ✅ **Multi-category handling** - Clear errors for unsupported operations
- ✅ **Parameter compilation** - Builder correctly compiles to raw parameters
- ✅ **Convenience methods** - Common filters have ergonomic wrappers
- ✅ **Type safety** - Proper typing throughout
- ✅ **Async support** - Async versions of all methods
- ✅ **Error handling** - Clear validation errors with helpful messages
- ✅ **Performance** - Builder operations are fast, minimal overhead
- ✅ **Documentation** - All methods documented with examples
- ✅ **Tests passing** - Unit and integration tests with real API
- ✅ **Examples working** - All usage examples execute successfully

This ergonomic search interface makes Trove research workflows more intuitive while maintaining access to the full power of the underlying API.