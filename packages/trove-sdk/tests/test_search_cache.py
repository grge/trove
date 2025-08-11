"""Tests for enhanced search caching functionality."""

import pytest
from unittest.mock import Mock, AsyncMock
from trove.cache import SearchCacheBackend, MemoryCache


class TestSearchCacheBackend:
    """Test SearchCacheBackend functionality."""
    
    @pytest.fixture
    def mock_backend(self):
        """Mock cache backend for testing."""
        backend = Mock()
        backend.get = Mock()
        backend.set = Mock()
        backend.aget = AsyncMock()
        backend.aset = AsyncMock()
        return backend
        
    @pytest.fixture
    def search_cache(self, mock_backend):
        """SearchCacheBackend instance for testing."""
        return SearchCacheBackend(mock_backend)
        
    def test_initialization(self, search_cache):
        """Test SearchCacheBackend initialization."""
        stats = search_cache.get_stats()
        
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['sets'] == 0
        assert stats['search_requests'] == 0
        assert stats['total_requests'] == 0
        assert stats['hit_rate'] == 0.0
        
    def test_get_hit_statistics(self, search_cache, mock_backend):
        """Test cache hit statistics tracking."""
        mock_backend.get.return_value = {'test': 'data'}
        
        result = search_cache.get('test_key')
        
        assert result == {'test': 'data'}
        stats = search_cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 0
        assert stats['total_requests'] == 1
        assert stats['hit_rate'] == 1.0
        assert stats['cache_savings_seconds'] == 1.5
        
    def test_get_miss_statistics(self, search_cache, mock_backend):
        """Test cache miss statistics tracking."""
        mock_backend.get.return_value = None
        
        result = search_cache.get('test_key')
        
        assert result is None
        stats = search_cache.get_stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 1
        assert stats['total_requests'] == 1
        assert stats['hit_rate'] == 0.0
        
    async def test_async_get_statistics(self, search_cache, mock_backend):
        """Test async cache hit statistics."""
        mock_backend.aget.return_value = {'async': 'data'}
        
        result = await search_cache.aget('test_key')
        
        assert result == {'async': 'data'}
        stats = search_cache.get_stats()
        assert stats['hits'] == 1
        assert stats['cache_savings_seconds'] == 1.5
        
    def test_set_basic(self, search_cache, mock_backend):
        """Test basic cache set functionality."""
        search_cache.set('key', {'data': 'value'}, ttl=900)
        
        mock_backend.set.assert_called_once_with('key', {'data': 'value'}, 900)
        stats = search_cache.get_stats()
        assert stats['sets'] == 1
        
    def test_set_with_search_params(self, search_cache, mock_backend):
        """Test cache set with search parameters for TTL calculation."""
        response_data = {
            'category': [
                {
                    'code': 'book',
                    'records': {'total': 100, 'work': []}
                }
            ]
        }
        search_params = {'category': 'book', 'q': 'test'}
        
        search_cache.set(
            'search_key', 
            response_data,
            search_params=search_params,
            route='/result'
        )
        
        # Should use default TTL for normal results
        mock_backend.set.assert_called_once()
        args = mock_backend.set.call_args[0]
        assert args[2] == 900  # Default TTL
        
        stats = search_cache.get_stats()
        assert stats['search_requests'] == 1
        
    def test_reset_stats(self, search_cache, mock_backend):
        """Test statistics reset functionality."""
        # Generate some stats
        mock_backend.get.return_value = None
        search_cache.get('key1')
        search_cache.set('key2', 'value')
        
        stats_before = search_cache.get_stats()
        assert stats_before['misses'] > 0
        assert stats_before['sets'] > 0
        
        search_cache.reset_stats()
        
        stats_after = search_cache.get_stats()
        assert stats_after['hits'] == 0
        assert stats_after['misses'] == 0
        assert stats_after['sets'] == 0
        assert stats_after['search_requests'] == 0
        
    def test_route_ttl_configuration(self, search_cache):
        """Test route TTL configuration."""
        # Check default values
        assert search_cache._route_ttl['/result'] == 900
        assert search_cache._route_ttl['/work'] == 3600
        assert search_cache._route_ttl['/people'] == 86400
        
        # Update TTL
        search_cache.set_route_ttl('/result', 1800)
        assert search_cache._route_ttl['/result'] == 1800
        
    def test_ttl_calculation_small_result_set(self, search_cache):
        """Test TTL calculation for small result sets."""
        response_data = {
            'category': [
                {
                    'code': 'book',
                    'records': {'total': 5}  # Small result set
                }
            ]
        }
        params = {'category': 'book'}
        
        ttl = search_cache._determine_search_ttl(params, response_data)
        
        # Should get reduced TTL for small result sets
        assert ttl == 300  # 900 // 3
        
    def test_ttl_calculation_bulk_harvest(self, search_cache):
        """Test TTL calculation for bulk harvest mode."""
        response_data = {
            'category': [
                {
                    'code': 'book',
                    'records': {'total': 100}
                }
            ]
        }
        params = {'bulkHarvest': 'true'}
        
        ttl = search_cache._determine_search_ttl(params, response_data)
        
        # Should get extended TTL for bulk harvest
        assert ttl == 3600  # 900 * 4
        
    def test_ttl_calculation_historical_data(self, search_cache):
        """Test TTL calculation for historical data."""
        response_data = {
            'category': [
                {
                    'code': 'book',
                    'records': {'total': 50}
                }
            ]
        }
        params = {'l-decade': '190,195'}  # Historical decades
        
        ttl = search_cache._determine_search_ttl(params, response_data)
        
        # Should get extended TTL for historical data
        assert ttl == 7200  # 900 * 8
        
    def test_ttl_calculation_coming_soon_content(self, search_cache):
        """Test TTL calculation for dynamic content."""
        response_data = {
            'category': [
                {
                    'code': 'book',
                    'records': {
                        'total': 50,
                        'work': [
                            {'id': '1', 'status': 'coming soon'}
                        ]
                    }
                }
            ]
        }
        params = {'category': 'book'}
        
        ttl = search_cache._determine_search_ttl(params, response_data)
        
        # Should get short TTL for dynamic content
        assert ttl == 300  # 5 minutes
        
    def test_ttl_calculation_non_search_route(self, search_cache):
        """Test TTL calculation for non-search routes."""
        response_data = {'work': {'id': '123'}}
        params = {}
        
        ttl = search_cache._determine_search_ttl(params, response_data, route='/work')
        
        # Should use route-specific default
        assert ttl == 3600  # Default for /work
        
    async def test_async_set(self, search_cache, mock_backend):
        """Test async cache set functionality."""
        await search_cache.aset('key', {'data': 'value'}, ttl=1800)
        
        mock_backend.aset.assert_called_once_with('key', {'data': 'value'}, 1800)
        stats = search_cache.get_stats()
        assert stats['sets'] == 1
        
    def test_mixed_hit_miss_statistics(self, search_cache, mock_backend):
        """Test mixed hit/miss statistics calculation."""
        # Configure mock to return hit, miss, hit
        mock_backend.get.side_effect = [
            {'data': 'hit1'},
            None,  # miss
            {'data': 'hit2'}
        ]
        
        search_cache.get('key1')  # hit
        search_cache.get('key2')  # miss  
        search_cache.get('key3')  # hit
        
        stats = search_cache.get_stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['total_requests'] == 3
        assert abs(stats['hit_rate'] - 2/3) < 1e-10
        assert abs(stats['miss_rate'] - 1/3) < 1e-10
        assert stats['cache_savings_seconds'] == 3.0  # 2 hits * 1.5 seconds each


class TestSearchCacheIntegration:
    """Test SearchCacheBackend integration with real backend."""
    
    @pytest.fixture
    def memory_cache(self):
        """Real MemoryCache for integration testing."""
        return MemoryCache()
        
    @pytest.fixture
    def search_cache(self, memory_cache):
        """SearchCacheBackend with real MemoryCache."""
        return SearchCacheBackend(memory_cache)
        
    def test_end_to_end_caching(self, search_cache):
        """Test end-to-end caching functionality."""
        # First set
        search_cache.set('test_key', {'data': 'value'}, ttl=60)
        
        # First get (should be hit)
        result1 = search_cache.get('test_key')
        assert result1 == {'data': 'value'}
        
        # Second get (should also be hit)
        result2 = search_cache.get('test_key')
        assert result2 == {'data': 'value'}
        
        # Check statistics
        stats = search_cache.get_stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 0
        assert stats['sets'] == 1
        assert stats['hit_rate'] == 1.0
        
    def test_cache_expiration(self, search_cache):
        """Test that cache expiration works correctly."""
        import time
        
        # Set with very short TTL
        search_cache.set('short_key', {'data': 'expires'}, ttl=1)
        
        # Immediate get should work
        result = search_cache.get('short_key')
        assert result == {'data': 'expires'}
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should now be expired
        expired_result = search_cache.get('short_key')
        assert expired_result is None
        
        # Check statistics  
        stats = search_cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        
    def test_search_specific_ttl_integration(self, search_cache):
        """Test search-specific TTL calculation with real backend."""
        # Large result set (should get default TTL)
        large_response = {
            'category': [
                {'code': 'book', 'records': {'total': 1000}}
            ]
        }
        search_cache.set(
            'large_search',
            large_response,
            search_params={'category': 'book'},
            route='/result'
        )
        
        # Small result set (should get reduced TTL)
        small_response = {
            'category': [
                {'code': 'book', 'records': {'total': 2}}
            ]
        }
        search_cache.set(
            'small_search',
            small_response,
            search_params={'category': 'book'},
            route='/result'
        )
        
        # Both should be retrievable immediately
        assert search_cache.get('large_search') == large_response
        assert search_cache.get('small_search') == small_response
        
        stats = search_cache.get_stats()
        assert stats['search_requests'] == 2
        assert stats['hits'] == 2