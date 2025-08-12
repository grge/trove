"""
Trove MCP Server - Exposes Trove SDK functionality via MCP protocol.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Union
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent

from trove import TroveClient
from trove.exceptions import TroveError, ResourceNotFoundError, ValidationError

from .tools.search_page import SearchPageTool
from .tools.get_record import (
    GetWorkTool, GetArticleTool, GetPeopleTool, GetListTool
)
from .tools.resolve_pid import ResolvePIDTool
from .tools.citation import CitationTool
from .utils.errors import map_trove_error_to_mcp
from .utils.validation import validate_environment

logger = logging.getLogger(__name__)


class TroveMCPServer:
    """MCP Server for Trove API access."""
    
    def __init__(self, config_overrides: Optional[Dict[str, Any]] = None):
        """Initialize MCP server.
        
        Args:
            config_overrides: Optional config overrides for testing
        """
        # Validate environment
        validate_environment()
        
        # Initialize Trove client with conservative settings for MCP usage
        self.client = TroveClient.from_env()
        
        # Override config for MCP usage if provided
        if config_overrides:
            for key, value in config_overrides.items():
                if hasattr(self.client.config, key):
                    setattr(self.client.config, key, value)
        
        # Initialize MCP server
        self.server = Server("trove", version="1.0.0")
        
        # Initialize tools
        self.tools = {
            'search_page': SearchPageTool(self.client),
            'get_work': GetWorkTool(self.client),
            'get_article': GetArticleTool(self.client), 
            'get_people': GetPeopleTool(self.client),
            'get_list': GetListTool(self.client),
            'resolve_pid': ResolvePIDTool(self.client),
            'citation_bibtex': CitationTool(self.client, format_type='bibtex'),
            'citation_csl_json': CitationTool(self.client, format_type='csl_json')
        }
        
        # Register MCP handlers
        self._register_handlers()
        
        logger.info("Trove MCP Server initialized with %d tools", len(self.tools))
    
    def _register_handlers(self):
        """Register MCP protocol handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            tools = []
            
            for tool_name, tool_instance in self.tools.items():
                tools.append(Tool(
                    name=tool_name,
                    description=tool_instance.description,
                    inputSchema=tool_instance.input_schema
                ))
            
            return tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[Union[TextContent, ImageContent]]:
            """Execute a tool call."""
            if name not in self.tools:
                raise Exception(f"Unknown tool: {name}")
            
            try:
                tool_instance = self.tools[name]
                result = await tool_instance.execute(arguments)
                
                # Convert result to MCP content format
                if isinstance(result, str):
                    return [TextContent(type="text", text=result)]
                elif isinstance(result, dict):
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                else:
                    return [TextContent(type="text", text=str(result))]
                
            except TroveError as e:
                # Map Trove errors to MCP errors
                mcp_error = map_trove_error_to_mcp(e)
                raise mcp_error
            except Exception as e:
                logger.error(f"Unexpected error in tool {name}: {e}", exc_info=True)
                raise Exception(f"Internal server error: {e}")
    
    async def run(self, transport_type: str = "stdio"):
        """Run the MCP server.
        
        Args:
            transport_type: Transport protocol ('stdio', 'sse', etc.)
        """
        if transport_type == "stdio":
            from mcp.server.stdio import stdio_server
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream, write_stream,
                    self.server.create_initialization_options()
                )
        else:
            raise ValueError(f"Unsupported transport type: {transport_type}")
    
    async def shutdown(self):
        """Shutdown the server and cleanup resources."""
        logger.info("Shutting down Trove MCP Server")
        await self.client.aclose()


async def main():
    """Main entry point for MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Trove MCP Server")
    parser.add_argument(
        "--transport", 
        default="stdio",
        choices=["stdio"],
        help="Transport protocol"
    )
    parser.add_argument(
        "--debug",
        action="store_true", 
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create and run server
    server = TroveMCPServer()
    
    try:
        await server.run(args.transport)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await server.shutdown()


if __name__ == "__main__":
    asyncio.run(main())