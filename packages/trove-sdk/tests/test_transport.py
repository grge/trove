"""Unit tests for TroveTransport class."""

from unittest.mock import Mock, patch

import httpx
import pytest

from trove.exceptions import (
    AuthenticationError,
    NetworkError,
    RateLimitError,
)
from trove.transport import TroveTransport


class TestTroveTransport:
    """Test cases for TroveTransport class."""

    @pytest.fixture
    def transport(self, test_config, memory_cache):
        """Create a transport instance for testing."""
        return TroveTransport(test_config, memory_cache)

    def test_build_url(self, transport):
        """Test URL building."""
        url = transport._build_url('/result')
        assert url == 'https://api.trove.nla.gov.au/v3/result'

        # Should handle leading slash
        url = transport._build_url('result')
        assert url == 'https://api.trove.nla.gov.au/v3/result'

    def test_build_headers(self, transport):
        """Test header building."""
        headers = transport._build_headers()
        assert headers['X-API-KEY'] == 'test_api_key_12345'
        assert 'User-Agent' in headers
        assert 'trove-sdk-python' in headers['User-Agent']
        assert headers['Accept'] == 'application/json'

    def test_cache_key_generation(self, transport):
        """Test cache key generation is consistent."""
        # Keys should be the same regardless of parameter order
        key1 = transport._build_cache_key('GET', '/result', {'q': 'test', 'category': 'book'})
        key2 = transport._build_cache_key('GET', '/result', {'category': 'book', 'q': 'test'})
        assert key1 == key2

        # Keys should be different for different parameters
        key3 = transport._build_cache_key('GET', '/result', {'q': 'different', 'category': 'book'})
        assert key1 != key3

    def test_cache_key_excludes_api_key(self, transport):
        """Test that API key is excluded from cache key."""
        key1 = transport._build_cache_key('GET', '/result', {'q': 'test'})
        key2 = transport._build_cache_key('GET', '/result', {'q': 'test', 'key': 'secret_key'})
        assert key1 == key2

    def test_determine_ttl(self, transport):
        """Test TTL determination based on endpoint and content."""
        # Search results should have short TTL
        ttl = transport._determine_ttl('/result', {'category': []})
        assert ttl == transport.config.cache_ttl_search

        # Individual records should have long TTL
        ttl = transport._determine_ttl('/work/123', {'work': {}})
        assert ttl == transport.config.cache_ttl_record

        # Coming soon records should have very short TTL
        ttl = transport._determine_ttl('/work/123', {'status': 'coming soon'})
        assert ttl == transport.config.cache_ttl_coming_soon

    def test_parse_response_json(self, transport):
        """Test JSON response parsing."""
        mock_response = Mock()
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'test': 'data'}

        result = transport._parse_response(mock_response)
        assert result == {'test': 'data'}

    def test_parse_response_xml(self, transport):
        """Test XML response parsing."""
        mock_response = Mock()
        mock_response.headers = {'content-type': 'application/xml'}
        mock_response.text = '<xml>test</xml>'

        result = transport._parse_response(mock_response)
        assert result['xml_content'] == '<xml>test</xml>'
        assert result['content_type'] == 'xml'

    def test_redact_credentials(self, transport):
        """Test credential redaction in logs."""
        params = {'q': 'test', 'key': 'secret_key', 'category': 'book'}
        safe_params = transport._redact_credentials(params)

        assert safe_params['q'] == 'test'
        assert safe_params['category'] == 'book'
        assert safe_params['key'] == '***redacted***'

        # Original params should be unchanged
        assert params['key'] == 'secret_key'

    @patch('httpx.Client.get')
    def test_successful_get_request(self, mock_get, transport):
        """Test successful GET request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {'category': [{'records': {'total': 5}}]}
        mock_response.headers = {'content-type': 'application/json'}
        mock_get.return_value = mock_response

        result = transport.get('/result', {'category': 'book', 'q': 'test'})

        assert result == {'category': [{'records': {'total': 5}}]}
        mock_get.assert_called_once()

    @patch('httpx.Client.get')
    def test_caching_behavior(self, mock_get, transport):
        """Test that responses are cached."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {'test': 'data'}
        mock_response.headers = {'content-type': 'application/json'}
        mock_get.return_value = mock_response

        params = {'category': 'book', 'q': 'test'}

        # First request should hit the API
        result1 = transport.get('/result', params)
        assert mock_get.call_count == 1

        # Second request should use cache
        result2 = transport.get('/result', params)
        assert mock_get.call_count == 1  # Still only one API call
        assert result1 == result2

    @patch('httpx.Client.get')
    def test_authentication_error_handling(self, mock_get, transport):
        """Test handling of authentication errors."""
        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'description': 'Invalid API key'}

        mock_get.side_effect = httpx.HTTPStatusError(
            "Unauthorized",
            request=Mock(),
            response=mock_response
        )

        with pytest.raises(AuthenticationError, match="Invalid API key"):
            transport.get('/result', {'category': 'book'})

    @patch('httpx.Client.get')
    def test_rate_limit_error_handling(self, mock_get, transport):
        """Test handling of rate limit errors."""
        # Mock 429 response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {
            'content-type': 'application/json',
            'Retry-After': '60'
        }
        mock_response.json.return_value = {'description': 'Rate limit exceeded'}

        mock_get.side_effect = httpx.HTTPStatusError(
            "Too Many Requests",
            request=Mock(),
            response=mock_response
        )

        with pytest.raises(RateLimitError) as exc_info:
            transport.get('/result', {'category': 'book'})

        assert exc_info.value.retry_after == '60'

    @patch('httpx.Client.get')
    def test_network_error_handling(self, mock_get, transport):
        """Test handling of network errors."""
        mock_get.side_effect = httpx.ConnectError("Connection failed")

        with pytest.raises(NetworkError, match="Network error"):
            transport.get('/result', {'category': 'book'})

    @patch('httpx.Client.get')
    def test_retry_on_retryable_errors(self, mock_get, transport):
        """Test retry behavior on retryable errors."""
        # First call fails with network error, second succeeds
        mock_response = Mock()
        mock_response.json.return_value = {'test': 'data'}
        mock_response.headers = {'content-type': 'application/json'}

        mock_get.side_effect = [
            httpx.ConnectError("Connection failed"),
            mock_response
        ]

        result = transport.get('/result', {'category': 'book'})
        assert result == {'test': 'data'}
        assert mock_get.call_count == 2

    @patch('httpx.Client.get')
    def test_no_retry_on_non_retryable_errors(self, mock_get, transport):
        """Test no retry on non-retryable errors like authentication."""
        # Mock 401 response (should not retry)
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'description': 'Invalid API key'}

        mock_get.side_effect = httpx.HTTPStatusError(
            "Unauthorized",
            request=Mock(),
            response=mock_response
        )

        with pytest.raises(AuthenticationError):
            transport.get('/result', {'category': 'book'})

        # Should only try once
        assert mock_get.call_count == 1

    def test_context_manager_sync(self, test_config, memory_cache):
        """Test synchronous context manager."""
        with TroveTransport(test_config, memory_cache) as transport:
            assert transport is not None
        # Should close without error

    @pytest.mark.asyncio
    async def test_context_manager_async(self, test_config, memory_cache):
        """Test asynchronous context manager."""
        async with TroveTransport(test_config, memory_cache) as transport:
            assert transport is not None
        # Should close without error

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_async_get_request(self, mock_aget, transport):
        """Test async GET request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {'test': 'async_data'}
        mock_response.headers = {'content-type': 'application/json'}
        mock_aget.return_value = mock_response

        result = await transport.aget('/result', {'category': 'book', 'q': 'test'})

        assert result == {'test': 'async_data'}
        mock_aget.assert_called_once()
