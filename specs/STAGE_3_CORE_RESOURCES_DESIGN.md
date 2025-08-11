# Stage 3 - Core Resources Design Document

## Overview

Stage 3 implements individual resource access for all Trove record types: works, newspaper/gazette articles, people/organizations, lists, and title records. This provides direct access to detailed record information with full support for include parameters and response formatting.

## API Analysis Summary

Based on the API documentation review, the core endpoints are:

- **`/v3/work/{workId}`** - Work records (books, images, maps, music, etc.)
- **`/v3/newspaper/{id}`** - Newspaper articles  
- **`/v3/gazette/{id}`** - Gazette articles
- **`/v3/people/{id}`** - People and organization records
- **`/v3/list/{id}`** - User-created lists
- **Title endpoints** - Newspaper, magazine, and gazette titles

Each endpoint supports `include`, `reclevel`, and `encoding` parameters with different available include options per resource type.

## Architecture Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Resource Interfaces                            │
├─────────────────────────────────────────────────────────────────────┤
│  WorkResource │ ArticleResource │ PeopleResource │ ListResource │ ... │
├──────────────┬───────────────────┬────────────────┬──────────────┬─────┤
│        BaseResource (common functionality)                          │
├─────────────────────────────────────────────────────────────────────┤
│                  Transport Layer (Stage 1)                         │
└─────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Design

### 1. Base Resource Class (`trove/resources/base.py`)

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import logging
from ..transport import TroveTransport
from ..exceptions import ResourceNotFoundError, ValidationError, TroveAPIError

logger = logging.getLogger(__name__)

class RecLevel(Enum):
    BRIEF = "brief"
    FULL = "full"

class Encoding(Enum):
    JSON = "json"
    XML = "xml"

class BaseResource(ABC):
    """Base class for all resource types with common functionality."""
    
    def __init__(self, transport: TroveTransport):
        self.transport = transport
        
    @property
    @abstractmethod
    def endpoint_path(self) -> str:
        """The API endpoint path for this resource type."""
        pass
        
    @property
    @abstractmethod  
    def valid_include_options(self) -> List[str]:
        """Valid include options for this resource type."""
        pass
        
    def get(self, resource_id: Union[str, int], 
           include: Optional[List[str]] = None,
           reclevel: Union[str, RecLevel] = RecLevel.BRIEF,
           encoding: Union[str, Encoding] = Encoding.JSON) -> Dict[str, Any]:
        """Get a single resource by ID.
        
        Args:
            resource_id: The resource identifier
            include: Optional fields to include in response
            reclevel: Level of detail (brief or full)  
            encoding: Response format (json or xml)
            
        Returns:
            Resource data as dictionary
            
        Raises:
            ResourceNotFoundError: Resource doesn't exist
            ValidationError: Invalid parameters
            TroveAPIError: Other API errors
        """
        # Validate and normalize parameters
        include = self._validate_include_params(include or [])
        reclevel = self._normalize_reclevel(reclevel)
        encoding = self._normalize_encoding(encoding)
        
        # Build request parameters
        params = {
            'reclevel': reclevel.value,
            'encoding': encoding.value
        }
        
        if include:
            params['include'] = ','.join(include)
            
        # Construct endpoint URL
        endpoint = f"{self.endpoint_path}/{resource_id}"
        
        try:
            logger.info(f"Fetching {self.__class__.__name__} {resource_id} with reclevel={reclevel.value}")
            
            response = self.transport.get(endpoint, params)
            
            # Post-process response if needed
            return self._post_process_response(response, resource_id)
            
        except TroveAPIError as e:
            if e.status_code == 404:
                raise ResourceNotFoundError(f"Resource {resource_id} not found") from e
            raise
            
    async def aget(self, resource_id: Union[str, int],
                  include: Optional[List[str]] = None, 
                  reclevel: Union[str, RecLevel] = RecLevel.BRIEF,
                  encoding: Union[str, Encoding] = Encoding.JSON) -> Dict[str, Any]:
        """Async version of get method."""
        # Similar implementation using transport.aget
        include = self._validate_include_params(include or [])
        reclevel = self._normalize_reclevel(reclevel)
        encoding = self._normalize_encoding(encoding)
        
        params = {
            'reclevel': reclevel.value,
            'encoding': encoding.value
        }
        
        if include:
            params['include'] = ','.join(include)
            
        endpoint = f"{self.endpoint_path}/{resource_id}"
        
        try:
            response = await self.transport.aget(endpoint, params)
            return self._post_process_response(response, resource_id)
            
        except TroveAPIError as e:
            if e.status_code == 404:
                raise ResourceNotFoundError(f"Resource {resource_id} not found") from e
            raise
    
    def _validate_include_params(self, include: List[str]) -> List[str]:
        """Validate include parameters against valid options."""
        valid_options = set(self.valid_include_options)
        invalid_options = set(include) - valid_options
        
        if invalid_options:
            valid_str = ', '.join(sorted(valid_options))
            invalid_str = ', '.join(sorted(invalid_options))
            raise ValidationError(
                f"Invalid include options: {invalid_str}. "
                f"Valid options for {self.__class__.__name__}: {valid_str}"
            )
            
        return include
        
    def _normalize_reclevel(self, reclevel: Union[str, RecLevel]) -> RecLevel:
        """Normalize reclevel parameter to enum."""
        if isinstance(reclevel, str):
            try:
                return RecLevel(reclevel.lower())
            except ValueError:
                raise ValidationError(f"Invalid reclevel: {reclevel}. Must be 'brief' or 'full'")
        return reclevel
        
    def _normalize_encoding(self, encoding: Union[str, Encoding]) -> Encoding:
        """Normalize encoding parameter to enum.""" 
        if isinstance(encoding, str):
            try:
                return Encoding(encoding.lower())
            except ValueError:
                raise ValidationError(f"Invalid encoding: {encoding}. Must be 'json' or 'xml'")
        return encoding
        
    def _post_process_response(self, response: Dict[str, Any], resource_id: Union[str, int]) -> Dict[str, Any]:
        """Post-process response data. Override in subclasses if needed."""
        return response
```

### 2. Work Resource (`trove/resources/work.py`)

```python
from typing import Dict, Any, List
from .base import BaseResource

class WorkResource(BaseResource):
    """Resource for accessing work records (books, images, maps, music, etc.)."""
    
    @property
    def endpoint_path(self) -> str:
        return "/work"
        
    @property
    def valid_include_options(self) -> List[str]:
        return [
            'all', 'comments', 'holdings', 'links', 'lists', 
            'subscribinglibs', 'tags', 'workversions'
        ]
        
    def _post_process_response(self, response: Dict[str, Any], work_id) -> Dict[str, Any]:
        """Post-process work response to extract work data."""
        # Work responses are wrapped in a 'work' container
        if 'work' in response:
            work_data = response['work']
            # Ensure work ID is present (it's in XML attributes)
            if isinstance(work_data, dict) and 'id' not in work_data:
                work_data['id'] = str(work_id)
            return work_data
        return response
        
    def get_versions(self, work_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Get all versions of a work.
        
        Args:
            work_id: Work identifier
            
        Returns:
            List of version dictionaries
        """
        work = self.get(work_id, include=['workversions'], reclevel='full')
        
        versions = []
        if 'version' in work:
            version_data = work['version']
            # Handle both single version and list of versions
            if isinstance(version_data, dict):
                versions = [version_data]
            elif isinstance(version_data, list):
                versions = version_data
                
        return versions
        
    def get_holdings(self, work_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Get library holdings for a work.
        
        Args:
            work_id: Work identifier
            
        Returns:
            List of holding dictionaries
        """
        work = self.get(work_id, include=['holdings'], reclevel='full')
        
        holdings = []
        if 'holding' in work:
            holding_data = work['holding']
            if isinstance(holding_data, dict):
                holdings = [holding_data] 
            elif isinstance(holding_data, list):
                holdings = holding_data
                
        return holdings
```

### 3. Article Resource (`trove/resources/article.py`)

```python
from typing import Dict, Any, List, Union, Optional
from .base import BaseResource

class ArticleResource(BaseResource):
    """Resource for accessing newspaper and gazette articles."""
    
    def __init__(self, transport, article_type: str = 'newspaper'):
        """Initialize article resource.
        
        Args:
            transport: Transport layer
            article_type: 'newspaper' or 'gazette'
        """
        super().__init__(transport)
        self.article_type = article_type
        
    @property
    def endpoint_path(self) -> str:
        return f"/{self.article_type}"
        
    @property
    def valid_include_options(self) -> List[str]:
        return ['all', 'articletext', 'comments', 'lists', 'tags']
        
    def _post_process_response(self, response: Dict[str, Any], article_id) -> Dict[str, Any]:
        """Post-process article response."""
        # Article responses are wrapped in 'article' container
        if 'article' in response:
            article_data = response['article']
            if isinstance(article_data, dict) and 'id' not in article_data:
                article_data['id'] = str(article_id)
            return article_data
        return response
        
    def get_full_text(self, article_id: Union[str, int]) -> Optional[str]:
        """Get full text of an article.
        
        Args:
            article_id: Article identifier
            
        Returns:
            Full text content or None if not available
        """
        article = self.get(article_id, include=['articletext'])
        return article.get('articleText')
        
    def get_pdf_urls(self, article_id: Union[str, int]) -> List[str]:
        """Get PDF URLs for article pages.
        
        Args:
            article_id: Article identifier
            
        Returns:
            List of PDF URLs
        """
        article = self.get(article_id)
        
        pdf_urls = []
        if 'pdf' in article:
            pdf_data = article['pdf']
            if isinstance(pdf_data, str):
                pdf_urls = [pdf_data]
            elif isinstance(pdf_data, list):
                pdf_urls = pdf_data
                
        return pdf_urls
        
    def is_coming_soon(self, article_id: Union[str, int]) -> bool:
        """Check if article has 'coming soon' status.
        
        Args:
            article_id: Article identifier
            
        Returns:
            True if article is coming soon
        """
        article = self.get(article_id)
        return article.get('status') == 'coming soon'

class NewspaperResource(ArticleResource):
    """Specialized resource for newspaper articles."""
    
    def __init__(self, transport):
        super().__init__(transport, 'newspaper')

class GazetteResource(ArticleResource):
    """Specialized resource for gazette articles."""
    
    def __init__(self, transport):
        super().__init__(transport, 'gazette')
```

### 4. People Resource (`trove/resources/people.py`)

```python
from typing import Dict, Any, List, Union
from .base import BaseResource

class PeopleResource(BaseResource):
    """Resource for accessing people and organization records."""
    
    @property
    def endpoint_path(self) -> str:
        return "/people"
        
    @property
    def valid_include_options(self) -> List[str]:
        return ['all', 'comments', 'lists', 'raweaccpf', 'tags']
        
    def _post_process_response(self, response: Dict[str, Any], person_id) -> Dict[str, Any]:
        """Post-process people response.""" 
        if 'people' in response:
            people_data = response['people']
            if isinstance(people_data, dict) and 'id' not in people_data:
                people_data['id'] = str(person_id)
            return people_data
        return response
        
    def get_biographies(self, person_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Get biographical information for a person/organization.
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            List of biography dictionaries
        """
        person = self.get(person_id, reclevel='full')
        
        biographies = []
        if 'biography' in person:
            bio_data = person['biography']
            if isinstance(bio_data, dict):
                biographies = [bio_data]
            elif isinstance(bio_data, list):
                biographies = bio_data
                
        return biographies
        
    def get_raw_eac_cpf(self, person_id: Union[str, int]) -> Optional[str]:
        """Get raw EAC-CPF XML record.
        
        Args:
            person_id: Person/organization identifier
            
        Returns:
            Raw EAC-CPF XML or None if not available
        """
        person = self.get(person_id, include=['raweaccpf'])
        return person.get('raweaccpf')
        
    def is_person(self, person_id: Union[str, int]) -> bool:
        """Check if record is a person (vs organization)."""
        person = self.get(person_id)
        return person.get('type') == 'person'
        
    def is_organization(self, person_id: Union[str, int]) -> bool:
        """Check if record is an organization."""
        person = self.get(person_id)
        return person.get('type') in ['corporatebody', 'family']
```

### 5. List Resource (`trove/resources/list.py`)

```python
from typing import Dict, Any, List, Union
from .base import BaseResource

class ListResource(BaseResource):
    """Resource for accessing user-created lists."""
    
    @property
    def endpoint_path(self) -> str:
        return "/list"
        
    @property
    def valid_include_options(self) -> List[str]:
        return ['all', 'comments', 'listitems', 'tags']
        
    def _post_process_response(self, response: Dict[str, Any], list_id) -> Dict[str, Any]:
        """Post-process list response."""
        if 'list' in response:
            list_data = response['list']
            if isinstance(list_data, dict) and 'id' not in list_data:
                list_data['id'] = str(list_id)
            return list_data
        return response
        
    def get_items(self, list_id: Union[str, int]) -> List[Dict[str, Any]]:
        """Get all items in a list.
        
        Args:
            list_id: List identifier
            
        Returns:
            List of item dictionaries
        """
        list_data = self.get(list_id, include=['listitems'])
        
        items = []
        if 'listItem' in list_data:
            item_data = list_data['listItem'] 
            if isinstance(item_data, dict):
                items = [item_data]
            elif isinstance(item_data, list):
                items = item_data
                
        return items
        
    def get_creator(self, list_id: Union[str, int]) -> str:
        """Get the username of the list creator."""
        list_data = self.get(list_id)
        return list_data.get('creator') or list_data.get('by', 'unknown')
        
    def get_item_count(self, list_id: Union[str, int]) -> int:
        """Get the number of items in the list."""
        list_data = self.get(list_id)
        return list_data.get('listItemCount', 0)
```

### 6. Title Resources (`trove/resources/titles.py`)

```python
from typing import Dict, Any, List, Union, Optional
from .base import BaseResource

class BaseTitleResource(BaseResource):
    """Base class for title resources (newspaper, magazine, gazette)."""
    
    def __init__(self, transport, title_type: str):
        super().__init__(transport)
        self.title_type = title_type
        
    @property
    def endpoint_path(self) -> str:
        return f"/{self.title_type}/title"
        
    @property
    def valid_include_options(self) -> List[str]:
        # Title endpoints don't use standard include parameters
        return []
        
    def search(self, offset: int = 0, limit: int = 20,
               state: Optional[str] = None,
               place: Optional[List[str]] = None,
               range_param: Optional[str] = None) -> Dict[str, Any]:
        """Search for titles.
        
        Args:
            offset: Starting index for results
            limit: Number of results to return
            state: Filter by state (newspapers/gazettes only)
            place: Filter by place
            range_param: Date range for issue information
            
        Returns:
            Search results containing titles
        """
        params = {
            'offset': offset,
            'limit': min(limit, 100),  # API maximum
            'encoding': 'json'
        }
        
        if state:
            params['state'] = state
        if place:
            params['place'] = ','.join(place) if isinstance(place, list) else place
        if range_param:
            params['range'] = range_param
            
        endpoint = f"/{self.title_type}/titles"
        return self.transport.get(endpoint, params)
        
    def get(self, title_id: Union[str, int],
           include: Optional[List[str]] = None,
           range_param: Optional[str] = None) -> Dict[str, Any]:
        """Get a specific title by ID.
        
        Args:
            title_id: Title identifier
            include: Include options (varies by title type)
            range_param: Date range for issue information
            
        Returns:
            Title information
        """
        params = {'encoding': 'json'}
        
        if include and 'years' in include:
            params['include'] = 'years'
        if range_param:
            params['range'] = range_param
            
        endpoint = f"{self.endpoint_path}/{title_id}"
        return self.transport.get(endpoint, params)

class NewspaperTitleResource(BaseTitleResource):
    """Resource for newspaper title information."""
    
    def __init__(self, transport):
        super().__init__(transport, 'newspaper')
        
    def search(self, offset: int = 0, limit: int = 20,
               state: Optional[str] = None,
               place: Optional[List[str]] = None) -> Dict[str, Any]:
        """Search newspaper titles."""
        return super().search(offset, limit, state, place)

class MagazineTitleResource(BaseTitleResource):
    """Resource for magazine title information."""
    
    def __init__(self, transport):
        super().__init__(transport, 'magazine')

class GazetteTitleResource(BaseTitleResource):
    """Resource for gazette title information."""
    
    def __init__(self, transport):
        super().__init__(transport, 'gazette')
```

### 7. Resource Factory (`trove/resources/__init__.py`)

```python
from typing import Dict, Type
from .base import BaseResource
from .work import WorkResource
from .article import NewspaperResource, GazetteResource
from .people import PeopleResource  
from .list import ListResource
from .titles import NewspaperTitleResource, MagazineTitleResource, GazetteTitleResource
from ..transport import TroveTransport

class ResourceFactory:
    """Factory for creating resource instances."""
    
    def __init__(self, transport: TroveTransport):
        self.transport = transport
        self._resources: Dict[str, BaseResource] = {}
        
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
    'ResourceFactory',
    'WorkResource', 
    'NewspaperResource',
    'GazetteResource', 
    'PeopleResource',
    'ListResource',
    'NewspaperTitleResource',
    'MagazineTitleResource', 
    'GazetteTitleResource'
]
```

## Testing Strategy

### Unit Tests

```python
# test_resources.py
import pytest
from unittest.mock import Mock
from trove.resources.work import WorkResource
from trove.resources.article import NewspaperResource
from trove.exceptions import ResourceNotFoundError, ValidationError

def test_work_resource_basic():
    """Test basic work resource functionality."""
    mock_transport = Mock()
    mock_transport.get.return_value = {
        'work': {
            'title': 'Test Book',
            'contributor': ['Test Author']
        }
    }
    
    work_resource = WorkResource(mock_transport)
    result = work_resource.get('123456')
    
    assert result['title'] == 'Test Book'
    mock_transport.get.assert_called_once_with(
        '/work/123456',
        {'reclevel': 'brief', 'encoding': 'json'}
    )

def test_include_parameter_validation():
    """Test include parameter validation."""
    mock_transport = Mock()
    work_resource = WorkResource(mock_transport)
    
    # Valid include options should work
    work_resource._validate_include_params(['tags', 'comments'])
    
    # Invalid include options should raise error
    with pytest.raises(ValidationError, match="Invalid include options"):
        work_resource._validate_include_params(['invalid_option'])

def test_resource_not_found_handling():
    """Test 404 error handling."""
    mock_transport = Mock()
    mock_transport.get.side_effect = TroveAPIError("Not found", status_code=404)
    
    work_resource = WorkResource(mock_transport)
    
    with pytest.raises(ResourceNotFoundError, match="Resource 999999 not found"):
        work_resource.get('999999')

def test_article_full_text_extraction():
    """Test article full text extraction."""
    mock_transport = Mock()
    mock_transport.get.return_value = {
        'article': {
            'heading': 'Test Article',
            'articleText': '<p>Article content</p>'
        }
    }
    
    article_resource = NewspaperResource(mock_transport)
    full_text = article_resource.get_full_text('12345')
    
    assert full_text == '<p>Article content</p>'
    mock_transport.get.assert_called_once_with(
        '/newspaper/12345',
        {'reclevel': 'brief', 'encoding': 'json', 'include': 'articletext'}
    )
```

### Integration Tests

```python
# test_resources_integration.py
import pytest
import os
from trove.config import TroveConfig
from trove.transport import TroveTransport
from trove.cache import MemoryCache
from trove.resources import ResourceFactory

@pytest.mark.integration
class TestResourcesIntegration:
    """Integration tests with real Trove API."""
    
    @pytest.fixture(scope="class")
    def resource_factory(self):
        api_key = os.environ.get('TROVE_API_KEY')
        if not api_key:
            pytest.skip("TROVE_API_KEY not set")
            
        config = TroveConfig(api_key=api_key, rate_limit=1.0)
        cache = MemoryCache()
        transport = TroveTransport(config, cache)
        return ResourceFactory(transport)
    
    def test_work_resource_real_data(self, resource_factory):
        """Test work resource with real API data.""" 
        work_resource = resource_factory.get_work_resource()
        
        # Use a known work ID (this should exist in Trove)
        work_id = "1234567"  # Replace with actual work ID
        
        try:
            work = work_resource.get(work_id)
            
            # Verify basic work structure
            assert 'title' in work
            assert isinstance(work['title'], str)
            assert len(work['title']) > 0
            
        except ResourceNotFoundError:
            # Skip test if the specific work doesn't exist
            pytest.skip(f"Work {work_id} not found")
            
    def test_newspaper_article_real_data(self, resource_factory):
        """Test newspaper article with real data."""
        newspaper_resource = resource_factory.get_newspaper_resource()
        
        article_id = "18341291"  # Known article from API docs
        
        try:
            article = newspaper_resource.get(article_id)
            
            assert 'heading' in article or 'title' in article
            assert 'date' in article
            
            # Test full text retrieval
            full_text = newspaper_resource.get_full_text(article_id)
            if full_text:
                assert isinstance(full_text, str)
                assert len(full_text) > 0
                
        except ResourceNotFoundError:
            pytest.skip(f"Article {article_id} not found")
            
    def test_people_resource_real_data(self, resource_factory):
        """Test people resource with real data."""
        people_resource = resource_factory.get_people_resource()
        
        # Use a known person ID
        person_id = "1234"  # Replace with actual person ID
        
        try:
            person = people_resource.get(person_id)
            
            assert 'primaryName' in person or 'primaryDisplayName' in person
            assert 'type' in person
            assert person['type'] in ['person', 'corporatebody', 'family']
            
        except ResourceNotFoundError:
            pytest.skip(f"Person {person_id} not found")
            
    def test_list_resource_real_data(self, resource_factory):
        """Test list resource with real data."""
        list_resource = resource_factory.get_list_resource()
        
        list_id = "21922"  # Known list from API docs
        
        try:
            list_data = list_resource.get(list_id)
            
            assert 'title' in list_data
            assert 'creator' in list_data or 'by' in list_data
            
            # Test item retrieval
            items = list_resource.get_items(list_id)
            assert isinstance(items, list)
            
        except ResourceNotFoundError:
            pytest.skip(f"List {list_id} not found")
            
    def test_include_parameters_real_data(self, resource_factory):
        """Test include parameters with real data."""
        work_resource = resource_factory.get_work_resource()
        
        work_id = "1234567"  # Replace with actual work ID
        
        try:
            # Test different include combinations
            work_basic = work_resource.get(work_id)
            work_with_tags = work_resource.get(work_id, include=['tags'])
            work_full = work_resource.get(work_id, include=['all'], reclevel='full')
            
            # Basic response should have core fields
            assert 'title' in work_basic
            
            # Full response should have more detail
            assert len(str(work_full)) >= len(str(work_basic))
            
        except ResourceNotFoundError:
            pytest.skip(f"Work {work_id} not found")
            
    def test_title_resources_real_data(self, resource_factory):
        """Test title resource searches."""
        newspaper_titles = resource_factory.get_newspaper_title_resource()
        
        # Search for newspaper titles
        results = newspaper_titles.search(limit=5, state='nsw')
        
        assert 'results' in results or 'titles' in results
        # Structure depends on actual API response
        
    def test_error_handling_real_api(self, resource_factory):
        """Test error handling with real API."""
        work_resource = resource_factory.get_work_resource()
        
        # Use an ID that definitely doesn't exist
        invalid_id = "999999999999"
        
        with pytest.raises(ResourceNotFoundError):
            work_resource.get(invalid_id)
            
    def test_caching_behavior(self, resource_factory):
        """Test that resources are properly cached."""
        work_resource = resource_factory.get_work_resource()
        
        work_id = "1234567"  # Replace with actual work ID
        
        try:
            # First request
            import time
            start_time = time.time()
            work1 = work_resource.get(work_id)
            first_duration = time.time() - start_time
            
            # Second request (should be cached)
            start_time = time.time()
            work2 = work_resource.get(work_id)
            second_duration = time.time() - start_time
            
            assert work1 == work2
            assert second_duration < first_duration  # Cache should be faster
            
        except ResourceNotFoundError:
            pytest.skip(f"Work {work_id} not found")
```

## Error Handling Strategy

```python
# Enhanced error handling in base resource
class BaseResource(ABC):
    
    def get(self, resource_id: Union[str, int], **kwargs) -> Dict[str, Any]:
        """Enhanced get method with better error handling."""
        try:
            # ... existing implementation ...
            
        except TroveAPIError as e:
            # Map specific error codes to meaningful exceptions
            if e.status_code == 404:
                raise ResourceNotFoundError(
                    f"{self.__class__.__name__} with ID '{resource_id}' not found"
                ) from e
            elif e.status_code == 429:
                # Rate limiting - let it propagate with retry info
                raise
            elif e.status_code >= 500:
                # Server errors - add context
                raise TroveAPIError(
                    f"Server error accessing {self.__class__.__name__} {resource_id}: {e}",
                    status_code=e.status_code
                ) from e
            else:
                # Other client errors - add resource context
                raise TroveAPIError(
                    f"Error accessing {self.__class__.__name__} {resource_id}: {e}",
                    status_code=e.status_code
                ) from e
                
        except Exception as e:
            # Unexpected errors
            raise TroveAPIError(
                f"Unexpected error accessing {self.__class__.__name__} {resource_id}: {e}"
            ) from e
```

## Performance Optimizations

```python
# Batch resource fetching utility
class BatchResourceFetcher:
    """Utility for efficiently fetching multiple resources."""
    
    def __init__(self, resource_factory: ResourceFactory):
        self.factory = resource_factory
        
    async def fetch_works_batch(self, work_ids: List[Union[str, int]], 
                               include: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """Fetch multiple works concurrently."""
        work_resource = self.factory.get_work_resource()
        
        tasks = []
        for work_id in work_ids:
            task = work_resource.aget(work_id, include=include)
            tasks.append((str(work_id), task))
            
        results = {}
        for work_id, task in tasks:
            try:
                results[work_id] = await task
            except ResourceNotFoundError:
                results[work_id] = None
                
        return results
```

## Definition of Done

Stage 3 is complete when:

- ✅ **All core endpoints implemented** - Work, article, people, list, title resources
- ✅ **Include parameters supported** - All documented include options work
- ✅ **Response processing** - Proper extraction and post-processing of responses
- ✅ **Error handling complete** - 404s become ResourceNotFoundError, proper error context
- ✅ **Async support** - All resources have async versions  
- ✅ **Resource factory** - Clean interface for accessing resource instances
- ✅ **Validation** - Include parameter validation, parameter normalization
- ✅ **Performance** - Proper caching, reasonable response times
- ✅ **Tests passing** - Unit and integration tests with real API data
- ✅ **Documentation** - All methods documented with examples
- ✅ **Examples working** - Resource access examples execute successfully

This comprehensive resource implementation provides direct, efficient access to all Trove record types with proper error handling and caching.