"""Search resource for comprehensive Trove API v3 search functionality."""

from typing import Dict, Any, List, Optional, Iterator, AsyncIterator, Tuple, Union
from dataclasses import dataclass
import logging
import warnings

from ..transport import TroveTransport
from ..params import SearchParameters
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
        """Extract cursors from response for each category."""
        self.cursors = {}
        for category in self.categories:
            if 'records' in category and 'nextStart' in category['records']:
                next_start = category['records']['nextStart']
                if next_start is not None:  # Only add non-None cursors
                    self.cursors[category['code']] = next_start


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
            
            # Using SearchParameters object
            params = SearchParameters(category=['book'], q='poetry')
            result = search.page(params=params)
        """
        # Handle SearchParameters object
        if 'params' in kwargs and isinstance(kwargs['params'], SearchParameters):
            params = kwargs['params']
        elif len(kwargs) == 1 and isinstance(list(kwargs.values())[0], SearchParameters):
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
        # Handle SearchParameters object
        if 'params' in kwargs and isinstance(kwargs['params'], SearchParameters):
            params = kwargs['params']
        elif len(kwargs) == 1 and isinstance(list(kwargs.values())[0], SearchParameters):
            params = list(kwargs.values())[0]
        else:
            # Convert kwargs to SearchParameters
            params = self._kwargs_to_params(kwargs)
            
        params.validate()
        query_params = params.to_query_params()
        
        logger.info(f"Async search request: categories={params.category}, query='{params.q}', n={params.n}")
        
        try:
            response_data = await self.transport.aget('/result', query_params)
            
            # Parse response into SearchResult
            result = self._parse_search_response(response_data, params)
            
            logger.info(f"Async search completed: {result.total_results} total results across {len(result.categories)} categories")
            
            return result
            
        except Exception as e:
            logger.error(f"Async search failed: {e}")
            raise
        
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
        page_count = 0
        
        while True:
            # Update cursor for this request
            params.s = current_cursor
            
            try:
                result = self.page(params=params)
                page_count += 1
                yield result
                
                logger.debug(f"Retrieved page {page_count} for category {category_code}")
                
                # Check if there are more pages
                if category_code not in result.cursors:
                    logger.info(f"Pagination complete for {category_code}: {page_count} pages retrieved")
                    break  # No more pages
                    
                current_cursor = result.cursors[category_code]
                
            except TroveAPIError as e:
                logger.warning(f"Pagination stopped due to API error: {e}")
                break
                
    async def aiter_pages(self, **kwargs) -> AsyncIterator[SearchResult]:
        """Async version of iter_pages."""
        params = self._kwargs_to_params(kwargs)
        
        if len(params.category) > 1:
            raise ValidationError(
                "aiter_pages only supports single-category searches. "
                "Use iter_pages_by_category for multi-category searches."
            )
            
        category_code = params.category[0]
        current_cursor = params.s
        page_count = 0
        
        while True:
            # Update cursor for this request
            params.s = current_cursor
            
            try:
                result = await self.apage(params=params)
                page_count += 1
                yield result
                
                logger.debug(f"Retrieved async page {page_count} for category {category_code}")
                
                # Check if there are more pages
                if category_code not in result.cursors:
                    logger.info(f"Async pagination complete for {category_code}: {page_count} pages retrieved")
                    break  # No more pages
                    
                current_cursor = result.cursors[category_code]
                
            except TroveAPIError as e:
                logger.warning(f"Async pagination stopped due to API error: {e}")
                break
        
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
        total_records = 0
        
        for page_result in self.iter_pages(**kwargs):
            category_data = page_result.categories[0]
            
            # Extract records based on category type
            records = self._extract_records_from_category(category_data, category_code)
            
            for record in records:
                total_records += 1
                yield record
                
        logger.info(f"Retrieved {total_records} total records from category {category_code}")
                
    async def aiter_records(self, **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """Async version of iter_records."""
        params = self._kwargs_to_params(kwargs)
        
        if len(params.category) > 1:
            raise ValidationError(
                "aiter_records only supports single-category searches. "
                "Use iter_pages_by_category for multi-category access."
            )
        
        category_code = params.category[0]
        total_records = 0
        
        async for page_result in self.aiter_pages(**kwargs):
            category_data = page_result.categories[0]
            
            # Extract records based on category type
            records = self._extract_records_from_category(category_data, category_code)
            
            for record in records:
                total_records += 1
                yield record
                
        logger.info(f"Retrieved {total_records} total records from category {category_code} (async)")
                
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
        initial_result = self.page(params=params)
        
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
                for page_result in self.iter_pages(params=single_category_params):
                    yield category_code, page_result
                    
        
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
        
        # Parse records in each category into Pydantic models if available
        parsed_categories = []
        for category in categories:
            parsed_category = category.copy()
            if 'records' in parsed_category:
                parsed_category['records'] = self._parse_category_records(parsed_category['records'])
            parsed_categories.append(parsed_category)
        
        # Calculate total results across all categories
        total_results = sum(
            cat.get('records', {}).get('total', 0) 
            for cat in parsed_categories
        )
        
        return SearchResult(
            query=query,
            categories=parsed_categories,
            total_results=total_results,
            cursors={},  # Will be populated in __post_init__
            response_data=response_data
        )
    
    def _parse_category_records(self, records_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse records within a category into Pydantic models if available."""
        try:
            from ..models import parse_records
            
            # Try to parse with models
            parsed_records = parse_records(records_data)
            if parsed_records:
                # Merge parsed records back into records_data
                updated_records = records_data.copy()
                updated_records.update(parsed_records)
                return updated_records
        except ImportError:
            # Models not available, return raw data
            pass
        except Exception as e:
            logger.debug(f"Failed to parse search records into models: {e}")
        
        return records_data
        
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
            'book': ['l_format', 'l_decade', 'l_year', 'l_language', 'l_availability', 'l_australian',
                    'l_austlanguage', 'l_firstAustralians', 'l_culturalSensitivity', 'l_geocoverage',
                    'l_contribcollection', 'l_partnerNuc', 'l_audience'],
            'newspaper': ['l_decade', 'l_year', 'l_month', 'l_state', 'l_artType', 'l_category', 
                         'l_illustrated', 'l_illustrationType', 'l_wordCount', 'l_format'],
            'image': ['l_format', 'l_decade', 'l_year', 'l_artType', 'l_zoom', 'l_geocoverage',
                     'l_language', 'l_austlanguage', 'l_firstAustralians', 'l_culturalSensitivity',
                     'l_contribcollection', 'l_partnerNuc', 'l_audience'],
            'people': ['l_place', 'l_occupation', 'l_birth', 'l_death', 'l_artType', 'l_australian',
                      'l_firstAustralians', 'l_culturalSensitivity'],
            'magazine': ['l_format', 'l_decade', 'l_year', 'l_language', 'l_austlanguage', 
                        'l_geocoverage', 'l_category', 'l_illustrated', 'l_illustrationType',
                        'l_wordCount', 'l_contribcollection', 'l_partnerNuc'],
            'music': ['l_format', 'l_decade', 'l_year', 'l_language', 'l_austlanguage', 
                     'l_availability', 'l_australian', 'l_firstAustralians', 'l_culturalSensitivity',
                     'l_geocoverage', 'l_contribcollection', 'l_partnerNuc', 'l_audience'],
            'diary': ['l_format', 'l_decade', 'l_year', 'l_language', 'l_austlanguage',
                     'l_availability', 'l_australian', 'l_firstAustralians', 'l_culturalSensitivity',
                     'l_geocoverage', 'l_occupation', 'l_contribcollection', 'l_partnerNuc'],
            'research': ['l_geocoverage', 'l_austlanguage', 'l_title', 'l_illustrated',
                        'l_illustrationType', 'l_wordCount', 'l_contribcollection', 'l_partnerNuc',
                        'l_audience'],
            'list': ['l_decade', 'l_year']
        }
        
        applicable_limits = category_limits.get(category, [])
        
        for limit_param in applicable_limits:
            if hasattr(source, limit_param):
                value = getattr(source, limit_param)
                if value:  # Only copy non-empty values
                    setattr(dest, limit_param, value)
                    
        # Copy other limits that might apply
        dest.otherLimits.update(source.otherLimits)