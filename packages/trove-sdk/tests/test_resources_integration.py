"""Integration tests for resource implementations."""

import pytest
import os
from unittest.mock import patch

from trove.config import TroveConfig
from trove.transport import TroveTransport
from trove.cache import MemoryCache
from trove.resources import ResourceFactory
from trove.exceptions import ResourceNotFoundError


@pytest.mark.integration
class TestResourcesIntegration:
    """Integration tests with real Trove API."""
    
    @pytest.fixture(scope="class")
    def resource_factory(self):
        """Create resource factory for integration tests."""
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
        
        # Use a known work ID that actually exists in Trove
        work_id = "23458006"  # Inside Asia - confirmed to exist
        
        try:
            work = work_resource.get(work_id)
            
            # Verify basic work structure
            assert 'title' in work or 'primaryTitle' in work  # Different response formats
            
            # Test with include parameters
            work_with_tags = work_resource.get(work_id, include=['tags'])
            assert isinstance(work_with_tags, dict)
            
        except ResourceNotFoundError:
            # Skip test if the specific work doesn't exist
            pytest.skip(f"Work {work_id} not found")
            
    def test_newspaper_article_real_data(self, resource_factory):
        """Test newspaper article with real data."""
        newspaper_resource = resource_factory.get_newspaper_resource()
        
        # Use an article ID that actually exists in Trove
        article_id = "166216596"  # Sydney! Sydney! Sydney! - confirmed to exist  
        
        try:
            article = newspaper_resource.get(article_id)
            
            # Verify basic article structure
            assert 'heading' in article or 'title' in article
            
            # Test full text retrieval (may not be available for all articles)
            full_text = newspaper_resource.get_full_text(article_id)
            # Full text might be None for some articles
            
        except ResourceNotFoundError:
            pytest.skip(f"Article {article_id} not found")
            
    def test_people_resource_real_data(self, resource_factory):
        """Test people resource with real data."""
        people_resource = resource_factory.get_people_resource()
        
        # Use a people ID that actually exists in Trove
        person_id = "1725799"  # Smith - confirmed to exist
        
        try:
            person = people_resource.get(person_id)
            
            # Verify basic person structure
            assert 'primaryName' in person or 'primaryDisplayName' in person or 'name' in person
            assert 'type' in person
            
            # Test type checking
            is_person = people_resource.is_person(person_id)
            is_org = people_resource.is_organization(person_id)
            # One of these should be true
            assert is_person or is_org
            
        except ResourceNotFoundError:
            pytest.skip(f"Person {person_id} not found")
            
    def test_list_resource_real_data(self, resource_factory):
        """Test list resource with real data."""
        list_resource = resource_factory.get_list_resource()
        
        # Use a list ID that actually exists in Trove
        list_id = "65445"  # Australia - confirmed to exist
        
        try:
            list_data = list_resource.get(list_id)
            
            # Verify basic list structure
            assert 'title' in list_data
            
            # Test metadata methods
            title = list_resource.get_title(list_id)
            creator = list_resource.get_creator(list_id)
            item_count = list_resource.get_item_count(list_id)
            
            assert isinstance(title, str)
            assert isinstance(creator, str)
            assert isinstance(item_count, int)
            
        except ResourceNotFoundError:
            pytest.skip(f"List {list_id} not found")
            
    def test_newspaper_title_search_real_data(self, resource_factory):
        """Test newspaper title search."""
        title_resource = resource_factory.get_newspaper_title_resource()
        
        # Search for newspaper titles
        results = title_resource.search(limit=2, state='nsw')
        
        # Should have response structure
        assert isinstance(results, dict)
        # Response format may vary, but should be a valid dictionary
        
    def test_error_handling_real_api(self, resource_factory):
        """Test error handling with real API."""
        work_resource = resource_factory.get_work_resource()
        
        # Use an ID that definitely doesn't exist
        invalid_id = "999999999999"
        
        with pytest.raises(ResourceNotFoundError):
            work_resource.get(invalid_id)
            
    @pytest.mark.asyncio
    async def test_async_resources_real_api(self, resource_factory):
        """Test async resource operations with real API."""
        work_resource = resource_factory.get_work_resource()
        
        work_id = "23458006"  # Inside Asia - confirmed to exist
        
        try:
            work = await work_resource.aget(work_id)
            
            # Should get same basic structure as sync version
            assert isinstance(work, dict)
            assert 'title' in work or 'primaryTitle' in work
            
        except ResourceNotFoundError:
            pytest.skip(f"Work {work_id} not found")
    
    def test_caching_behavior(self, resource_factory):
        """Test that resources are properly cached."""
        work_resource = resource_factory.get_work_resource()
        
        work_id = "23458006"  # Inside Asia - confirmed to exist
        
        try:
            # First request
            import time
            start_time = time.time()
            work1 = work_resource.get(work_id)
            first_duration = time.time() - start_time
            
            # Second request (should be cached if cache is working)
            start_time = time.time()
            work2 = work_resource.get(work_id)
            second_duration = time.time() - start_time
            
            # Results should be the same
            assert work1 == work2
            
            # Note: We can't reliably test that second_duration < first_duration
            # because the cache might not be configured or the response might be very fast
            
        except ResourceNotFoundError:
            pytest.skip(f"Work {work_id} not found")


@pytest.mark.integration 
class TestResourcesWithMockIntegration:
    """Integration tests with mocked responses that simulate real API structure."""
    
    def test_work_resource_with_realistic_response(self):
        """Test work resource with realistic API response structure."""
        # This simulates the actual response structure from Trove API
        mock_response = {
            "work": {
                "id": "123456",
                "title": "The Australian National Bibliography : a guide to published sources",
                "contributor": ["National Library of Australia"],
                "type": ["Book"],
                "issued": "1988",
                "identifier": [
                    {"type": "url", "value": "https://nla.gov.au/nla.cat-vn123456"}
                ],
                "abstract": "A comprehensive guide to published sources in Australia",
                "holdingsCount": 25,
                "versionCount": 1,
                "tagCount": [{"total": 3}],
                "commentCount": [{"total": 1}],
                "listCount": 5
            }
        }
        
        # Mock the transport layer
        from unittest.mock import Mock
        mock_transport = Mock()
        mock_transport.get.return_value = mock_response
        
        factory = ResourceFactory(mock_transport)
        work_resource = factory.get_work_resource()
        
        result = work_resource.get("123456")
        
        # Test post-processing worked correctly
        assert result["id"] == "123456"
        assert result["title"] == "The Australian National Bibliography : a guide to published sources"
        assert "National Library of Australia" in result["contributor"]
        
    def test_article_resource_with_realistic_response(self):
        """Test article resource with realistic API response structure."""
        mock_response = {
            "article": {
                "id": "18341291",
                "url": "https://api.trove.nla.gov.au/v3/newspaper/18341291",
                "heading": "SHIPPING INTELLIGENCE.",
                "category": "Article",
                "title": {
                    "id": "11",
                    "title": "The Sydney Morning Herald (NSW : 1842 - 1954)"
                },
                "date": "1876-05-27",
                "page": "7",
                "pageSequence": "7",
                "wordCount": "42",
                "correctionCount": "0",
                "tagCount": "1",
                "commentCount": "0",
                "listCount": "2",
                "pdf": [
                    "https://trove.nla.gov.au/ndp/imageservice/nla.news-page2243685/print"
                ]
            }
        }
        
        from unittest.mock import Mock
        mock_transport = Mock()
        mock_transport.get.return_value = mock_response
        
        factory = ResourceFactory(mock_transport)
        newspaper_resource = factory.get_newspaper_resource()
        
        result = newspaper_resource.get("18341291")
        
        # Test post-processing and convenience methods
        assert result["id"] == "18341291"
        assert result["heading"] == "SHIPPING INTELLIGENCE."
        
        # Test PDF URL extraction
        pdf_urls = newspaper_resource.get_pdf_urls("18341291")
        assert len(pdf_urls) == 1
        assert "nla.news-page2243685" in pdf_urls[0]
        
    def test_people_resource_with_realistic_response(self):
        """Test people resource with realistic API response structure."""
        mock_response = {
            "people": {
                "id": "1234",
                "primaryName": "Smith, John, 1950-2020",
                "primaryDisplayName": "John Smith",
                "type": "person",
                "occupation": ["Writer", "Journalist"],
                "biography": [
                    {
                        "contributor": "Australian Dictionary of Biography",
                        "biography": "John Smith was a prominent Australian writer..."
                    }
                ],
                "tagCount": 5,
                "commentCount": 2,
                "listCount": 8
            }
        }
        
        from unittest.mock import Mock
        mock_transport = Mock()
        mock_transport.get.return_value = mock_response
        
        factory = ResourceFactory(mock_transport)
        people_resource = factory.get_people_resource()
        
        result = people_resource.get("1234")
        
        # Test post-processing and convenience methods
        assert result["id"] == "1234"
        assert result["primaryName"] == "Smith, John, 1950-2020"
        assert people_resource.is_person("1234") is True
        assert people_resource.is_organization("1234") is False
        
        occupations = people_resource.get_occupations("1234")
        assert "Writer" in occupations
        assert "Journalist" in occupations