"""Test MCP tool contracts and schemas."""

import pytest
import json
from mcp.types import Tool

from trove_mcp.server import TroveMCPServer
from trove_mcp.tools.search_page import SearchPageTool, SearchPageInput


class TestMCPContracts:
    """Test MCP protocol contracts."""
    
    @pytest.fixture
    def server(self, test_server_config):
        # Use test configuration
        return TroveMCPServer(test_server_config)
    
    def test_tool_schema_validation(self, server):
        """Test that tool schemas are valid JSON Schema."""
        for tool_name, tool_instance in server.tools.items():
            schema = tool_instance.input_schema
            
            # Should be valid JSON Schema
            assert isinstance(schema, dict)
            assert 'type' in schema
            assert schema['type'] == 'object'
            assert 'properties' in schema
    
    def test_search_page_input_validation(self):
        """Test search page input validation."""
        # Valid input
        valid_input = {
            'categories': ['book'],
            'query': 'test',
            'page_size': 10
        }
        
        search_input = SearchPageInput(**valid_input)
        assert search_input.categories == ['book']
        assert search_input.page_size == 10
        
        # Invalid category
        with pytest.raises(ValueError, match="Invalid categories"):
            SearchPageInput(categories=['invalid_category'])
        
        # Invalid page size
        with pytest.raises(ValueError):
            SearchPageInput(categories=['book'], page_size=101)
    
    @pytest.mark.asyncio
    async def test_tool_execution_interface(self, server):
        """Test that all tools implement the execution interface correctly."""
        for tool_name, tool_instance in server.tools.items():
            # Should have required attributes
            assert hasattr(tool_instance, 'name')
            assert hasattr(tool_instance, 'description') 
            assert hasattr(tool_instance, 'input_schema')
            assert hasattr(tool_instance, 'execute')
            
            # Should be callable
            assert callable(tool_instance.execute)