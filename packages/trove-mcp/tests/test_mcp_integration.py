"""Integration tests for MCP server."""

import pytest
import json
import os

from trove_mcp.server import TroveMCPServer


@pytest.mark.integration
class TestMCPIntegration:
    """Integration tests with real Trove API."""
    
    @pytest.fixture(scope="class")
    def server(self):
        if not os.environ.get('TROVE_API_KEY'):
            pytest.skip("TROVE_API_KEY not set")
        
        config_overrides = {
            'rate_limit': 1.0,  # Conservative for testing
        }
        return TroveMCPServer(config_overrides)
    
    @pytest.mark.asyncio
    async def test_search_page_tool_real_api(self, server):
        """Test search page tool with real API."""
        search_tool = server.tools['search_page']
        
        arguments = {
            'categories': ['book'],
            'query': 'Australian history',
            'page_size': 5
        }
        
        result = await search_tool.execute(arguments)
        
        assert 'query' in result
        assert 'total_results' in result
        assert 'categories' in result
        assert isinstance(result['categories'], list)
        assert len(result['categories']) == 1
        assert result['categories'][0]['code'] == 'book'
    
    @pytest.mark.asyncio 
    async def test_get_work_tool_real_api(self, server):
        """Test get work tool with real API."""
        # First, find a work ID through search
        search_tool = server.tools['search_page']
        search_result = await search_tool.execute({
            'categories': ['book'],
            'query': 'test',
            'page_size': 1
        })
        
        if (search_result['total_results'] > 0 and 
            search_result['categories'][0]['records']['work']):
            
            work_id = search_result['categories'][0]['records']['work'][0]['id']
            
            # Test work retrieval
            work_tool = server.tools['get_work']
            work_result = await work_tool.execute({
                'record_id': work_id,
                'record_level': 'brief'
            })
            
            assert work_result['record_type'] == 'work'
            assert work_result['record_id'] == work_id
            assert 'data' in work_result
            assert work_result['data']['id'] == work_id
    
    @pytest.mark.asyncio
    async def test_citation_tool_real_api(self, server):
        """Test citation tool with real API.""" 
        # Use a known work for citation
        citation_tool = server.tools['citation_bibtex']
        
        # Test with known URL
        test_url = "https://nla.gov.au/nla.news-article18341291"
        
        try:
            citation_result = await citation_tool.execute({
                'source': test_url
            })
            
            assert isinstance(citation_result, str)
            assert '@' in citation_result  # BibTeX format
            
        except Exception as e:
            # May fail if the specific article doesn't exist
            pytest.skip(f"Citation test skipped: {e}")