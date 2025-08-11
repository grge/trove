"""Integration tests for search functionality with real Trove API."""

import pytest
import os
import asyncio
from trove.config import TroveConfig
from trove.transport import TroveTransport
from trove.cache import create_cache
from trove.resources.search import SearchResource
from trove.params import SearchParameters
from trove.exceptions import ValidationError


@pytest.mark.integration
class TestSearchIntegration:
    """Integration tests with real Trove API."""
    
    @pytest.fixture(scope="class")
    def search_resource(self):
        """Create search resource with real API configuration."""
        api_key = os.environ.get('TROVE_API_KEY')
        if not api_key:
            pytest.skip("TROVE_API_KEY not set")
            
        config = TroveConfig(api_key=api_key, rate_limit=1.0)  # Slow rate for testing
        cache = create_cache("memory", enhanced=True)
        transport = TroveTransport(config, cache)
        return SearchResource(transport)
    
    def test_basic_search(self, search_resource):
        """Test basic search functionality with real API."""
        result = search_resource.page(
            category=['book'],
            q='Australian history',
            n=5
        )
        
        assert result.total_results > 0
        assert len(result.categories) == 1
        assert result.categories[0]['code'] == 'book'
        assert 'records' in result.categories[0]
        assert 'work' in result.categories[0]['records']
        
        # Should have some books
        works = result.categories[0]['records']['work']
        assert len(works) > 0
        assert 'title' in works[0]
        
    def test_multi_category_search(self, search_resource):
        """Test multi-category search with real API."""
        result = search_resource.page(
            category=['book', 'image'],
            q='Sydney',
            n=10
        )
        
        assert len(result.categories) <= 2  # May not have results in all categories
        category_codes = {cat['code'] for cat in result.categories}
        assert category_codes.issubset({'book', 'image'})
        
        # Check that we have reasonable total results
        assert result.total_results >= 0
        
    def test_search_with_limit_parameters(self, search_resource):
        """Test search with various limit parameters."""
        result = search_resource.page(
            category=['book'],
            q='literature',
            l_decade=['200'],  # 2000s
            l_availability=['y'],  # Online
            l_australian='y',  # Australian content
            n=5
        )
        
        # Should return results (exact count varies)
        assert result.categories[0]['records']['total'] >= 0
        
        # Verify request was processed (should have query in response)
        assert result.query is not None
        
    def test_faceted_search(self, search_resource):
        """Test search with facet requests."""
        result = search_resource.page(
            category=['book'],
            q='Australian literature',
            facet=['decade', 'format', 'language'],
            n=5  # Get a few results to ensure facets are present
        )
        
        # Check for facets in response
        category = result.categories[0]
        # Facets might not always be present, so test gracefully
        if 'facets' in category and category['facets']:
            facets = category['facets']
            if 'facet' in facets:
                # Should have at least one facet
                assert len(facets['facet']) > 0
                
                # Check facet structure
                facet_names = {f['name'] for f in facets['facet']}
                # At least one of the requested facets should be present
                assert len(facet_names.intersection({'decade', 'format', 'language'})) > 0
            
    def test_newspaper_search_with_dependencies(self, search_resource):
        """Test newspaper search with parameter dependencies."""
        result = search_resource.page(
            category=['newspaper'],
            q='federation',
            l_decade=['190'],  # 1900s
            l_year=['1901'],   # Federation year
            l_state=['NSW'],
            n=5
        )
        
        # Should return results from NSW newspapers in 1901
        assert result.categories[0]['records']['total'] >= 0
        
    def test_search_parameters_object(self, search_resource):
        """Test search using SearchParameters object."""
        params = SearchParameters(
            category=['book'],
            q='poetry',
            l_decade=['200'],
            reclevel='full',
            include=['tags'],
            facet=['decade']
        )
        
        result = search_resource.page(params=params)
        
        assert result.total_results >= 0
        assert result.query == 'poetry'
        
    def test_bulk_harvest_mode(self, search_resource):
        """Test bulk harvest functionality."""
        result = search_resource.page(
            category=['book'],
            q='Australia',  # Valid query (not wildcard)
            l_australian='y',  # Limit to Australian content
            bulkHarvest=True,
            n=10
        )
        
        # Should return results sorted by identifier
        assert result.categories[0]['records']['total'] >= 0
        
    def test_pagination_single_category(self, search_resource):
        """Test single-category pagination with real API."""
        # Get first few pages of a broad search
        pages = []
        page_count = 0
        
        for page in search_resource.iter_pages(
            category=['book'],
            q='history',  # Broad search likely to have multiple pages
            n=5  # Small page size to ensure multiple pages
        ):
            pages.append(page)
            page_count += 1
            
            # Limit test to avoid too many API calls
            if page_count >= 3:
                break
                
        # Should get at least one page
        assert len(pages) >= 1
        
        # If we got multiple pages, check cursor progression
        if len(pages) > 1:
            # Each page should have a different cursor state
            cursors = [page.cursors.get('book', '') for page in pages]
            assert len(set(cursors)) > 1  # Should have different cursors
            
    def test_record_iteration(self, search_resource):
        """Test individual record iteration."""
        records = []
        record_count = 0
        
        for record in search_resource.iter_records(
            category=['book'],
            q='Australian poetry',
            n=10
        ):
            records.append(record)
            record_count += 1
            
            # Limit to avoid too many API calls
            if record_count >= 20:
                break
                
        # Should get individual record objects
        if records:  # If any records found
            assert isinstance(records[0], dict)
            # Should have typical work fields
            assert any(field in records[0] for field in ['title', 'heading', 'id'])
            
    def test_multi_category_pagination(self, search_resource):
        """Test multi-category pagination handling."""
        results = []
        
        for category_code, page in search_resource.iter_pages_by_category(
            category=['book', 'newspaper'],
            q='federation',
            n=3
        ):
            results.append((category_code, page))
            
            # Limit to avoid too many API calls
            if len(results) >= 4:
                break
                
        # Should get results for each category that has data
        if results:
            category_codes = {category_code for category_code, _ in results}
            assert len(category_codes) >= 1  # At least one category should have results
            assert category_codes.issubset({'book', 'newspaper'})
            
    def test_error_handling_invalid_parameters(self, search_resource):
        """Test error handling for invalid parameters."""
        # Test missing required category
        with pytest.raises(ValueError, match="category is required"):
            search_resource.page(q='test')
            
        # Test invalid category
        with pytest.raises(ValueError, match="Invalid categories"):
            search_resource.page(category=['invalid_category'], q='test')
            
        # Test pagination error for multiple categories
        with pytest.raises(ValidationError, match="single-category"):
            list(search_resource.iter_pages(
                category=['book', 'image'],
                q='test'
            ))
            
    def test_parameter_dependencies_validation(self, search_resource):
        """Test parameter dependency validation with real API."""
        # Month without year should fail
        with pytest.raises(ValueError, match="l-month requires l-year"):
            search_resource.page(
                category=['newspaper'],
                l_month=['03']
            )
            
        # Newspaper year without decade should fail  
        with pytest.raises(ValueError, match="l-year requires l-decade"):
            search_resource.page(
                category=['newspaper'],
                l_year=['2015']
            )
            
    @pytest.mark.asyncio
    async def test_async_search(self, search_resource):
        """Test async search functionality."""
        result = await search_resource.apage(
            category=['book'],
            q='Australian history',
            n=5
        )
        
        assert result.total_results >= 0
        assert len(result.categories) == 1
        
    @pytest.mark.asyncio  
    async def test_async_pagination(self, search_resource):
        """Test async pagination."""
        pages = []
        page_count = 0
        
        async for page in search_resource.aiter_pages(
            category=['book'],
            q='literature',
            n=5
        ):
            pages.append(page)
            page_count += 1
            
            if page_count >= 2:  # Limit API calls
                break
                
        assert len(pages) >= 1
        
    @pytest.mark.asyncio
    async def test_async_record_iteration(self, search_resource):
        """Test async record iteration."""
        records = []
        record_count = 0
        
        async for record in search_resource.aiter_records(
            category=['book'],
            q='poetry',
            n=10
        ):
            records.append(record)
            record_count += 1
            
            if record_count >= 15:  # Limit API calls
                break
                
        if records:
            assert isinstance(records[0], dict)


@pytest.mark.integration
class TestCacheIntegration:
    """Test enhanced caching with real API."""
    
    @pytest.fixture
    def cached_search_resource(self):
        """Create search resource with enhanced caching."""
        api_key = os.environ.get('TROVE_API_KEY')
        if not api_key:
            pytest.skip("TROVE_API_KEY not set")
            
        config = TroveConfig(api_key=api_key, rate_limit=1.0)
        cache = create_cache("memory", enhanced=True)
        transport = TroveTransport(config, cache)
        return SearchResource(transport)
    
    def test_cache_effectiveness(self, cached_search_resource):
        """Test that caching improves performance."""
        import time
        
        # First request (uncached)
        start_time = time.time()
        result1 = cached_search_resource.page(
            category=['book'],
            q='cache test query',
            n=10
        )
        first_duration = time.time() - start_time
        
        # Second identical request (should be cached)
        start_time = time.time()
        result2 = cached_search_resource.page(
            category=['book'],
            q='cache test query',  # Same query
            n=10
        )
        second_duration = time.time() - start_time
        
        # Results should be identical
        assert result1.total_results == result2.total_results
        assert result1.query == result2.query
        
        # Second request should be significantly faster
        assert second_duration < first_duration * 0.8
        
        # Check cache statistics if available
        transport = cached_search_resource.transport
        if hasattr(transport.cache, 'get_stats'):
            stats = transport.cache.get_stats()
            assert stats['hits'] >= 1
            assert stats['search_requests'] >= 1
            assert stats['hit_rate'] > 0
            
    def test_cache_ttl_behavior(self, cached_search_resource):
        """Test different TTL behavior for different search types."""
        # Small result set (should get short TTL)
        small_result = cached_search_resource.page(
            category=['book'],
            q='very specific unique query 12345',  # Likely to have few results
            n=5
        )
        
        # Large historical search (should get long TTL)
        historical_result = cached_search_resource.page(
            category=['book'],
            q='history',
            l_decade=['180'],  # Historical data
            n=10
        )
        
        # Both should work (TTL testing would require time manipulation)
        assert small_result.total_results >= 0
        assert historical_result.total_results >= 0


@pytest.mark.integration 
class TestPerformanceRequirements:
    """Test that performance requirements are met."""
    
    @pytest.fixture
    def search_resource(self):
        """Search resource for performance testing."""
        api_key = os.environ.get('TROVE_API_KEY')
        if not api_key:
            pytest.skip("TROVE_API_KEY not set")
            
        config = TroveConfig(api_key=api_key, rate_limit=2.0)
        cache = create_cache("memory", enhanced=True)
        transport = TroveTransport(config, cache)
        return SearchResource(transport)
    
    def test_search_response_time(self, search_resource):
        """Test that searches complete within reasonable time."""
        import time
        
        start_time = time.time()
        
        result = search_resource.page(
            category=['book'],
            q='test query',
            n=20
        )
        
        duration = time.time() - start_time
        
        # Should complete within 5 seconds (accounting for network)
        assert duration < 5.0
        assert result.total_results >= 0
        
    def test_cached_search_performance(self, search_resource):
        """Test that cached searches are significantly faster."""
        import time
        
        params = {
            'category': ['book'], 
            'q': 'performance test query',
            'n': 10
        }
        
        # First request (uncached)
        start_time = time.time()
        result1 = search_resource.page(**params)
        uncached_duration = time.time() - start_time
        
        # Second request (should be cached)
        start_time = time.time() 
        result2 = search_resource.page(**params)
        cached_duration = time.time() - start_time
        
        # Results should be identical
        assert result1.total_results == result2.total_results
        
        # Cached request should be much faster
        assert cached_duration < uncached_duration * 0.5
        
    def test_pagination_performance(self, search_resource):
        """Test pagination doesn't degrade significantly."""
        import time
        
        start_time = time.time()
        
        pages = []
        for page in search_resource.iter_pages(
            category=['book'],
            q='test',
            n=10
        ):
            pages.append(page)
            if len(pages) >= 3:  # Test first few pages
                break
                
        duration = time.time() - start_time
        
        # Should handle multiple pages reasonably quickly
        # (accounting for rate limiting)
        assert duration < 10.0
        assert len(pages) >= 1