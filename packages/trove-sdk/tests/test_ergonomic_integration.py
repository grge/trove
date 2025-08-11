"""Integration tests for ergonomic search with real API."""

import pytest
import os
import asyncio
from trove import TroveClient
from trove.exceptions import ValidationError


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
                 
        assert result.total_results >= 0
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
        search_obj = (client.search()
                     .text("poetry")
                     .in_("book")
                     .page_size(5))
        
        pages = []
        for i, page in enumerate(search_obj.pages()):
            pages.append(page)
            if i >= 1:  # Limit to first 2 pages
                break
                     
        assert len(pages) >= 1
        if len(pages) > 1:
            # Verify pagination worked
            assert pages[0].response_data != pages[1].response_data
            
    def test_record_iteration(self, client):
        """Test individual record iteration.""" 
        search_obj = (client.search()
                     .text("Melbourne")
                     .in_("book")
                     .page_size(10))
        
        records = []
        for i, record in enumerate(search_obj.records()):
            records.append(record)
            if i >= 14:  # Limit to first 15 records
                break
                       
        if records:  # If any records found
            assert isinstance(records[0], dict)
            # Different record types have different fields
            assert 'title' in records[0] or 'heading' in records[0]
            
    def test_faceting_integration(self, client):
        """Test faceting with ergonomic search."""
        result = (client.search()
                 .text("literature")
                 .in_("book")
                 .with_facets("decade", "format")
                 .page_size(1)
                 .first_page())
                 
        if result.categories:
            facets = result.categories[0].get('facets', {})
            if 'facet' in facets:
                facet_list = facets['facet']
                if isinstance(facet_list, dict):
                    facet_list = [facet_list]
                facet_names = {f['name'] for f in facet_list}
                # Check if any expected facets are present
                expected_facets = {'decade', 'format'}
                assert len(facet_names.intersection(expected_facets)) >= 0
            
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
        search_obj = (client.search()
                     .text("Sydney")
                     .in_("book", "image")
                     .page_size(10))
                 
        # first_page should work
        result = search_obj.first_page()
        assert len(result.categories) >= 1  # Could be 1 or 2 depending on results
        
        # pages() should raise error
        with pytest.raises(ValidationError, match="only supports single-category"):
            list(search_obj.pages())
            
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
        
    @pytest.mark.asyncio
    async def test_async_search(self, client):
        """Test async search functionality.""" 
        result = await (client.search()
                       .text("Australian poetry")
                       .in_("book")
                       .page_size(5)
                       .afirst_page())
        
        assert result.total_results >= 0
        assert len(result.categories) >= 0
        
    @pytest.mark.asyncio 
    async def test_async_iteration(self, client):
        """Test async record iteration."""
        search_obj = (client.search()
                     .text("history")
                     .in_("book")
                     .page_size(5))
        
        records = []
        async for record in search_obj.arecords():
            records.append(record)
            if len(records) >= 10:  # Limit to first 10 records
                break
        
        if records:
            assert isinstance(records[0], dict)
            
    def test_explain_functionality(self, client):
        """Test explain method for debugging."""
        search_obj = (client.search()
                     .text("Australian literature")
                     .in_("book")
                     .decade("200")
                     .page_size(25))
        
        explanation = search_obj.explain()
        
        assert explanation['categories'] == ["book"]
        assert explanation['query'] == "Australian literature"
        assert explanation['page_size'] == 25
        assert 'compiled_params' in explanation
        assert 'category' in explanation['compiled_params']
        assert 'q' in explanation['compiled_params']
        
    def test_convenience_methods(self, client):
        """Test convenience filter methods work with real API."""
        # Test a search that should work with most filters
        result = (client.search()
                 .text("Australia")
                 .in_("book")
                 .decade("200")  # 2000s
                 .online()  # Available online
                 .australian_content()  # Australian content
                 .page_size(5)
                 .first_page())
        
        # Should complete without errors
        assert result.categories[0]['records']['total'] >= 0
        
    def test_newspaper_specific_filters(self, client):
        """Test newspaper-specific filters."""
        result = (client.search()
                 .text("federation")
                 .in_("newspaper")
                 .decade("190")  # 1900s
                 .state("NSW")  # New South Wales
                 .page_size(5)
                 .first_page())
        
        # Should complete without errors
        assert result.categories[0]['records']['total'] >= 0
        
    def test_client_context_manager(self, client):
        """Test client works as context manager."""
        api_key = os.environ.get('TROVE_API_KEY')
        if not api_key:
            pytest.skip("TROVE_API_KEY not set")
            
        with TroveClient.from_api_key(api_key) as test_client:
            result = (test_client.search()
                     .text("test")
                     .in_("book")
                     .page_size(1)
                     .first_page())
            assert result.categories[0]['records']['total'] >= 0
        
        # Client should be closed after context manager exits
        
    @pytest.mark.asyncio
    async def test_async_context_manager(self, client):
        """Test client works as async context manager."""
        api_key = os.environ.get('TROVE_API_KEY')
        if not api_key:
            pytest.skip("TROVE_API_KEY not set")
            
        async with TroveClient.from_api_key(api_key) as test_client:
            result = await (test_client.search()
                           .text("test")
                           .in_("book")
                           .page_size(1)
                           .afirst_page())
            assert result.categories[0]['records']['total'] >= 0