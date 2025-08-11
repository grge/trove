"""Integration tests requiring real API key and network access."""

import time

import pytest

from trove.cache import MemoryCache
from trove.transport import TroveTransport


@pytest.mark.integration
class TestTroveIntegration:
    """Integration tests requiring real API key."""

    @pytest.fixture
    def transport(self, integration_config):
        """Create transport with real configuration for integration testing."""
        cache = MemoryCache()
        transport = TroveTransport(integration_config, cache)
        yield transport
        transport.close()

    def test_basic_search_request(self, transport):
        """Test basic search functionality with real API."""
        response = transport.get('/result', {
            'category': 'book',
            'q': 'Australian history',
            'n': 5,
            'encoding': 'json'
        })

        # Verify response structure
        assert 'category' in response
        assert len(response['category']) > 0

        category = response['category'][0]
        assert 'name' in category
        assert 'records' in category
        assert 'total' in category['records']

        # Should have some results
        assert category['records']['total'] > 0

    def test_work_resource_request(self, transport):
        """Test fetching a specific work resource."""
        # First, get a work ID from search results
        search_response = transport.get('/result', {
            'category': 'book',
            'q': 'Australian',
            'n': 1,
            'encoding': 'json'
        })

        # Extract first work ID
        works = search_response['category'][0]['records'].get('work', [])
        if not works:
            pytest.skip("No works found in search results")

        work_id = works[0]['id']

        # Fetch the specific work
        work_response = transport.get(f'/work/{work_id}', {
            'encoding': 'json',
            'reclevel': 'brief'
        })

        assert 'id' in work_response
        assert work_response['id'] == work_id

    def test_caching_reduces_api_calls(self, transport):
        """Test that caching actually reduces API calls."""
        params = {'category': 'book', 'q': 'caching_test', 'n': 1}

        # First request - should be slower (network)
        start_time = time.time()
        response1 = transport.get('/result', params)
        first_duration = time.time() - start_time

        # Second request - should be faster (cached)
        start_time = time.time()
        response2 = transport.get('/result', params)
        second_duration = time.time() - start_time

        # Responses should be identical
        assert response1 == response2

        # Cached response should be significantly faster
        # (allowing some margin for variability)
        assert second_duration < first_duration * 0.5

    def test_rate_limiting_enforced(self, transport):
        """Test that rate limiting is properly enforced."""
        start_time = time.time()

        # Make multiple requests that should trigger rate limiting
        for i in range(3):
            transport.get('/result', {
                'category': 'book',
                'q': f'rate_limit_test_{i}',
                'n': 1
            })

        duration = time.time() - start_time

        # With rate limit of 1 req/sec and burst=2, first 2 requests are immediate,
        # 3rd request must wait ~1 second
        assert duration >= 0.8  # Allow some margin for timing variations

    def test_different_encodings(self, transport):
        """Test requesting different response encodings."""
        params = {'category': 'book', 'q': 'encoding test', 'n': 1}

        # Test JSON encoding
        json_response = transport.get('/result', {**params, 'encoding': 'json'})
        assert isinstance(json_response, dict)
        assert 'category' in json_response

        # Test XML encoding (returns wrapped response)
        xml_response = transport.get('/result', {**params, 'encoding': 'xml'})
        assert 'xml_content' in xml_response
        assert 'content_type' in xml_response
        assert xml_response['content_type'] == 'xml'

    def test_search_parameters(self, transport):
        """Test various search parameters work correctly."""
        # Test basic text search
        response = transport.get('/result', {
            'category': 'book',
            'q': 'history',
            'n': 3
        })
        assert len(response['category'][0]['records'].get('work', [])) <= 3

        # Test with facets
        response = transport.get('/result', {
            'category': 'book',
            'q': 'australia',
            'facet': 'format,decade',
            'n': 2
        })

        # Should include facet information
        category = response['category'][0]
        assert 'facets' in category

    def test_error_handling_with_real_api(self, transport):
        """Test error handling with real API responses."""
        # Test invalid work ID (should return 404-like response or empty result)
        try:
            response = transport.get('/work/nonexistent_work_id_12345')
            # Some invalid IDs might return empty responses rather than 404
            assert response is not None
        except Exception as e:
            # If it does raise an exception, it should be a proper Trove exception
            from trove.exceptions import TroveError
            assert isinstance(e, TroveError)

    @pytest.mark.asyncio
    async def test_async_requests(self, integration_config):
        """Test async request functionality."""
        cache = MemoryCache()
        async with TroveTransport(integration_config, cache) as transport:
            response = await transport.aget('/result', {
                'category': 'book',
                'q': 'async test',
                'n': 2
            })

            assert 'category' in response
            assert len(response['category']) > 0
