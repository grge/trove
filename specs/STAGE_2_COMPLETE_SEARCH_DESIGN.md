# Stage 2 - Complete Search Design Document

## Overview

Stage 2 implements comprehensive search functionality with complete parameter support, cursor-based pagination, and robust multi-category handling. This stage provides the raw, powerful search interface that later stages will build upon.

## API Analysis Summary

Based on the comprehensive API documentation review:

- **60+ search parameters** across categories (l-format, l-decade, l-year, l-availability, etc.)
- **Complex pagination** using `s` (start) cursor with `nextStart` responses
- **Multi-category challenges** - each category has independent pagination cursors
- **Faceting system** for result refinement and discovery
- **Bulk harvest mode** for systematic data collection

## Architecture Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Search Interface                             │
├─────────────────────────────────────────────────────────────────────┤
│  SearchResource  │  ParameterBuilder  │  Iterators  │  Validators   │
├──────────────────┴────────────────────┴─────────────┴───────────────┤
│                       Transport Layer (Stage 1)                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Design

### 1. Parameter Management (`trove/params.py`)

```python
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import warnings

class SortBy(Enum):
    RELEVANCE = "relevance"
    DATE_DESC = "datedesc" 
    DATE_ASC = "dateasc"

class RecLevel(Enum):
    BRIEF = "brief"
    FULL = "full"

class Encoding(Enum):
    JSON = "json"
    XML = "xml"

@dataclass
class SearchParameters:
    """Comprehensive search parameters based on Trove API v3 specification."""
    
    # Required parameters
    category: List[str] = field(default_factory=list)
    
    # Core search parameters  
    q: Optional[str] = None
    
    # Pagination and results
    s: str = "*"  # start cursor
    n: int = 20   # number of results
    sortby: SortBy = SortBy.RELEVANCE
    bulkHarvest: bool = False
    
    # Response control
    reclevel: RecLevel = RecLevel.BRIEF
    encoding: Encoding = Encoding.JSON
    include: List[str] = field(default_factory=list)
    facet: List[str] = field(default_factory=list)
    
    # Date and time filters
    l_decade: List[str] = field(default_factory=list)
    l_year: List[str] = field(default_factory=list) 
    l_month: List[str] = field(default_factory=list)
    
    # Format and content type
    l_format: List[str] = field(default_factory=list)
    l_artType: List[str] = field(default_factory=list)
    
    # Language and cultural
    l_language: List[str] = field(default_factory=list)
    l_austlanguage: List[str] = field(default_factory=list)
    l_firstAustralians: Optional[str] = None  # "y" only
    l_culturalSensitivity: Optional[str] = None  # "y" only
    
    # Geographic
    l_geocoverage: List[str] = field(default_factory=list)
    l_place: List[str] = field(default_factory=list)
    l_state: List[str] = field(default_factory=list)
    
    # Contributor and collection
    l_contribcollection: Optional[str] = None
    l_partnerNuc: List[str] = field(default_factory=list)
    
    # Availability
    l_availability: List[str] = field(default_factory=list)
    l_australian: Optional[str] = None  # "y" only
    
    # People-specific
    l_occupation: List[str] = field(default_factory=list)
    l_birth: List[str] = field(default_factory=list)
    l_death: List[str] = field(default_factory=list)
    
    # Content specific  
    l_zoom: List[str] = field(default_factory=list)
    l_audience: List[str] = field(default_factory=list)
    l_title: List[str] = field(default_factory=list)
    l_category: List[str] = field(default_factory=list)
    l_illustrated: Optional[bool] = None
    l_illustrationType: List[str] = field(default_factory=list)
    l_wordCount: List[str] = field(default_factory=list)
    
    # Additional limits (for extensibility)
    otherLimits: Dict[str, Any] = field(default_factory=dict)
    
    def to_query_params(self) -> Dict[str, Any]:
        """Convert to query parameters for API request."""
        params = {}
        
        # Required category parameter
        if not self.category:
            raise ValueError("At least one category is required")
        params['category'] = ','.join(self.category)
        
        # Optional query
        if self.q is not None:
            params['q'] = self.q
            
        # Pagination
        params['s'] = self.s
        params['n'] = self.n
        params['sortby'] = self.sortby.value
        if self.bulkHarvest:
            params['bulkHarvest'] = 'true'
            
        # Response control
        params['reclevel'] = self.reclevel.value
        params['encoding'] = self.encoding.value
        
        if self.include:
            params['include'] = ','.join(self.include)
        if self.facet:
            params['facet'] = ','.join(self.facet)
            
        # Add limit parameters (l-*)
        limit_fields = [f for f in dir(self) if f.startswith('l_')]
        for field_name in limit_fields:
            api_name = field_name.replace('_', '-')
            value = getattr(self, field_name)
            
            if value is None:
                continue
            elif isinstance(value, list) and value:
                params[api_name] = ','.join(value)
            elif isinstance(value, bool):
                params[api_name] = str(value).lower()
            elif isinstance(value, str):
                params[api_name] = value
                
        # Add other limits
        params.update(self.otherLimits)
        
        return params
        
    def validate(self) -> None:
        """Validate parameter combinations and dependencies."""
        if not self.category:
            raise ValueError("At least one category is required")
            
        # Validate category values
        valid_categories = {
            'all', 'book', 'diary', 'image', 'list', 
            'magazine', 'music', 'newspaper', 'people', 'research'
        }
        invalid_categories = set(self.category) - valid_categories
        if invalid_categories:
            raise ValueError(f"Invalid categories: {invalid_categories}")
            
        # Check parameter dependencies
        if self.l_month and not self.l_year:
            raise ValueError("l-month requires l-year to also be specified")
            
        if 'newspaper' in self.category and self.l_year and not self.l_decade:
            raise ValueError("For newspapers, l-year requires l-decade to also be specified")
            
        # Check boolean-only fields
        boolean_only_fields = ['l_firstAustralians', 'l_culturalSensitivity', 'l_australian']
        for field_name in boolean_only_fields:
            value = getattr(self, field_name)
            if value is not None and value != 'y':
                raise ValueError(f"{field_name} can only be 'y' or None")
                
        # Validate availability values  
        if self.l_availability:
            valid_availability = {'y', 'y/f', 'y/r', 'y/s', 'y/u'}
            invalid_availability = set(self.l_availability) - valid_availability
            if invalid_availability:
                raise ValueError(f"Invalid availability values: {invalid_availability}")

class ParameterBuilder:
    """Builder for constructing search parameters with validation."""
    
    def __init__(self):
        self._params = SearchParameters()
        
    def categories(self, *categories: str) -> 'ParameterBuilder':
        """Set search categories."""
        self._params.category = list(categories)
        return self
        
    def query(self, q: str) -> 'ParameterBuilder':
        """Set search query."""
        self._params.q = q
        return self
        
    def page_size(self, n: int) -> 'ParameterBuilder':
        """Set number of results per page."""
        if n < 1 or n > 100:
            raise ValueError("Page size must be between 1 and 100")
        self._params.n = n
        return self
        
    def cursor(self, s: str) -> 'ParameterBuilder':
        """Set pagination cursor."""
        self._params.s = s
        return self
        
    def sort(self, sortby: Union[str, SortBy]) -> 'ParameterBuilder':
        """Set sort order."""
        if isinstance(sortby, str):
            sortby = SortBy(sortby)
        self._params.sortby = sortby
        return self
        
    def bulk_harvest(self, enabled: bool = True) -> 'ParameterBuilder':
        """Enable bulk harvest mode."""
        self._params.bulkHarvest = enabled
        return self
        
    def record_level(self, reclevel: Union[str, RecLevel]) -> 'ParameterBuilder':
        """Set record detail level."""
        if isinstance(reclevel, str):
            reclevel = RecLevel(reclevel)
        self._params.reclevel = reclevel
        return self
        
    def include_fields(self, *fields: str) -> 'ParameterBuilder':
        """Include optional fields in results."""
        self._params.include = list(fields)
        return self
        
    def facets(self, *facets: str) -> 'ParameterBuilder':
        """Request facet information."""
        self._params.facet = list(facets)
        return self
        
    def decade(self, *decades: str) -> 'ParameterBuilder':
        """Filter by publication decade(s)."""
        self._params.l_decade = list(decades)
        return self
        
    def year(self, *years: str) -> 'ParameterBuilder':
        """Filter by publication year(s)."""
        self._params.l_year = list(years)
        return self
        
    def format(self, *formats: str) -> 'ParameterBuilder':
        """Filter by format(s)."""
        self._params.l_format = list(formats)
        return self
        
    def availability(self, *availability: str) -> 'ParameterBuilder':
        """Filter by availability."""
        self._params.l_availability = list(availability)
        return self
        
    def state(self, *states: str) -> 'ParameterBuilder':
        """Filter by state (newspapers).""" 
        self._params.l_state = list(states)
        return self
        
    def first_australians(self) -> 'ParameterBuilder':
        """Filter for First Australians content."""
        self._params.l_firstAustralians = 'y'
        return self
        
    def australian_content(self) -> 'ParameterBuilder':
        """Filter for Australian content."""
        self._params.l_australian = 'y'
        return self
        
    def limit(self, param: str, *values: str) -> 'ParameterBuilder':
        """Add arbitrary limit parameter."""
        self._params.otherLimits[param] = ','.join(values) if len(values) > 1 else values[0]
        return self
        
    def build(self) -> SearchParameters:
        """Build and validate parameters."""
        self._params.validate()
        return self._params
```

### 2. Search Resource (`trove/resources/search.py`)

```python
from typing import Dict, Any, List, Optional, Iterator, AsyncIterator, Tuple
from dataclasses import dataclass
import logging
import warnings
from ..transport import TroveTransport
from ..params import SearchParameters, ParameterBuilder
from ..exceptions import TroveAPIError, ValidationError

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Container for search results with metadata."""
    
    query: str
    categories: List[Dict[str, Any]]
    total_results: int
    cursors: Dict[str, str]  # category_code -> next_cursor
    response_data: Dict[str, Any]
    
    def __post_init__(self):
        # Extract cursors from response for each category
        self.cursors = {}
        for category in self.categories:
            if 'records' in category and 'nextStart' in category['records']:
                self.cursors[category['code']] = category['records']['nextStart']

@dataclass 
class PaginationState:
    """State for paginated search operations."""
    
    params: SearchParameters
    current_category: str
    current_cursor: str
    has_more: bool = True
    total_retrieved: int = 0

class SearchResource:
    """Raw search resource providing complete API access."""
    
    def __init__(self, transport: TroveTransport):
        self.transport = transport
        
    def page(self, **kwargs) -> SearchResult:
        """Execute a single search page request.
        
        Args:
            **kwargs: Search parameters (can be raw params or named arguments)
            
        Returns:
            SearchResult with response data and pagination info
            
        Examples:
            # Using raw parameters
            result = search.page(category=['book'], q='Australian history', n=10)
            
            # Using parameter names  
            result = search.page(
                category=['book', 'image'],
                q='Sydney',
                l_decade=['200'],
                facet=['format', 'decade'],
                n=20
            )
        """
        # Handle both SearchParameters objects and raw kwargs
        if len(kwargs) == 1 and isinstance(list(kwargs.values())[0], SearchParameters):
            params = list(kwargs.values())[0]
        else:
            # Convert kwargs to SearchParameters
            params = self._kwargs_to_params(kwargs)
            
        params.validate()
        query_params = params.to_query_params()
        
        logger.info(f"Search request: categories={params.category}, query='{params.q}', n={params.n}")
        
        try:
            response_data = self.transport.get('/result', query_params)
            
            # Parse response into SearchResult
            result = self._parse_search_response(response_data, params)
            
            logger.info(f"Search completed: {result.total_results} total results across {len(result.categories)} categories")
            
            return result
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
            
    async def apage(self, **kwargs) -> SearchResult:
        """Async version of page method."""
        # Similar implementation using transport.aget
        pass  # Implementation similar to page() but using async transport
        
    def iter_pages(self, **kwargs) -> Iterator[SearchResult]:
        """Iterate through all pages for single-category searches.
        
        Args:
            **kwargs: Search parameters
            
        Yields:
            SearchResult objects for each page
            
        Raises:
            ValidationError: If multiple categories specified
            
        Examples:
            for page in search.iter_pages(category=['book'], q='history'):
                print(f"Page has {len(page.categories[0]['records']['work'])} results")
                if some_condition:
                    break  # Can break early
        """
        params = self._kwargs_to_params(kwargs)
        
        if len(params.category) > 1:
            raise ValidationError(
                "iter_pages only supports single-category searches. "
                "Use iter_pages_by_category for multi-category searches."
            )
            
        category_code = params.category[0]
        current_cursor = params.s
        
        while True:
            # Update cursor for this request
            params.s = current_cursor
            
            try:
                result = self.page(params)
                yield result
                
                # Check if there are more pages
                if category_code not in result.cursors:
                    break  # No more pages
                    
                current_cursor = result.cursors[category_code]
                
            except TroveAPIError as e:
                logger.warning(f"Pagination stopped due to API error: {e}")
                break
                
    async def aiter_pages(self, **kwargs) -> AsyncIterator[SearchResult]:
        """Async version of iter_pages."""
        # Similar implementation but async
        pass
        
    def iter_records(self, **kwargs) -> Iterator[Dict[str, Any]]:
        """Iterate through individual records for single-category searches.
        
        Args:
            **kwargs: Search parameters
            
        Yields:
            Individual record dictionaries
            
        Examples:
            for record in search.iter_records(category=['work'], q='poetry', n=50):
                print(f"Found: {record['title']}")
                if total_processed >= 1000:
                    break
        """
        params = self._kwargs_to_params(kwargs)
        
        if len(params.category) > 1:
            raise ValidationError(
                "iter_records only supports single-category searches. "
                "Use iter_pages_by_category for multi-category access."
            )
        
        category_code = params.category[0]
        
        for page_result in self.iter_pages(**kwargs):
            category_data = page_result.categories[0]
            
            # Extract records based on category type
            records = self._extract_records_from_category(category_data, category_code)
            
            for record in records:
                yield record
                
    def iter_pages_by_category(self, **kwargs) -> Iterator[Tuple[str, SearchResult]]:
        """Iterate through pages for multi-category searches.
        
        This method handles the complexity of multi-category pagination by
        yielding pages for each category sequentially.
        
        Args:
            **kwargs: Search parameters (can include multiple categories)
            
        Yields:
            Tuples of (category_code, SearchResult) for each page
            
        Examples:
            params = {'category': ['book', 'image'], 'q': 'Sydney'}
            for category_code, page in search.iter_pages_by_category(**params):
                print(f"Category {category_code}: {page.total_results} total results")
                # Process records for this category...
        """
        params = self._kwargs_to_params(kwargs)
        
        # First request gets initial results for all categories
        initial_result = self.page(params)
        
        # Process each category separately
        for category_data in initial_result.categories:
            category_code = category_data['code']
            
            # Yield the first page for this category
            single_category_result = SearchResult(
                query=initial_result.query,
                categories=[category_data],
                total_results=category_data['records'].get('total', 0),
                cursors={category_code: initial_result.cursors.get(category_code, '')},
                response_data=initial_result.response_data
            )
            yield category_code, single_category_result
            
            # Continue with remaining pages for this category if available
            if category_code in initial_result.cursors:
                single_category_params = SearchParameters(
                    category=[category_code],
                    q=params.q,
                    n=params.n,
                    s=initial_result.cursors[category_code],
                    sortby=params.sortby,
                    reclevel=params.reclevel,
                    encoding=params.encoding
                )
                
                # Copy relevant limit parameters for this category
                self._copy_category_limits(params, single_category_params, category_code)
                
                # Iterate remaining pages
                for page_result in self.iter_pages(single_category_params):
                    yield category_code, page_result
                    
    def build_params(self) -> ParameterBuilder:
        """Create a parameter builder for fluent parameter construction."""
        return ParameterBuilder()
        
    def _kwargs_to_params(self, kwargs: Dict[str, Any]) -> SearchParameters:
        """Convert keyword arguments to SearchParameters object."""
        # Handle the case where a SearchParameters object is passed
        if 'params' in kwargs and isinstance(kwargs['params'], SearchParameters):
            return kwargs['params']
        
        # Convert kwargs to SearchParameters
        params = SearchParameters()
        
        # Map common parameter names
        param_mapping = {
            'category': 'category',
            'q': 'q', 
            's': 's',
            'n': 'n',
            'sortby': 'sortby',
            'bulkHarvest': 'bulkHarvest', 
            'reclevel': 'reclevel',
            'encoding': 'encoding',
            'include': 'include',
            'facet': 'facet'
        }
        
        for kwarg_name, value in kwargs.items():
            if kwarg_name in param_mapping:
                setattr(params, param_mapping[kwarg_name], value)
            elif kwarg_name.startswith('l_') or kwarg_name.startswith('l-'):
                # Handle limit parameters
                attr_name = kwarg_name.replace('-', '_')
                if hasattr(params, attr_name):
                    setattr(params, attr_name, value)
                else:
                    # Store in otherLimits for unknown parameters
                    api_name = kwarg_name.replace('_', '-')
                    params.otherLimits[api_name] = value
                    
        return params
        
    def _parse_search_response(self, response_data: Dict[str, Any], 
                             params: SearchParameters) -> SearchResult:
        """Parse API response into SearchResult object."""
        
        query = response_data.get('query', params.q or '')
        categories = response_data.get('category', [])
        
        # Calculate total results across all categories
        total_results = sum(
            cat.get('records', {}).get('total', 0) 
            for cat in categories
        )
        
        return SearchResult(
            query=query,
            categories=categories,
            total_results=total_results,
            cursors={},  # Will be populated in __post_init__
            response_data=response_data
        )
        
    def _extract_records_from_category(self, category_data: Dict[str, Any], 
                                     category_code: str) -> List[Dict[str, Any]]:
        """Extract individual records from category data."""
        records = category_data.get('records', {})
        
        # Different categories have different record containers
        record_containers = {
            'book': 'work',
            'image': 'work', 
            'magazine': 'work',
            'music': 'work',
            'diary': 'work',
            'research': 'work',
            'newspaper': 'article',
            'people': 'people',
            'list': 'list'
        }
        
        container = record_containers.get(category_code, 'work')
        return records.get(container, [])
        
    def _copy_category_limits(self, source: SearchParameters, 
                            dest: SearchParameters, category: str) -> None:
        """Copy category-specific limit parameters."""
        
        # Category-specific parameter mappings
        category_limits = {
            'book': ['l_format', 'l_decade', 'l_year', 'l_language', 'l_availability', 'l_australian'],
            'newspaper': ['l_decade', 'l_year', 'l_month', 'l_state', 'l_artType', 'l_category', 'l_illustrated'],
            'image': ['l_format', 'l_decade', 'l_year', 'l_artType', 'l_zoom', 'l_geocoverage'],
            'people': ['l_place', 'l_occupation', 'l_birth', 'l_death', 'l_artType'],
            # ... other category mappings
        }
        
        applicable_limits = category_limits.get(category, [])
        
        for limit_param in applicable_limits:
            if hasattr(source, limit_param):
                value = getattr(source, limit_param)
                if value:  # Only copy non-empty values
                    setattr(dest, limit_param, value)
                    
        # Copy other limits that might apply
        dest.otherLimits.update(source.otherLimits)
```

### 3. Enhanced Caching (`trove/cache.py` - additions)

```python
# Additional TTL logic for search results
class SearchCacheBackend(CacheBackend):
    """Cache backend with search-specific TTL logic."""
    
    def __init__(self, backend: CacheBackend):
        self._backend = backend
        
    def _determine_search_ttl(self, params: Dict[str, Any], response: Dict[str, Any]) -> int:
        """Determine TTL based on search characteristics."""
        base_ttl = 900  # 15 minutes default
        
        # Shorter TTL for:
        # - Very recent content (might change frequently)  
        # - Coming soon results
        # - Small result sets (more likely to change)
        
        categories = response.get('category', [])
        total_results = sum(cat.get('records', {}).get('total', 0) for cat in categories)
        
        if total_results < 10:
            return base_ttl // 3  # 5 minutes for small result sets
            
        # Check for "coming soon" content
        for category in categories:
            records = category.get('records', {})
            for record_type in ['work', 'article', 'people', 'list']:
                for record in records.get(record_type, []):
                    if record.get('status') == 'coming soon':
                        return 300  # 5 minutes for coming soon content
                        
        # Longer TTL for bulk harvest (more stable)
        if params.get('bulkHarvest') == 'true':
            return base_ttl * 4  # 1 hour
            
        return base_ttl
        
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
           search_params: Optional[Dict[str, Any]] = None) -> None:
        """Set with dynamic TTL calculation for search results."""
        if ttl is None and search_params and '/result' in key:
            ttl = self._determine_search_ttl(search_params, value)
        
        self._backend.set(key, value, ttl or 900)
```

## Testing Strategy

### Unit Tests

```python
# test_search.py
import pytest
from trove.resources.search import SearchResource
from trove.params import SearchParameters, ParameterBuilder
from trove.exceptions import ValidationError

def test_parameter_validation():
    """Test parameter validation logic."""
    params = SearchParameters()
    
    # Should fail without categories
    with pytest.raises(ValueError, match="category is required"):
        params.validate()
    
    # Should fail with invalid category
    params.category = ['invalid_category']
    with pytest.raises(ValueError, match="Invalid categories"):
        params.validate()
        
def test_parameter_dependencies():
    """Test parameter dependency validation."""
    params = SearchParameters(category=['newspaper'])
    
    # Month requires year
    params.l_month = ['03']
    with pytest.raises(ValueError, match="l-month requires l-year"):
        params.validate()
        
    # For newspapers, year requires decade
    params.l_year = ['2015']
    with pytest.raises(ValueError, match="l-year requires l-decade"):
        params.validate()
        
def test_parameter_builder():
    """Test fluent parameter builder."""
    params = (ParameterBuilder()
             .categories('book', 'image')
             .query('Australian history')
             .decade('200', '199')
             .page_size(50)
             .bulk_harvest()
             .build())
    
    assert params.category == ['book', 'image']
    assert params.q == 'Australian history'
    assert params.l_decade == ['200', '199']
    assert params.n == 50
    assert params.bulkHarvest == True

@pytest.mark.parametrize("categories,should_raise", [
    (['book'], False),
    (['book', 'image'], True),
    (['all'], False),
])
def test_single_category_validation(categories, should_raise):
    """Test single category validation for iterators."""
    search = SearchResource(Mock())
    
    if should_raise:
        with pytest.raises(ValidationError):
            list(search.iter_pages(category=categories, q='test'))
    else:
        # Should not raise (though will fail on actual API call in this test)
        pass
```

### Integration Tests

```python
# test_search_integration.py
import pytest
import os
from trove.config import TroveConfig
from trove.transport import TroveTransport
from trove.cache import MemoryCache
from trove.resources.search import SearchResource

@pytest.mark.integration
class TestSearchIntegration:
    """Integration tests with real Trove API."""
    
    @pytest.fixture(scope="class")
    def search_resource(self):
        api_key = os.environ.get('TROVE_API_KEY')
        if not api_key:
            pytest.skip("TROVE_API_KEY not set")
            
        config = TroveConfig(api_key=api_key, rate_limit=1.0)
        cache = MemoryCache()
        transport = TroveTransport(config, cache)
        return SearchResource(transport)
    
    def test_basic_search(self, search_resource):
        """Test basic search functionality."""
        result = search_resource.page(
            category=['book'],
            q='Australian history',
            n=5
        )
        
        assert result.total_results > 0
        assert len(result.categories) == 1
        assert result.categories[0]['code'] == 'book'
        assert 'work' in result.categories[0]['records']
        
    def test_multi_category_search(self, search_resource):
        """Test multi-category search."""
        result = search_resource.page(
            category=['book', 'image'],
            q='Sydney',
            n=10
        )
        
        assert len(result.categories) == 2
        category_codes = {cat['code'] for cat in result.categories}
        assert 'book' in category_codes
        assert 'image' in category_codes
        
    def test_limit_parameters(self, search_resource):
        """Test various limit parameters."""
        result = search_resource.page(
            category=['book'],
            q='history',
            l_decade=['200'],
            l_availability=['y'],
            l_australian='y',
            n=5
        )
        
        # Should return results (exact assertions depend on data)
        assert result.categories[0]['records']['total'] >= 0
        
    def test_faceting(self, search_resource):
        """Test facet requests."""
        result = search_resource.page(
            category=['book'],
            q='literature',
            facet=['decade', 'format', 'language'],
            n=1
        )
        
        facets = result.categories[0].get('facets', {})
        assert 'facet' in facets
        facet_names = {f['name'] for f in facets['facet']}
        assert 'decade' in facet_names
        
    def test_pagination_single_category(self, search_resource):
        """Test single-category pagination."""
        pages = list(search_resource.iter_pages(
            category=['book'],
            q='test',
            n=10
        ))
        
        # Should get at least one page
        assert len(pages) >= 1
        
        # If multiple pages, check cursor progression
        if len(pages) > 1:
            first_page = pages[0]
            second_page = pages[1]
            assert first_page.cursors != second_page.cursors
            
    def test_multi_category_pagination(self, search_resource):
        """Test multi-category pagination handling."""
        results = list(search_resource.iter_pages_by_category(
            category=['book', 'newspaper'],
            q='federation',
            n=5
        ))
        
        # Should get results for each category
        category_codes = {category_code for category_code, _ in results}
        assert len(category_codes) >= 1  # At least one category should have results
        
    def test_record_iteration(self, search_resource):
        """Test individual record iteration."""
        records = list(search_resource.iter_records(
            category=['book'],
            q='poetry',
            n=20
        ))
        
        # Should get individual record objects
        if records:  # If any records found
            assert isinstance(records[0], dict)
            assert 'title' in records[0] or 'heading' in records[0]
            
    def test_bulk_harvest_mode(self, search_resource):
        """Test bulk harvest functionality."""
        result = search_resource.page(
            category=['book'],
            q='*',  # All records
            l_australian='y',
            bulkHarvest=True,
            n=10
        )
        
        # Should return results sorted by identifier
        assert result.categories[0]['records']['total'] >= 0
        
    def test_parameter_builder_integration(self, search_resource):
        """Test parameter builder with real API."""
        params = (search_resource.build_params()
                 .categories('book')
                 .query('Melbourne')
                 .decade('200')
                 .page_size(15)
                 .facets('format', 'language')
                 .build())
                 
        result = search_resource.page(params)
        assert result.total_results >= 0
```

## Performance Testing

```python
# test_performance.py
import time
import pytest
from concurrent.futures import ThreadPoolExecutor

@pytest.mark.performance
class TestSearchPerformance:
    """Performance tests for search operations."""
    
    def test_search_response_time(self, search_resource):
        """Test that searches complete within reasonable time."""
        start_time = time.time()
        
        result = search_resource.page(
            category=['book'],
            q='test',
            n=20
        )
        
        duration = time.time() - start_time
        assert duration < 5.0  # Should complete within 5 seconds
        
    def test_cached_search_performance(self, search_resource):
        """Test that cached searches are significantly faster."""
        params = {'category': ['book'], 'q': 'cache_test', 'n': 10}
        
        # First request (uncached)
        start_time = time.time()
        result1 = search_resource.page(**params)
        uncached_duration = time.time() - start_time
        
        # Second request (should be cached)
        start_time = time.time() 
        result2 = search_resource.page(**params)
        cached_duration = time.time() - start_time
        
        assert cached_duration < uncached_duration * 0.5  # At least 50% faster
        assert result1.response_data == result2.response_data
        
    def test_concurrent_searches(self, search_resource):
        """Test concurrent search performance."""
        def make_search(query_suffix):
            return search_resource.page(
                category=['book'],
                q=f'test_{query_suffix}',
                n=5
            )
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_search, i) for i in range(5)]
            results = [future.result() for future in futures]
            
        duration = time.time() - start_time
        
        # Should complete all searches without timeout
        assert len(results) == 5
        assert all(result.total_results >= 0 for result in results)
        # Should respect rate limiting but use concurrency effectively
        assert duration < 15.0  # Reasonable for 5 searches with rate limiting
```

## Definition of Done

Stage 2 is complete when:

- ✅ **Complete parameter support** - All 60+ search parameters supported
- ✅ **Single-category pagination** - iter_pages and iter_records work reliably
- ✅ **Multi-category handling** - iter_pages_by_category handles complexity
- ✅ **Parameter validation** - All dependencies and constraints enforced
- ✅ **Faceting support** - Facet requests and response parsing work
- ✅ **Bulk harvest mode** - Supports systematic harvesting workflows
- ✅ **Persistent caching** - SQLite cache with appropriate TTL
- ✅ **Error handling** - Graceful handling of API errors during pagination
- ✅ **Performance** - Meets response time and caching targets
- ✅ **Documentation** - All methods documented with examples
- ✅ **Tests passing** - Integration tests with real API data
- ✅ **Examples working** - All documented examples execute successfully

This comprehensive search implementation provides the robust foundation needed for both simple queries and complex research workflows.