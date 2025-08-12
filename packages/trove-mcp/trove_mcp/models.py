"""
Pydantic models for structured output from MCP tools.

These models provide type-safe structured data for MCP clients,
while maintaining backward compatibility with unstructured responses.
"""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Result from search_page tool with structured output."""
    
    query: Optional[str] = Field(None, description="Original search query text")
    total_results: int = Field(description="Total number of results across all categories")
    categories: List[Dict[str, Any]] = Field(description="Search results by category")
    cursors: Dict[str, str] = Field(default_factory=dict, description="Pagination cursors for each category")
    facets: Optional[Dict[str, Any]] = Field(None, description="Facet information if requested")
    
    class Config:
        arbitrary_types_allowed = True


class RecordResult(BaseModel):
    """Result from individual record retrieval tools."""
    
    record_type: str = Field(description="Type of record (work, article, people, list)")
    record_id: str = Field(description="Record identifier") 
    data: Dict[str, Any] = Field(description="Complete record data")
    metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata about the record")
    
    class Config:
        arbitrary_types_allowed = True


class CitationResult(BaseModel):
    """Result from citation generation tools."""
    
    format: Literal["bibtex", "csl_json"] = Field(description="Citation format type")
    citation: str = Field(description="Formatted citation text")
    record_id: str = Field(description="Original record identifier")
    record_type: str = Field(description="Type of record cited")
    
    class Config:
        arbitrary_types_allowed = True


class PIDResolution(BaseModel):
    """Result from PID resolution tool."""
    
    original_identifier: str = Field(description="Original PID, URL, or identifier provided")
    resolved_type: str = Field(description="Type of resolved record")
    record_id: str = Field(description="Resolved record identifier")
    title: Optional[str] = Field(None, description="Record title if available")
    url: Optional[str] = Field(None, description="Trove URL for the record")
    
    class Config:
        arbitrary_types_allowed = True


class CategoryInfo(BaseModel):
    """Information about available search categories."""
    
    code: str = Field(description="Category code")
    name: str = Field(description="Human-readable category name")
    description: str = Field(description="Category description")
    supported_filters: List[str] = Field(description="Available filters for this category")
    
    class Config:
        arbitrary_types_allowed = True


class ServerInfo(BaseModel):
    """Information about the MCP server and Trove API capabilities."""
    
    server_name: str = Field(description="MCP server name")
    server_version: str = Field(description="MCP server version")
    trove_api_version: str = Field(description="Supported Trove API version")
    available_categories: List[CategoryInfo] = Field(description="Available search categories")
    rate_limit: float = Field(description="Current rate limit (requests per second)")
    
    class Config:
        arbitrary_types_allowed = True