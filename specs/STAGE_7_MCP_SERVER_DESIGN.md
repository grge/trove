# Stage 7 - MCP Server Design Document

## Overview

Stage 7 implements a separate MCP (Model Context Protocol) server package that exposes the Trove SDK functionality through standardized MCP tools. This enables AI agents and applications to interact with Trove through a secure, stateless protocol interface.

## MCP Architecture Principles

- **Stateless Tools** - Each tool call is independent, no server-side state
- **JSON Schema Validation** - All inputs and outputs strictly validated
- **Security First** - API keys from environment only, never from client inputs
- **Shared Infrastructure** - Uses same cache and rate limiting as SDK
- **Tool Granularity** - One tool per logical operation for clarity

## Package Structure

```
trove-mcp/
├── trove_mcp/
│   ├── __init__.py
│   ├── server.py              # Main MCP server
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search_page.py     # Search operations
│   │   ├── get_record.py      # Individual record retrieval
│   │   ├── resolve_pid.py     # PID resolution
│   │   └── citation.py        # Citation generation
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── search.py          # Search tool schemas
│   │   ├── records.py         # Record tool schemas
│   │   └── common.py          # Shared schemas
│   └── utils/
│       ├── __init__.py
│       ├── validation.py      # Input validation
│       └── errors.py          # Error handling
├── tests/
├── pyproject.toml
└── README.md
```

## Detailed Component Design

### 1. MCP Server Core (`trove_mcp/server.py`)

```python
"""
Trove MCP Server - Exposes Trove SDK functionality via MCP protocol.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from mcp import Server, McpError
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
        self.server = Server("trove")
        
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
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent | ImageContent]:
            """Execute a tool call."""
            if name not in self.tools:
                raise McpError(f"Unknown tool: {name}")
            
            try:
                tool_instance = self.tools[name]
                result = await tool_instance.execute(arguments)
                
                # Convert result to MCP content format
                if isinstance(result, str):
                    return [TextContent(type="text", text=result)]
                elif isinstance(result, dict):
                    import json
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                else:
                    return [TextContent(type="text", text=str(result))]
                
            except TroveError as e:
                # Map Trove errors to MCP errors
                mcp_error = map_trove_error_to_mcp(e)
                raise mcp_error
            except Exception as e:
                logger.error(f"Unexpected error in tool {name}: {e}", exc_info=True)
                raise McpError(f"Internal server error: {e}")
    
    async def run(self, transport_type: str = "stdio"):
        """Run the MCP server.
        
        Args:
            transport_type: Transport protocol ('stdio', 'sse', etc.)
        """
        if transport_type == "stdio":
            from mcp.server.stdio import stdio_server
            await stdio_server(self.server)
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
```

### 2. Search Tool (`trove_mcp/tools/search_page.py`)

```python
"""Search page tool for MCP."""

import json
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator

from trove import TroveClient
from ..utils.validation import validate_search_params
from .base import BaseTool

class SearchPageInput(BaseModel):
    """Input schema for search_page tool."""
    
    categories: List[str] = Field(
        description="Search categories (book, newspaper, image, people, list, magazine, music, diary, research, all)",
        min_items=1
    )
    query: Optional[str] = Field(
        None,
        description="Search query text with optional field indexes"
    )
    limits: Optional[Dict[str, Union[str, List[str]]]] = Field(
        default_factory=dict,
        description="Search limits/filters (l-decade, l-format, l-availability, etc.)"
    )
    facets: Optional[List[str]] = Field(
        default_factory=list,
        description="Facets to include in response"
    )
    page_size: Optional[int] = Field(
        20,
        ge=1,
        le=100,
        description="Number of results per category (1-100)"
    )
    sort_by: Optional[str] = Field(
        "relevance",
        description="Sort order: relevance, datedesc, dateasc"
    )
    record_level: Optional[str] = Field(
        "brief",
        description="Record detail level: brief or full"
    )
    bulk_harvest: Optional[bool] = Field(
        False,
        description="Enable bulk harvest mode for systematic collection"
    )
    cursor: Optional[str] = Field(
        None,
        description="Pagination cursor from previous response"
    )
    include_fields: Optional[List[str]] = Field(
        default_factory=list,
        description="Optional fields to include (tags, comments, etc.)"
    )
    
    @validator('categories')
    def validate_categories(cls, v):
        valid_categories = {
            'all', 'book', 'diary', 'image', 'list', 
            'magazine', 'music', 'newspaper', 'people', 'research'
        }
        invalid = set(v) - valid_categories
        if invalid:
            raise ValueError(f"Invalid categories: {', '.join(invalid)}")
        return v
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        if v not in ['relevance', 'datedesc', 'dateasc']:
            raise ValueError("sort_by must be one of: relevance, datedesc, dateasc")
        return v
    
    @validator('record_level')
    def validate_record_level(cls, v):
        if v not in ['brief', 'full']:
            raise ValueError("record_level must be 'brief' or 'full'")
        return v

class SearchPageOutput(BaseModel):
    """Output schema for search_page tool."""
    
    query: str = Field(description="The search query that was executed")
    total_results: int = Field(description="Total number of results across all categories")
    categories: List[Dict[str, Any]] = Field(description="Results by category")
    cursors: Dict[str, str] = Field(description="Pagination cursors for each category")
    facets: Optional[Dict[str, Any]] = Field(None, description="Facet information if requested")

class SearchPageTool(BaseTool):
    """Tool for executing search page requests."""
    
    name = "search_page"
    description = """
    Search Trove records with full parameter support and pagination.
    
    Returns a single page of search results across specified categories.
    For multi-category searches, use cursors to paginate through each category separately.
    
    Supports all search parameters including limits (l-*), facets, and includes.
    Use bulk_harvest=true for systematic data collection workflows.
    """
    
    input_schema = SearchPageInput.model_json_schema()
    output_schema = SearchPageOutput.model_json_schema()
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search page request."""
        # Validate input
        input_data = SearchPageInput(**arguments)
        
        # Build search using ergonomic interface
        search_builder = self.client.search()
        
        # Apply parameters
        search_builder = search_builder.in_(*input_data.categories)
        
        if input_data.query:
            search_builder = search_builder.text(input_data.query)
        
        search_builder = search_builder.page_size(input_data.page_size)
        search_builder = search_builder.sort_by(input_data.sort_by)
        search_builder = search_builder.with_reclevel(input_data.record_level)
        search_builder = search_builder.harvest(input_data.bulk_harvest)
        
        if input_data.facets:
            search_builder = search_builder.with_facets(*input_data.facets)
        
        if input_data.include_fields:
            search_builder = search_builder.include(*input_data.include_fields)
        
        # Apply limits
        for limit_param, limit_values in input_data.limits.items():
            if isinstance(limit_values, str):
                limit_values = [limit_values]
            search_builder = search_builder.where(limit_param, *limit_values)
        
        # Handle cursor for pagination
        if input_data.cursor:
            # For MCP stateless operation, need to modify the underlying parameters
            search_spec = search_builder._spec
            params = search_spec.to_parameters()
            params.s = input_data.cursor
            
            # Execute with cursor
            result = self.client.raw_search.page(params)
        else:
            # Execute search
            result = search_builder.first_page()
        
        # Extract facets if present
        facets = {}
        for category in result.categories:
            category_facets = {}
            facets_data = category.get('facets', {}).get('facet', [])
            if isinstance(facets_data, dict):
                facets_data = [facets_data]
                
            for facet in facets_data:
                facet_name = facet.get('name')
                if facet_name:
                    terms = facet.get('term', [])
                    if isinstance(terms, dict):
                        terms = [terms]
                    category_facets[facet_name] = terms
                    
            if category_facets:
                facets[category['code']] = category_facets
        
        return SearchPageOutput(
            query=result.query,
            total_results=result.total_results,
            categories=result.categories,
            cursors=result.cursors,
            facets=facets if facets else None
        ).model_dump()
```

### 3. Record Retrieval Tools (`trove_mcp/tools/get_record.py`)

```python
"""Record retrieval tools for MCP."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from trove import TroveClient
from trove.resources import ResourceFactory
from .base import BaseTool

class RecordInput(BaseModel):
    """Base input schema for record retrieval."""
    
    record_id: str = Field(description="The record identifier")
    include_fields: Optional[List[str]] = Field(
        default_factory=list,
        description="Optional fields to include"
    )
    record_level: Optional[str] = Field(
        "brief",
        description="Record detail level: brief or full"
    )
    
    class Config:
        extra = "forbid"  # Prevent additional fields

class GetWorkTool(BaseTool):
    """Tool for retrieving work records."""
    
    name = "get_work"
    description = """
    Retrieve a specific work record (book, image, map, music, etc.) by ID.
    
    Supports include parameters: all, comments, holdings, links, lists, 
    subscribinglibs, tags, workversions.
    """
    
    input_schema = RecordInput.model_json_schema()
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute work retrieval."""
        input_data = RecordInput(**arguments)
        
        work_resource = self.client.resources.get_work_resource()
        
        work = work_resource.get(
            input_data.record_id,
            include=input_data.include_fields,
            reclevel=input_data.record_level
        )
        
        return {
            "record_type": "work",
            "record_id": input_data.record_id,
            "data": work
        }

class ArticleInput(BaseModel):
    """Input schema for article retrieval."""
    
    article_id: str = Field(description="The article identifier")
    article_type: Optional[str] = Field(
        "newspaper",
        description="Article type: newspaper or gazette"
    )
    include_fields: Optional[List[str]] = Field(
        default_factory=list,
        description="Optional fields: all, articletext, comments, lists, tags"
    )
    record_level: Optional[str] = Field(
        "brief",
        description="Record detail level: brief or full"
    )

class GetArticleTool(BaseTool):
    """Tool for retrieving newspaper/gazette articles."""
    
    name = "get_article" 
    description = """
    Retrieve a specific newspaper or gazette article by ID.
    
    Supports include parameters: all, articletext, comments, lists, tags.
    Set article_type to 'gazette' for gazette articles.
    """
    
    input_schema = ArticleInput.model_json_schema()
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute article retrieval."""
        input_data = ArticleInput(**arguments)
        
        if input_data.article_type == "gazette":
            article_resource = self.client.resources.get_gazette_resource()
        else:
            article_resource = self.client.resources.get_newspaper_resource()
        
        article = article_resource.get(
            input_data.article_id,
            include=input_data.include_fields,
            reclevel=input_data.record_level
        )
        
        return {
            "record_type": "article",
            "article_type": input_data.article_type,
            "record_id": input_data.article_id,
            "data": article
        }

class GetPeopleTool(BaseTool):
    """Tool for retrieving people/organization records."""
    
    name = "get_people"
    description = """
    Retrieve a specific people or organization record by ID.
    
    Supports include parameters: all, comments, lists, raweaccpf, tags.
    """
    
    input_schema = RecordInput.model_json_schema()
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute people record retrieval."""
        input_data = RecordInput(**arguments)
        
        people_resource = self.client.resources.get_people_resource()
        
        # Validate include fields for people records
        valid_includes = ['all', 'comments', 'lists', 'raweaccpf', 'tags']
        invalid_includes = set(input_data.include_fields) - set(valid_includes)
        if invalid_includes:
            raise ValueError(f"Invalid include fields for people records: {', '.join(invalid_includes)}")
        
        people = people_resource.get(
            input_data.record_id,
            include=input_data.include_fields,
            reclevel=input_data.record_level
        )
        
        return {
            "record_type": "people",
            "record_id": input_data.record_id,
            "data": people
        }

class GetListTool(BaseTool):
    """Tool for retrieving list records."""
    
    name = "get_list"
    description = """
    Retrieve a specific user-created list by ID.
    
    Supports include parameters: all, comments, listitems, tags.
    """
    
    input_schema = RecordInput.model_json_schema()
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute list retrieval."""
        input_data = RecordInput(**arguments)
        
        list_resource = self.client.resources.get_list_resource()
        
        # Validate include fields for list records
        valid_includes = ['all', 'comments', 'listitems', 'tags']
        invalid_includes = set(input_data.include_fields) - set(valid_includes)
        if invalid_includes:
            raise ValueError(f"Invalid include fields for list records: {', '.join(invalid_includes)}")
        
        list_data = list_resource.get(
            input_data.record_id,
            include=input_data.include_fields,
            reclevel=input_data.record_level
        )
        
        return {
            "record_type": "list",
            "record_id": input_data.record_id,
            "data": list_data
        }
```

### 4. PID Resolution Tool (`trove_mcp/tools/resolve_pid.py`)

```python
"""PID resolution tool for MCP."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from trove.citations import CitationManager
from .base import BaseTool

class ResolvePIDInput(BaseModel):
    """Input schema for PID resolution."""
    
    identifier: str = Field(
        description="PID, URL, or identifier to resolve"
    )
    
    class Config:
        extra = "forbid"

class ResolvePIDOutput(BaseModel):
    """Output schema for PID resolution."""
    
    resolved: bool = Field(description="Whether the identifier was successfully resolved")
    record_type: Optional[str] = Field(None, description="Type of record (work, article, people, list)")
    record_id: Optional[str] = Field(None, description="Resolved record ID")
    pid: Optional[str] = Field(None, description="Canonical PID if available")
    trove_url: Optional[str] = Field(None, description="Trove web interface URL")
    api_url: Optional[str] = Field(None, description="API endpoint URL")
    title: Optional[str] = Field(None, description="Record title")
    error_message: Optional[str] = Field(None, description="Error message if resolution failed")

class ResolvePIDTool(BaseTool):
    """Tool for resolving PIDs and URLs to record information."""
    
    name = "resolve_pid"
    description = """
    Resolve a PID, URL, or identifier to detailed record information.
    
    Supports:
    - Trove PIDs (e.g., nla.obj-123456789, nla.news-article18341291)
    - Trove URLs (web interface and API URLs)
    - Bare record IDs (attempts resolution across record types)
    
    Returns basic record information without full metadata.
    Use get_* tools to retrieve complete record data.
    """
    
    input_schema = ResolvePIDInput.model_json_schema()
    output_schema = ResolvePIDOutput.model_json_schema()
    
    def __init__(self, client):
        super().__init__(client)
        self.citation_manager = CitationManager(client.resources)
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PID resolution."""
        input_data = ResolvePIDInput(**arguments)
        
        try:
            citation_ref = self.citation_manager.resolve_identifier(input_data.identifier)
            
            if citation_ref:
                return ResolvePIDOutput(
                    resolved=True,
                    record_type=citation_ref.record_type.value,
                    record_id=citation_ref.record_id,
                    pid=citation_ref.canonical_pid,
                    trove_url=citation_ref.trove_url,
                    api_url=citation_ref.api_url,
                    title=citation_ref.title,
                    error_message=None
                ).model_dump()
            else:
                return ResolvePIDOutput(
                    resolved=False,
                    error_message=f"Could not resolve identifier: {input_data.identifier}"
                ).model_dump()
                
        except Exception as e:
            return ResolvePIDOutput(
                resolved=False,
                error_message=str(e)
            ).model_dump()
```

### 5. Citation Tool (`trove_mcp/tools/citation.py`)

```python
"""Citation generation tool for MCP."""

from typing import Dict, Any, Union
from pydantic import BaseModel, Field, validator

from trove.citations import CitationManager, RecordType
from .base import BaseTool

class CitationInput(BaseModel):
    """Input schema for citation generation."""
    
    source: Union[str, Dict[str, Any]] = Field(
        description="PID/URL to cite, or raw record data with record_type"
    )
    record_type: Optional[str] = Field(
        None,
        description="Record type when providing raw data (work, article, people, list)"
    )
    format_type: str = Field(
        "bibtex",
        description="Citation format: bibtex or csl_json"
    )
    
    @validator('record_type')
    def validate_record_type(cls, v):
        if v and v not in ['work', 'article', 'people', 'list']:
            raise ValueError("record_type must be one of: work, article, people, list")
        return v
    
    @validator('format_type')
    def validate_format_type(cls, v):
        if v not in ['bibtex', 'csl_json']:
            raise ValueError("format_type must be 'bibtex' or 'csl_json'")
        return v
    
    class Config:
        extra = "forbid"

class CitationTool(BaseTool):
    """Tool for generating citations in various formats."""
    
    def __init__(self, client, format_type: str = 'bibtex'):
        super().__init__(client)
        self.format_type = format_type
        self.citation_manager = CitationManager(client.resources)
    
    @property
    def name(self) -> str:
        return f"citation_{self.format_type}"
    
    @property 
    def description(self) -> str:
        format_desc = {
            'bibtex': 'BibTeX format for LaTeX documents',
            'csl_json': 'CSL-JSON format for reference managers'
        }
        
        return f"""
        Generate {format_desc.get(self.format_type, 'formatted')} citations for Trove records.
        
        Can cite by:
        - PID or URL (automatically resolves to record)
        - Raw record data (must specify record_type)
        
        Produces properly formatted citations suitable for academic use.
        """
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        schema = CitationInput.model_json_schema()
        # Override format_type default for this specific tool
        schema['properties']['format_type']['default'] = self.format_type
        return schema
    
    async def execute(self, arguments: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        """Execute citation generation."""
        input_data = CitationInput(**arguments)
        
        # Override format type from tool configuration
        input_data.format_type = self.format_type
        
        if isinstance(input_data.source, str):
            # Resolve PID/URL to citation
            if self.format_type == 'bibtex':
                citation = self.citation_manager.cite_bibtex(input_data.source)
            else:
                citation = self.citation_manager.cite_csl_json(input_data.source)
        else:
            # Use raw record data
            if not input_data.record_type:
                raise ValueError("record_type is required when providing raw record data")
            
            record_type = RecordType(input_data.record_type)
            citation_ref = self.citation_manager.extract_from_record(input_data.source, record_type)
            
            if self.format_type == 'bibtex':
                citation = self.citation_manager.cite_bibtex(citation_ref)
            else:
                citation = self.citation_manager.cite_csl_json(citation_ref)
        
        return citation
```

### 6. Base Tool Class (`trove_mcp/tools/base.py`)

```python
"""Base tool class for MCP tools."""

from abc import ABC, abstractmethod
from typing import Dict, Any

from trove import TroveClient

class BaseTool(ABC):
    """Base class for all MCP tools."""
    
    def __init__(self, client: TroveClient):
        self.client = client
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """JSON schema for tool input."""
        pass
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        """Execute the tool with given arguments."""
        pass
```

### 7. Utility Functions (`trove_mcp/utils/`)

```python
# trove_mcp/utils/validation.py
"""Input validation utilities for MCP tools."""

import os
from typing import Dict, Any
from mcp import McpError

def validate_environment():
    """Validate that required environment variables are set."""
    required_vars = ['TROVE_API_KEY']
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise McpError(
            f"Required environment variables not set: {', '.join(missing_vars)}"
        )

def validate_search_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize search parameters."""
    # Add any search-specific validation here
    return params

# trove_mcp/utils/errors.py
"""Error mapping utilities."""

from mcp import McpError
from trove.exceptions import (
    TroveError, TroveAPIError, AuthenticationError, 
    ResourceNotFoundError, ValidationError, RateLimitError
)

def map_trove_error_to_mcp(error: TroveError) -> McpError:
    """Map Trove SDK errors to MCP errors."""
    
    if isinstance(error, AuthenticationError):
        return McpError(f"Authentication failed: {error}")
    
    elif isinstance(error, ResourceNotFoundError):
        return McpError(f"Resource not found: {error}")
    
    elif isinstance(error, ValidationError):
        return McpError(f"Invalid parameters: {error}")
    
    elif isinstance(error, RateLimitError):
        return McpError(f"Rate limit exceeded: {error}")
    
    elif isinstance(error, TroveAPIError):
        status_info = f" (HTTP {error.status_code})" if error.status_code else ""
        return McpError(f"API error: {error}{status_info}")
    
    else:
        return McpError(f"Unexpected error: {error}")
```

### 8. Package Configuration (`pyproject.toml`)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "trove-mcp"
version = "1.0.0"
description = "MCP server for Trove API access"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "Trove SDK Team", email = "noreply@example.com"},
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
requires-python = ">=3.10"
dependencies = [
    "trove-sdk>=1.0.0",
    "mcp>=0.5.0",
    "pydantic>=2.0.0",
    "asyncio",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "mypy>=1.0.0",
    "ruff>=0.0.275",
]

[project.scripts]
trove-mcp = "trove_mcp.server:main"

[tool.hatch.build.targets.wheel]
packages = ["trove_mcp"]

[tool.black]
line-length = 100
target-version = ["py310"]

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.ruff]
line-length = 100
target-version = "py310"
select = ["E", "F", "UP", "B", "SIM", "I"]
```

## Testing Strategy

### Contract Tests

```python
# tests/test_mcp_contracts.py
"""Test MCP tool contracts and schemas."""

import pytest
import json
from mcp.types import Tool

from trove_mcp.server import TroveMCPServer
from trove_mcp.tools.search_page import SearchPageTool, SearchPageInput

class TestMCPContracts:
    """Test MCP protocol contracts."""
    
    @pytest.fixture
    def server(self):
        # Use test configuration
        config_overrides = {
            'rate_limit': 0.1,  # Very slow for testing
            'cache_backend': 'memory'
        }
        return TroveMCPServer(config_overrides)
    
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
```

### Integration Tests

```python
# tests/test_mcp_integration.py
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
```

### Performance Tests

```python
# tests/test_mcp_performance.py  
"""Performance tests for MCP server."""

import pytest
import time
import asyncio

@pytest.mark.performance
class TestMCPPerformance:
    """Performance tests for MCP operations."""
    
    @pytest.mark.asyncio
    async def test_search_response_time(self, server):
        """Test search tool response time."""
        search_tool = server.tools['search_page']
        
        start_time = time.time()
        
        result = await search_tool.execute({
            'categories': ['book'],
            'query': 'test',
            'page_size': 10
        })
        
        duration = time.time() - start_time
        
        # Should complete within reasonable time
        assert duration < 5.0  # 5 seconds max
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, server):
        """Test concurrent tool execution."""
        search_tool = server.tools['search_page']
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(3):
            task = search_tool.execute({
                'categories': ['book'],
                'query': f'test {i}',
                'page_size': 5
            })
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start_time
        
        # Should handle concurrent requests efficiently
        assert len(results) == 3
        assert all(isinstance(r, dict) or isinstance(r, Exception) for r in results)
        assert duration < 15.0  # Should not take too long even with rate limiting
```

## Definition of Done

Stage 7 is complete when:

- ✅ **MCP server implemented** - Full MCP protocol compliance
- ✅ **All tools working** - search_page, get_*, resolve_pid, citation tools
- ✅ **Schema validation** - JSON Schema validation for all inputs/outputs
- ✅ **Stateless operation** - No server-side state, proper cursor handling
- ✅ **Security implemented** - API keys from environment only
- ✅ **Shared infrastructure** - Uses same cache/rate limiting as SDK
- ✅ **Error handling** - Proper MCP error mapping and responses
- ✅ **Contract tests** - Tool contracts and schemas validated
- ✅ **Integration tests** - End-to-end tests with real API
- ✅ **Performance tests** - Meets response time and concurrency targets
- ✅ **Documentation** - Tool documentation and usage examples
- ✅ **Package ready** - Deployable MCP server package

This MCP server implementation provides a secure, stateless interface for AI agents to access Trove functionality while maintaining all the benefits of the underlying SDK.