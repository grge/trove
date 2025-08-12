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
            result = await self.client.raw_search.apage(params)
        else:
            # Execute search
            result = await search_builder.afirst_page()
        
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