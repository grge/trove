"""Tests for search resource functionality."""

import pytest
from unittest.mock import Mock, AsyncMock
from trove.resources.search import SearchResource, SearchResult, PaginationState
from trove.params import SearchParameters
from trove.exceptions import ValidationError, TroveAPIError


class TestSearchResource:
    """Test SearchResource functionality."""
    
    @pytest.fixture
    def mock_transport(self):
        """Mock transport for testing."""
        transport = Mock()
        transport.get = Mock()
        transport.aget = AsyncMock()
        return transport
        
    @pytest.fixture
    def search_resource(self, mock_transport):
        """SearchResource instance for testing."""
        return SearchResource(mock_transport)
        
    @pytest.fixture
    def sample_response(self):
        """Sample API response for testing."""
        return {
            'query': 'test query',
            'category': [
                {
                    'code': 'book',
                    'name': 'Books & Libraries',
                    'records': {
                        'total': 150,
                        'work': [
                            {'id': '1', 'title': 'Test Book 1'},
                            {'id': '2', 'title': 'Test Book 2'}
                        ],
                        'nextStart': 'next_cursor_value'
                    }
                }
            ]
        }
        
    def test_page_with_kwargs(self, search_resource, mock_transport, sample_response):
        """Test page method with keyword arguments."""
        mock_transport.get.return_value = sample_response
        
        result = search_resource.page(
            category=['book'], 
            q='test query', 
            n=10
        )
        
        # Verify transport was called correctly
        mock_transport.get.assert_called_once()
        call_args = mock_transport.get.call_args
        assert call_args[0][0] == '/result'
        
        params = call_args[0][1]
        assert params['category'] == 'book'
        assert params['q'] == 'test query'
        assert params['n'] == 10
        
        # Verify result
        assert isinstance(result, SearchResult)
        assert result.query == 'test query'
        assert len(result.categories) == 1
        assert result.total_results == 150
        assert result.cursors['book'] == 'next_cursor_value'
        
    def test_page_with_search_parameters(self, search_resource, mock_transport, sample_response):
        """Test page method with SearchParameters object."""
        mock_transport.get.return_value = sample_response
        
        params = SearchParameters(
            category=['book'],
            q='test query',
            l_decade=['200'],
            facet=['format', 'decade']
        )
        
        result = search_resource.page(params=params)
        
        # Verify transport was called
        mock_transport.get.assert_called_once()
        call_args = mock_transport.get.call_args[0][1]
        assert call_args['category'] == 'book'
        assert call_args['q'] == 'test query'
        assert call_args['l-decade'] == '200'
        assert call_args['facet'] == 'format,decade'
        
    def test_page_with_complex_parameters(self, search_resource, mock_transport, sample_response):
        """Test page method with complex parameter combinations."""
        mock_transport.get.return_value = sample_response
        
        result = search_resource.page(
            category=['book', 'image'],
            q='Australian history',
            l_decade=['190', '200'],
            l_availability=['y/f'],
            l_firstAustralians='y',
            facet=['decade', 'format', 'language'],
            include=['tags', 'comments'],
            reclevel='full',
            n=50
        )
        
        call_args = mock_transport.get.call_args[0][1]
        assert call_args['category'] == 'book,image'
        assert call_args['l-decade'] == '190,200'
        assert call_args['l-availability'] == 'y/f'
        assert call_args['l-firstAustralians'] == 'y'
        assert call_args['facet'] == 'decade,format,language'
        assert call_args['include'] == 'tags,comments'
        assert call_args['reclevel'] == 'full'
        assert call_args['n'] == 50
        
    def test_page_validation_error(self, search_resource):
        """Test that page method validates parameters."""
        with pytest.raises(ValueError, match="At least one category is required"):
            search_resource.page(q='test')
            
    async def test_apage(self, search_resource, mock_transport, sample_response):
        """Test async page method."""
        mock_transport.aget.return_value = sample_response
        
        result = await search_resource.apage(
            category=['book'],
            q='test query'
        )
        
        # Verify async transport was called
        mock_transport.aget.assert_called_once()
        assert isinstance(result, SearchResult)
        assert result.query == 'test query'


class TestPagination:
    """Test pagination functionality."""
    
    @pytest.fixture
    def mock_transport(self):
        """Mock transport for pagination testing."""
        transport = Mock()
        transport.get = Mock()
        transport.aget = AsyncMock()
        return transport
        
    @pytest.fixture
    def search_resource(self, mock_transport):
        """SearchResource instance for testing."""
        return SearchResource(mock_transport)
        
    def create_mock_response(self, page_num, has_next=True):
        """Create mock response for pagination testing."""
        return {
            'query': 'test query',
            'category': [
                {
                    'code': 'book',
                    'name': 'Books & Libraries',
                    'records': {
                        'total': 100,
                        'work': [
                            {'id': f'{page_num}_1', 'title': f'Book {page_num}_1'},
                            {'id': f'{page_num}_2', 'title': f'Book {page_num}_2'}
                        ],
                        'nextStart': f'cursor_page_{page_num + 1}' if has_next else None
                    }
                }
            ]
        }
        
    def test_iter_pages_single_category(self, search_resource, mock_transport):
        """Test iter_pages with single category."""
        # Mock responses for 3 pages
        responses = [
            self.create_mock_response(1, has_next=True),
            self.create_mock_response(2, has_next=True),
            self.create_mock_response(3, has_next=False)  # Last page
        ]
        call_count = 0
        def mock_get_responses(url, params):
            nonlocal call_count
            if call_count < len(responses):
                result = responses[call_count]
                call_count += 1
                return result
            else:
                raise Exception(f"Test should not make more requests (call {call_count + 1})")
                
        mock_transport.get.side_effect = mock_get_responses
        
        pages = list(search_resource.iter_pages(
            category=['book'],
            q='test query',
            n=2
        ))
        
        assert len(pages) == 3
        assert mock_transport.get.call_count == 3
        
        # Verify cursor progression
        call_args_list = mock_transport.get.call_args_list
        assert call_args_list[0][0][1]['s'] == '*'  # First page
        assert call_args_list[1][0][1]['s'] == 'cursor_page_2'  # Second page
        assert call_args_list[2][0][1]['s'] == 'cursor_page_3'  # Third page
        
    def test_iter_pages_multi_category_error(self, search_resource):
        """Test that iter_pages raises error for multiple categories."""
        with pytest.raises(ValidationError, match="only supports single-category"):
            list(search_resource.iter_pages(
                category=['book', 'image'],
                q='test'
            ))
            
    def test_iter_pages_api_error_handling(self, search_resource, mock_transport):
        """Test iter_pages handles API errors gracefully."""
        # First page succeeds, second fails
        responses = [
            self.create_mock_response(1, has_next=True),
            TroveAPIError("API error")
        ]
        mock_transport.get.side_effect = responses
        
        pages = list(search_resource.iter_pages(
            category=['book'],
            q='test'
        ))
        
        # Should only get the first page before error
        assert len(pages) == 1
        assert mock_transport.get.call_count == 2
        
    async def test_aiter_pages(self, search_resource, mock_transport):
        """Test async page iteration."""
        responses = [
            self.create_mock_response(1, has_next=True),
            self.create_mock_response(2, has_next=False)
        ]
        mock_transport.aget.side_effect = responses
        
        pages = []
        async for page in search_resource.aiter_pages(
            category=['book'],
            q='test'
        ):
            pages.append(page)
            
        assert len(pages) == 2
        assert mock_transport.aget.call_count == 2
        
    def test_iter_records_single_category(self, search_resource, mock_transport):
        """Test iter_records with single category."""
        responses = [
            self.create_mock_response(1, has_next=True),
            self.create_mock_response(2, has_next=False)
        ]
        mock_transport.get.side_effect = responses
        
        records = list(search_resource.iter_records(
            category=['book'],
            q='test'
        ))
        
        # Should get 2 records from each page = 4 total
        assert len(records) == 4
        assert records[0]['id'] == '1_1'
        assert records[1]['id'] == '1_2'
        assert records[2]['id'] == '2_1'
        assert records[3]['id'] == '2_2'
        
    def test_iter_records_multi_category_error(self, search_resource):
        """Test that iter_records raises error for multiple categories."""
        with pytest.raises(ValidationError, match="only supports single-category"):
            list(search_resource.iter_records(
                category=['book', 'image'],
                q='test'
            ))
            
    async def test_aiter_records(self, search_resource, mock_transport):
        """Test async record iteration."""
        responses = [
            self.create_mock_response(1, has_next=False)
        ]
        mock_transport.aget.side_effect = responses
        
        records = []
        async for record in search_resource.aiter_records(
            category=['book'],
            q='test'
        ):
            records.append(record)
            
        assert len(records) == 2
        assert records[0]['id'] == '1_1'


class TestMultiCategoryPagination:
    """Test multi-category pagination functionality."""
    
    @pytest.fixture
    def mock_transport(self):
        """Mock transport for testing."""
        transport = Mock()
        transport.get = Mock()
        return transport
        
    @pytest.fixture
    def search_resource(self, mock_transport):
        """SearchResource instance for testing."""
        return SearchResource(mock_transport)
        
    @pytest.fixture
    def multi_category_response(self):
        """Sample multi-category response."""
        return {
            'query': 'test query',
            'category': [
                {
                    'code': 'book',
                    'name': 'Books & Libraries',
                    'records': {
                        'total': 50,
                        'work': [
                            {'id': 'book_1', 'title': 'Book 1'}
                        ],
                        'nextStart': 'book_cursor_2'
                    }
                },
                {
                    'code': 'image',
                    'name': 'Images, Maps & Artefacts',
                    'records': {
                        'total': 25,
                        'work': [
                            {'id': 'image_1', 'title': 'Image 1'}
                        ],
                        'nextStart': 'image_cursor_2'
                    }
                }
            ]
        }
        
    def test_iter_pages_by_category(self, search_resource, mock_transport, multi_category_response):
        """Test multi-category pagination handling."""
        # Mock initial response and subsequent single-category responses
        book_page_2 = {
            'query': 'test query',
            'category': [
                {
                    'code': 'book',
                    'records': {
                        'total': 50,
                        'work': [{'id': 'book_2'}]
                    }
                }
            ]
        }
        
        image_page_2 = {
            'query': 'test query', 
            'category': [
                {
                    'code': 'image',
                    'records': {
                        'total': 25,
                        'work': [{'id': 'image_2'}]
                    }
                }
            ]
        }
        
        mock_transport.get.side_effect = [
            multi_category_response,  # Initial multi-category response
            book_page_2,             # Book page 2
            image_page_2             # Image page 2
        ]
        
        results = list(search_resource.iter_pages_by_category(
            category=['book', 'image'],
            q='test query'
        ))
        
        # Should get 4 results: book page 1, book page 2, image page 1, image page 2
        assert len(results) == 4
        
        # Check category codes and pages
        categories_and_pages = [(cat, len(page.categories)) for cat, page in results]
        assert categories_and_pages == [
            ('book', 1), ('book', 1),    # Book pages
            ('image', 1), ('image', 1)   # Image pages
        ]
        
        # Verify transport calls
        assert mock_transport.get.call_count == 3


class TestSearchResult:
    """Test SearchResult dataclass."""
    
    def test_search_result_initialization(self):
        """Test SearchResult initialization."""
        categories = [
            {
                'code': 'book',
                'records': {
                    'total': 100,
                    'work': [{'id': '1', 'title': 'Test'}],
                    'nextStart': 'cursor_123'
                }
            }
        ]
        
        result = SearchResult(
            query='test',
            categories=categories,
            total_results=100,
            cursors={},  # Will be populated by __post_init__
            response_data={'query': 'test', 'category': categories}
        )
        
        assert result.query == 'test'
        assert result.total_results == 100
        assert result.cursors['book'] == 'cursor_123'  # Extracted in __post_init__
        
    def test_search_result_no_cursor(self):
        """Test SearchResult when no nextStart cursor."""
        categories = [
            {
                'code': 'book',
                'records': {
                    'total': 5,
                    'work': [{'id': '1'}]
                    # No nextStart - last page
                }
            }
        ]
        
        result = SearchResult(
            query='test',
            categories=categories,
            total_results=5,
            cursors={},
            response_data={}
        )
        
        assert 'book' not in result.cursors  # No cursor extracted


class TestParameterConversion:
    """Test parameter conversion functionality."""
    
    @pytest.fixture
    def search_resource(self):
        """SearchResource for testing parameter conversion."""
        return SearchResource(Mock())
        
    def test_kwargs_to_params_basic(self, search_resource):
        """Test basic parameter conversion."""
        kwargs = {
            'category': ['book'],
            'q': 'test',
            'n': 50,
            'sortby': 'datedesc'
        }
        
        params = search_resource._kwargs_to_params(kwargs)
        
        assert params.category == ['book']
        assert params.q == 'test'
        assert params.n == 50
        assert params.sortby == 'datedesc'
        
    def test_kwargs_to_params_with_limits(self, search_resource):
        """Test parameter conversion with limit parameters."""
        kwargs = {
            'category': ['book'],
            'l_decade': ['200'],
            'l-availability': ['y/f'],  # Hyphen format
            'l_firstAustralians': 'y'
        }
        
        params = search_resource._kwargs_to_params(kwargs)
        
        assert params.l_decade == ['200']
        assert params.l_firstAustralians == 'y'
        # l-availability should be converted to l_availability attribute
        assert params.l_availability == ['y/f']
        
    def test_kwargs_to_params_unknown_limits(self, search_resource):
        """Test handling of unknown limit parameters."""
        kwargs = {
            'category': ['book'],
            'l_unknown_param': ['value'],
            'l-custom-limit': 'custom_value'
        }
        
        params = search_resource._kwargs_to_params(kwargs)
        
        # Unknown parameters should go to otherLimits
        assert params.otherLimits['l-unknown-param'] == ['value']
        assert params.otherLimits['l-custom-limit'] == 'custom_value'


class TestCategoryLimitsMapping:
    """Test category-specific limit parameter mapping."""
    
    @pytest.fixture
    def search_resource(self):
        """SearchResource for testing."""
        return SearchResource(Mock())
        
    def test_copy_category_limits_book(self, search_resource):
        """Test copying limits for book category."""
        source = SearchParameters(
            category=['book', 'image'],
            l_decade=['200'],
            l_availability=['y'],
            l_zoom=['1:50000']  # Image-specific, shouldn't be copied to book
        )
        
        dest = SearchParameters(category=['book'])
        
        search_resource._copy_category_limits(source, dest, 'book')
        
        assert dest.l_decade == ['200']
        assert dest.l_availability == ['y'] 
        assert not dest.l_zoom  # Should not be copied (not applicable to books)
        
    def test_copy_category_limits_newspaper(self, search_resource):
        """Test copying limits for newspaper category."""
        source = SearchParameters(
            category=['newspaper'],
            l_decade=['200'],
            l_state=['NSW'],
            l_illustrated=True,
            l_availability=['y']  # Not applicable to newspapers
        )
        
        dest = SearchParameters(category=['newspaper'])
        
        search_resource._copy_category_limits(source, dest, 'newspaper')
        
        assert dest.l_decade == ['200']
        assert dest.l_state == ['NSW']
        assert dest.l_illustrated == True
        assert not dest.l_availability  # Should not be copied
        
    def test_copy_other_limits(self, search_resource):
        """Test copying of other limits."""
        source = SearchParameters(
            category=['book'],
            otherLimits={'custom-param': 'value', 'another-limit': 'test'}
        )
        
        dest = SearchParameters(category=['book'])
        
        search_resource._copy_category_limits(source, dest, 'book')
        
        assert dest.otherLimits == source.otherLimits


class TestRecordExtraction:
    """Test record extraction from category data."""
    
    @pytest.fixture
    def search_resource(self):
        """SearchResource for testing."""
        return SearchResource(Mock())
        
    def test_extract_records_book_category(self, search_resource):
        """Test record extraction for book category."""
        category_data = {
            'code': 'book',
            'records': {
                'work': [
                    {'id': '1', 'title': 'Book 1'},
                    {'id': '2', 'title': 'Book 2'}
                ]
            }
        }
        
        records = search_resource._extract_records_from_category(category_data, 'book')
        
        assert len(records) == 2
        assert records[0]['id'] == '1'
        assert records[1]['id'] == '2'
        
    def test_extract_records_newspaper_category(self, search_resource):
        """Test record extraction for newspaper category."""
        category_data = {
            'code': 'newspaper',
            'records': {
                'article': [
                    {'id': 'art_1', 'title': 'Article 1'},
                    {'id': 'art_2', 'title': 'Article 2'}
                ]
            }
        }
        
        records = search_resource._extract_records_from_category(category_data, 'newspaper')
        
        assert len(records) == 2
        assert records[0]['id'] == 'art_1'
        
    def test_extract_records_people_category(self, search_resource):
        """Test record extraction for people category."""
        category_data = {
            'code': 'people',
            'records': {
                'people': [
                    {'id': 'person_1', 'name': 'Person 1'}
                ]
            }
        }
        
        records = search_resource._extract_records_from_category(category_data, 'people')
        
        assert len(records) == 1
        assert records[0]['id'] == 'person_1'
        
    def test_extract_records_empty(self, search_resource):
        """Test record extraction with no records."""
        category_data = {
            'code': 'book',
            'records': {}
        }
        
        records = search_resource._extract_records_from_category(category_data, 'book')
        
        assert len(records) == 0