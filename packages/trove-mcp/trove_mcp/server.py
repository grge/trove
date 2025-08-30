"""
Modern Trove MCP Server using FastMCP.

This server exposes Trove SDK functionality via the Model Context Protocol,
using structured output and the latest MCP features.
"""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Literal, Union

from pydantic import Field
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from trove import TroveClient
from trove.exceptions import TroveError, ResourceNotFoundError, ValidationError

from .models import (
    SearchResult,
    RecordResult,
    CitationResult,
    PIDResolution,
    CategoryInfo,
    ServerInfo,
)

logger = logging.getLogger(__name__)


# Validate categories based on official Trove API documentation
VALID_CATEGORIES = {
    'all', 'book', 'diary', 'image', 'list', 
    'magazine', 'music', 'newspaper', 'people', 'research'
}


def validate_categories(categories: List[str]) -> None:
    """Validate categories against official Trove API categories."""
    invalid_categories = set(categories) - VALID_CATEGORIES
    if invalid_categories:
        valid_list = sorted(VALID_CATEGORIES)
        raise Exception(
            f"""Invalid categories: {list(invalid_categories)}
            
Valid categories for Trove search:
🗞️ newspaper - START HERE for historical research (richest information)
📚 book - Published works and academic sources  
🖼️ image - Photographs, maps, artwork, posters
👥 people - Biographical records and authority files
📰 magazine - Periodicals and newsletters
🎵 music - Audio and video materials
📔 diary - Diaries, letters, archives
📝 list - User-created lists
🔬 research - Research publications and reports

For most historical research, use: categories=['newspaper']
Use the 'trove://categories' resource for detailed descriptions."""
        )


def validate_newspaper_filters(categories: List[str], limits: Dict[str, Union[str, List[str]]]) -> None:
    """Validate newspaper-specific filter dependencies."""
    if 'newspaper' not in categories:
        return
        
    has_year = 'year' in limits and limits['year']
    has_decade = 'decade' in limits and limits['decade']
    has_month = 'month' in limits and limits['month']
    
    # Check for multiple decades (common mistake)
    if has_decade and isinstance(limits['decade'], list) and len(limits['decade']) > 1:
        raise Exception(
            f"⚠️ NEWSPAPER FILTER ERROR: Cannot search multiple decades simultaneously.\n"
            f"You provided: {limits['decade']}\n"
            f"Search ONE decade at a time: {{'decade': ['{limits['decade'][0]}']}}\n"
            f"Then search the next decade separately: {{'decade': ['{limits['decade'][1]}']}}\n"
            "This is a Trove API limitation for newspaper searches."
        )
    
    if has_year and not has_decade:
        raise Exception(
            "⚠️ NEWSPAPER FILTER ERROR: 'year' requires 'decade' to be specified.\n"
            f"Example: limits={{'decade': ['190'], 'year': {limits['year']}}}\n"
            "This is a Trove API requirement for newspaper searches."
        )
    
    if has_month and not has_year:
        raise Exception(
            "⚠️ NEWSPAPER FILTER ERROR: 'month' requires both 'decade' and 'year'.\n"
            f"Example: limits={{'decade': ['190'], 'year': ['1901'], 'month': {limits['month']}}}\n"
            "This is a Trove API requirement for newspaper searches."
        )


@dataclass
class TroveContext:
    """Application context with Trove client and configuration."""
    
    client: TroveClient
    server_version: str = "1.0.0"
    

@asynccontextmanager
async def trove_lifespan(server: FastMCP) -> AsyncIterator[TroveContext]:
    """Manage Trove client lifecycle with proper startup and shutdown."""
    logger.info("Initializing Trove MCP Server")
    
    # Validate environment
    if not os.getenv('TROVE_API_KEY'):
        raise ValueError("TROVE_API_KEY environment variable is required")
    
    # Initialize Trove client
    client = TroveClient.from_env()
    
    try:
        # Configure for MCP usage - conservative settings
        if hasattr(client.config, 'rate_limit'):
            # Use conservative rate limiting for MCP context
            original_rate_limit = client.config.rate_limit
            client.config.rate_limit = min(original_rate_limit, 1.5)
            
        yield TroveContext(client=client, server_version="1.0.0")
        
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down Trove MCP Server")
        await client.aclose()


# Create FastMCP server with lifespan management and improved instructions
mcp = FastMCP(
    "Trove API",
    instructions="""
    Access Australia's National Library Trove collection containing millions of historical documents.
    
    🗞️ NEWSPAPER SEARCHES are the most valuable for historical research - they contain:
    - Breaking news from 1803-today
    - Detailed historical events and social context  
    - Local perspectives on national events
    - Biographical information in death notices, social pages
    - Economic and social conditions through advertisements
    
    Start with search_page(categories=['newspaper']) for most historical research.
    Other categories (book, image, people) are more specialized collections.
    
    Quick start: search_page(categories=['newspaper'], query='your topic', limits={'state': ['New South Wales'], 'decade': ['190']})
    """,
    lifespan=trove_lifespan
)


@mcp.tool()
async def search_page(
    categories: List[str] = Field(..., description="Categories to search. For historical research, START with ['newspaper'] - contains the richest historical information including news, social context, biographical details in obituaries, and economic conditions. Other categories: 'book' (published works), 'image' (photos/maps/art), 'people' (biographical records), 'magazine', 'music', 'diary', 'list', 'research'"),
    query: Optional[str] = Field(None, description="Search terms. Can be names, places, events, topics. Examples: 'federation ceremony', 'gold rush ballarat', 'women suffrage'. Leave empty to browse by filters only."),
    page_size: int = Field(20, description="Results per category (1-100). Use 50-100 for research, 10-20 for browsing.", ge=1, le=100),
    sort_by: str = Field("relevance", description="Sort order: 'relevance' (best for topic searches), 'date_desc' (newest first), 'date_asc' (chronological)"),
    limits: Optional[Dict[str, Union[str, List[str]]]] = Field(None, description="""Search filters as key-value pairs. ESSENTIAL for newspaper research:
    
    🗞️ NEWSPAPER ESSENTIALS (with dependencies):
    - state: ['New South Wales', 'Victoria', 'Queensland', 'South Australia', 'Western Australia', 'Tasmania', 'Northern Territory', 'Australian Capital Territory']
    - decade: SINGLE decade only! ['185'] for 1850s, ['190'] for 1900s, ['200'] for 2000s, ['201'] for 2010s
      ⚠️ NEVER use multiple decades like ['185','190'] - search ONE decade at a time!
    - year: ['1901', '1902'] - REQUIRES decade for newspaper searches!
    - month: ['01', '02', '03'] - REQUIRES both decade AND year for newspapers!
    
    📚 OTHER FILTERS:
    - format: ['Book', 'Periodical', 'Map', 'Photograph'] 
    - availability: ['y'] for online-only content
    - australian: ['y'] for Australian content only
    - illustrated: ['y'] for illustrated articles
    - artType: ['newspaper', 'gazette'] for article type
    
    ⚠️ IMPORTANT: For newspapers, always include decade when using year!
    
    TESTED Examples:
    - Basic: {'state': ['New South Wales'], 'decade': ['190']} → ~11M results
    - Specific year: {'state': ['Victoria'], 'decade': ['190'], 'year': ['1901']} → ~598K results
    - Specific month: {'decade': ['190'], 'year': ['1901'], 'month': ['01']} → ~237K results"""),
    facets: Optional[List[str]] = Field(None, description="Facets to include for data analysis: ['decade', 'year', 'state', 'format', 'language']. Useful for understanding data distribution before detailed searches."),
    record_level: str = Field("brief", description="Detail level: 'brief' (fast, good for browsing), 'full' (complete metadata, slower)"),
    cursor: Optional[str] = Field(None, description="Pagination cursor from previous search results"),
    bulk_harvest: bool = Field(False, description="Enable for systematic large-scale data collection"),
    ctx: Context[ServerSession, TroveContext] = None
) -> SearchResult:
    """
    🗞️ PRIMARY SEARCH TOOL - Search Australia's Trove digital collection.
    
    **NEWSPAPER SEARCHES ARE BEST FOR HISTORICAL RESEARCH**
    Newspapers (1803-today) contain the richest historical information:
    - Breaking news and detailed event coverage
    - Social context and local perspectives  
    - Biographical details in obituaries and social pages
    - Economic conditions through advertisements
    - Daily life through community news
    
    **TESTED WORKFLOWS:**
    
    1. **Historical Event Research:**
       categories=['newspaper'], query='federation ceremony', limits={'decade': ['190'], 'year': ['1901'], 'state': ['New South Wales']}
       → Returns ~3,200 results about federation ceremonies in NSW in 1901
    
    2. **Biographical Research:**
       categories=['newspaper'], query='Smith family', limits={'decade': ['190'], 'state': ['Victoria']}
       → Returns ~115,000 results mentioning Smith families in Victoria 1900s
       
    3. **Social History:**
       categories=['newspaper'], query='women employment', limits={'decade': ['200'], 'state': ['New South Wales']}
       → Returns ~500 results about women's employment in NSW 2000s
       
    4. **Economic History:**
       categories=['newspaper'], query='mining boom', limits={'state': ['Western Australia'], 'decade': ['190']}
       → Returns ~22,000 results about mining boom in WA 1900s
    
    5. **Specific Date Research:**
       categories=['newspaper'], query='royal visit', limits={'decade': ['190'], 'year': ['1901'], 'month': ['05']}
       → Returns ~13,000 results about royal visits in May 1901
    
    6. **Exploratory Research (use facets first):**
       categories=['newspaper'], query='federation', facets=['decade'], page_size=1
       → Shows data distribution across decades (peak in 1900s with ~1.97M results)
    
    **OTHER CATEGORIES** (more specialized):
    - book: Published works, academic sources
    - image: Photographs, maps, artwork, posters  
    - people: Biographical records and authority files
    - magazine: Periodicals and newsletters
    
    **ESSENTIAL TIPS:**
    - Always specify 'state' for newspaper searches - gets much better results
    - Use 'decade' then 'year' filters for time periods
    - Try both broad and specific search terms
    - Use facets first to understand data distribution
    """
    client = ctx.request_context.lifespan_context.client
    
    # Validate categories
    validate_categories(categories)
    
    # Validate newspaper filter dependencies
    if limits:
        validate_newspaper_filters(categories, limits)
    
    try:
        # Build search using fluent API
        search_builder = client.search()
        
        if query:
            search_builder = search_builder.text(query)
            
        # Add categories
        search_builder = search_builder.in_(*categories)
        
        # Add page size
        search_builder = search_builder.page_size(page_size)
        
        # Add sorting
        if sort_by != "relevance":
            search_builder = search_builder.sort_by(sort_by)
            
        # Add record level
        if record_level == "full":
            search_builder = search_builder.with_reclevel("full")
            
        # Add facets
        if facets:
            search_builder = search_builder.with_facets(*facets)
            
        # Add limits/filters
        if limits:
            for key, value in limits.items():
                filter_values = value if isinstance(value, list) else [value]
                
                # Map common filters to search builder methods
                if key in ["decade", "year", "state", "format", "title"]:
                    method = getattr(search_builder, key, None)
                    if method:
                        search_builder = method(*filter_values)
                elif key == "availability" and "y" in filter_values:
                    search_builder = search_builder.online()
                elif key == "illustrated" and "y" in filter_values:
                    search_builder = search_builder.illustrated()
        
        # Enable bulk harvest if requested
        if bulk_harvest:
            search_builder = search_builder.harvest()
        
        # Handle pagination cursor
        if cursor:
            # The cursor parameter maps to the 's' parameter in SearchParameters
            # We need to create a custom SearchParameters object with the cursor
            params = search_builder._spec.to_parameters()
            params.s = cursor
            results = await client.resources.get_search_resource().apage(params=params)
        else:
            # Execute search normally
            results = await search_builder.afirst_page()
        
        # Extract cursors for pagination
        cursors = {}
        for category in results.categories:
            if 'records' in category and category['records'].get('next'):
                cursors[category['code']] = category['records']['next']
        
        # Build structured response
        return SearchResult(
            query=query,
            total_results=results.total_results,
            categories=results.categories,
            cursors=cursors,
            facets=getattr(results, 'facets', None)
        )
        
    except TroveError as e:
        await ctx.error(f"Trove API error in search: {e}")
        raise Exception(f"Search failed: {e}")
    except Exception as e:
        await ctx.error(f"Unexpected error in search: {e}")
        raise Exception(f"Search failed: {e}")


@mcp.tool()
async def get_work(
    record_id: str,
    include_fields: Optional[List[str]] = None,
    record_level: str = "brief",
    ctx: Context[ServerSession, TroveContext] = None
) -> RecordResult:
    """
    Retrieve a specific work record (book, image, music, etc.) by ID.
    
    Args:
        record_id: Work identifier (numeric ID or PID)
        include_fields: Additional fields to include (e.g., ['workversions', 'holdings'])
        record_level: Detail level - 'brief' or 'full'
        
    Returns:
        RecordResult with complete work data
    """
    client = ctx.request_context.lifespan_context.client
    
    try:
        # Get the work record
        work = await client.resources.get_work_resource().aget(
            record_id,
            include=include_fields,
            reclevel=record_level
        )
        
        # Build metadata
        metadata = {
            "record_type": "work",
            "record_id": record_id,
            "detail_level": record_level
        }
        
        if include_fields:
            metadata["included_fields"] = ", ".join(include_fields)
        
        return RecordResult(
            record_type="work",
            record_id=record_id,
            data=work.raw if hasattr(work, 'raw') else work,
            metadata=metadata
        )
        
    except ResourceNotFoundError:
        raise Exception(f"Work record {record_id} not found")
    except TroveError as e:
        await ctx.error(f"Trove API error getting work {record_id}: {e}")
        raise Exception(f"Failed to get work: {e}")


@mcp.tool()
async def get_article(
    article_id: str,
    article_type: str = "newspaper",
    include_fields: Optional[Union[str, List[str]]] = None,
    record_level: str = "brief",
    ctx: Context[ServerSession, TroveContext] = None
) -> RecordResult:
    """
    Retrieve a specific newspaper or gazette article by ID.
    
    Args:
        article_id: Article identifier (numeric ID from search results)
        article_type: Article source type - 'newspaper' or 'gazette'
        include_fields: Additional fields as array (['articletext', 'comments', 'lists', 'tags'])
        record_level: Detail level - 'brief' or 'full'
        
    Returns:
        RecordResult with complete article data
    """
    client = ctx.request_context.lifespan_context.client
    
    try:
        # Choose the appropriate resource
        if article_type == "gazette":
            article = await client.resources.get_gazette_resource().aget(
                article_id,
                include=include_fields,
                reclevel=record_level
            )
        else:
            article = await client.resources.get_newspaper_resource().aget(
                article_id,
                include=include_fields,
                reclevel=record_level
            )
        
        metadata = {
            "record_type": f"{article_type}_article",
            "record_id": article_id,
            "detail_level": record_level
        }
        
        if include_fields:
            fields = include_fields if isinstance(include_fields, list) else [include_fields]
            metadata["included_fields"] = ", ".join(fields)
        
        return RecordResult(
            record_type=f"{article_type}_article",
            record_id=article_id,
            data=article.raw if hasattr(article, 'raw') else article,
            metadata=metadata
        )
        
    except ResourceNotFoundError:
        raise Exception(f"{article_type.title()} article {article_id} not found")
    except TroveError as e:
        await ctx.error(f"Trove API error getting {article_type} article {article_id}: {e}")
        raise Exception(f"Failed to get article: {e}")


@mcp.tool()
async def get_people(
    record_id: str,
    include_fields: Optional[List[str]] = None,
    record_level: str = "brief",
    ctx: Context[ServerSession, TroveContext] = None
) -> RecordResult:
    """
    Retrieve a specific people or organization record by ID.
    
    Args:
        record_id: People record identifier (numeric ID or PID)
        include_fields: Additional fields to include
        record_level: Detail level - 'brief' or 'full'
        
    Returns:
        RecordResult with complete people/organization data
    """
    client = ctx.request_context.lifespan_context.client
    
    try:
        person = await client.resources.get_people_resource().aget(
            record_id,
            include=include_fields,
            reclevel=record_level
        )
        
        metadata = {
            "record_type": "people",
            "record_id": record_id,
            "detail_level": record_level
        }
        
        if include_fields:
            metadata["included_fields"] = ", ".join(include_fields)
        
        return RecordResult(
            record_type="people",
            record_id=record_id,
            data=person.raw if hasattr(person, 'raw') else person,
            metadata=metadata
        )
        
    except ResourceNotFoundError:
        raise Exception(f"People record {record_id} not found")
    except TroveError as e:
        await ctx.error(f"Trove API error getting people record {record_id}: {e}")
        raise Exception(f"Failed to get people record: {e}")


@mcp.tool()
async def get_list(
    record_id: str,
    include_fields: Optional[List[str]] = None,
    record_level: str = "brief",
    ctx: Context[ServerSession, TroveContext] = None
) -> RecordResult:
    """
    Retrieve a specific user-created list by ID.
    
    Args:
        record_id: List identifier (numeric ID or PID)
        include_fields: Additional fields to include
        record_level: Detail level - 'brief' or 'full'
        
    Returns:
        RecordResult with complete list data
    """
    client = ctx.request_context.lifespan_context.client
    
    try:
        trove_list = await client.resources.get_list_resource().aget(
            record_id,
            include=include_fields,
            reclevel=record_level
        )
        
        metadata = {
            "record_type": "list",
            "record_id": record_id,
            "detail_level": record_level
        }
        
        if include_fields:
            metadata["included_fields"] = ", ".join(include_fields)
        
        return RecordResult(
            record_type="list",
            record_id=record_id,
            data=trove_list.raw if hasattr(trove_list, 'raw') else trove_list,
            metadata=metadata
        )
        
    except ResourceNotFoundError:
        raise Exception(f"List {record_id} not found")
    except TroveError as e:
        await ctx.error(f"Trove API error getting list {record_id}: {e}")
        raise Exception(f"Failed to get list: {e}")


@mcp.tool()
async def resolve_pid(
    identifier: str,
    ctx: Context[ServerSession, TroveContext] = None
) -> PIDResolution:
    """
    Resolve a PID, URL, or identifier to detailed record information.
    
    Supports:
    - Trove PIDs (e.g., nla.obj-123456789, nla.news-article18341291)
    - Trove URLs (web interface and API URLs)
    - Bare record IDs (attempts resolution across record types)
    
    Args:
        identifier: PID, URL, or identifier to resolve
        
    Returns:
        PIDResolution with basic record information
    """
    client = ctx.request_context.lifespan_context.client
    
    try:
        # Use the client's resolution capability if available
        # This is a simplified implementation - the actual trove-sdk may have
        # dedicated PID resolution methods
        
        # Try to extract record info from common patterns
        resolved_info = await _resolve_identifier(client, identifier, ctx)
        
        return PIDResolution(
            original_identifier=identifier,
            resolved_type=resolved_info["type"],
            record_id=resolved_info["id"],
            title=resolved_info.get("title"),
            url=resolved_info.get("url")
        )
        
    except Exception as e:
        await ctx.error(f"Failed to resolve identifier {identifier}: {e}")
        raise Exception(f"Resolution failed: {e}")


@mcp.tool()
async def cite_bibtex(
    source: Union[str, Dict[str, Any]],
    record_type: Optional[str] = None,
    ctx: Context[ServerSession, TroveContext] = None
) -> CitationResult:
    """
    Generate BibTeX format citation for Trove records.
    
    Args:
        source: PID/URL to cite, or raw record data
        record_type: Record type when providing raw data (work, article, people, list)
        
    Returns:
        CitationResult with properly formatted BibTeX citation
    """
    client = ctx.request_context.lifespan_context.client
    
    try:
        # If source is a string, treat as PID/URL
        if isinstance(source, str):
            # Resolve and get the record for citation
            resolved = await resolve_pid(source, ctx)
            record_type = resolved.resolved_type
            record_id = resolved.record_id
            
            # Get the actual record data for citation
            if record_type == "work":
                record_data = await client.resources.get_work_resource().aget(record_id)
            elif "article" in record_type:
                if "gazette" in record_type:
                    record_data = await client.resources.get_gazette_resource().aget(record_id)
                else:
                    record_data = await client.resources.get_newspaper_resource().aget(record_id)
            elif record_type == "people":
                record_data = await client.resources.get_people_resource().aget(record_id)
            elif record_type == "list":
                record_data = await client.resources.get_list_resource().aget(record_id)
            else:
                raise ValueError(f"Unsupported record type for citation: {record_type}")
        else:
            # Source is raw record data
            record_data = source
            record_id = str(source.get('id', 'unknown'))
            if not record_type:
                raise ValueError("record_type required when providing raw record data")
        
        # Generate BibTeX citation using client's citation functionality
        # This assumes the client has citation support - adapt based on actual API
        if hasattr(client, 'citations'):
            citation_text = await client.citations.acite_bibtex(record_data)
        else:
            # Fallback to basic BibTeX generation
            citation_text = _generate_basic_bibtex(record_data, record_type, record_id)
        
        return CitationResult(
            format="bibtex",
            citation=citation_text,
            record_id=record_id,
            record_type=record_type
        )
        
    except Exception as e:
        await ctx.error(f"Failed to generate BibTeX citation: {e}")
        raise Exception(f"Citation generation failed: {e}")


@mcp.tool()
async def cite_csl_json(
    source: Union[str, Dict[str, Any]],
    record_type: Optional[str] = None,
    ctx: Context[ServerSession, TroveContext] = None
) -> CitationResult:
    """
    Generate CSL-JSON format citation for Trove records.
    
    Args:
        source: PID/URL to cite, or raw record data
        record_type: Record type when providing raw data (work, article, people, list)
        
    Returns:
        CitationResult with properly formatted CSL-JSON citation
    """
    client = ctx.request_context.lifespan_context.client
    
    try:
        # Similar logic to cite_bibtex but for CSL-JSON
        if isinstance(source, str):
            resolved = await resolve_pid(source, ctx)
            record_type = resolved.resolved_type
            record_id = resolved.record_id
            
            # Get the actual record data
            if record_type == "work":
                record_data = await client.resources.get_work_resource().aget(record_id)
            elif "article" in record_type:
                if "gazette" in record_type:
                    record_data = await client.resources.get_gazette_resource().aget(record_id)
                else:
                    record_data = await client.resources.get_newspaper_resource().aget(record_id)
            elif record_type == "people":
                record_data = await client.resources.get_people_resource().aget(record_id)
            elif record_type == "list":
                record_data = await client.resources.get_list_resource().aget(record_id)
            else:
                raise ValueError(f"Unsupported record type for citation: {record_type}")
        else:
            record_data = source
            record_id = str(source.get('id', 'unknown'))
            if not record_type:
                raise ValueError("record_type required when providing raw record data")
        
        # Generate CSL-JSON citation
        if hasattr(client, 'citations'):
            citation_text = await client.citations.acite_csl_json(record_data)
        else:
            # Fallback to basic CSL-JSON generation
            citation_text = _generate_basic_csl_json(record_data, record_type, record_id)
        
        return CitationResult(
            format="csl_json",
            citation=citation_text,
            record_id=record_id,
            record_type=record_type
        )
        
    except Exception as e:
        await ctx.error(f"Failed to generate CSL-JSON citation: {e}")
        raise Exception(f"Citation generation failed: {e}")


# Helper functions

async def _resolve_identifier(client: TroveClient, identifier: str, ctx: Context) -> Dict[str, Any]:
    """Helper to resolve various identifier formats to record information."""
    # This is a simplified implementation - would need full PID resolution logic
    
    # Handle common patterns
    if identifier.startswith("nla.obj-"):
        # Work PID
        record_id = identifier.replace("nla.obj-", "")
        work = await client.resources.get_work_resource().aget(record_id, reclevel="brief")
        return {
            "type": "work",
            "id": record_id,
            "title": getattr(work, 'primary_title', work.get('title', 'Untitled Work')),
            "url": f"https://trove.nla.gov.au/work/{record_id}"
        }
    elif identifier.startswith("nla.news-article"):
        # Article PID
        record_id = identifier.replace("nla.news-article", "")
        article = await client.resources.get_newspaper_resource().aget(record_id, reclevel="brief")
        return {
            "type": "newspaper_article",
            "id": record_id,
            "title": getattr(article, 'display_title', article.get('heading', 'Untitled Article')),
            "url": f"https://trove.nla.gov.au/newspaper/article/{record_id}"
        }
    elif identifier.startswith("https://trove.nla.gov.au/"):
        # Trove URL - extract ID and type
        await ctx.info(f"Parsing Trove URL: {identifier}")
        # Would need URL parsing logic here
        raise NotImplementedError("URL parsing not yet implemented")
    else:
        # Bare ID - try as work first
        try:
            work = await client.resources.get_work_resource().aget(identifier, reclevel="brief")
            return {
                "type": "work", 
                "id": identifier,
                "title": getattr(work, 'primary_title', work.get('title', 'Untitled Work')),
                "url": f"https://trove.nla.gov.au/work/{identifier}"
            }
        except ResourceNotFoundError:
            # Try as article
            try:
                article = await client.resources.get_newspaper_resource().aget(identifier, reclevel="brief")
                return {
                    "type": "newspaper_article",
                    "id": identifier,
                    "title": getattr(article, 'display_title', article.get('heading', 'Untitled Article')),
                    "url": f"https://trove.nla.gov.au/newspaper/article/{identifier}"
                }
            except ResourceNotFoundError:
                raise Exception(f"Could not resolve identifier: {identifier}")


def _generate_basic_bibtex(record_data: Any, record_type: str, record_id: str) -> str:
    """Generate basic BibTeX citation."""
    # Simplified BibTeX generation - would need full implementation
    if record_type == "work":
        title = getattr(record_data, 'primary_title', record_data.get('title', 'Untitled'))
        author = getattr(record_data, 'primary_contributor', record_data.get('contributor', ['Unknown'])[0] if record_data.get('contributor') else 'Unknown')
        year = getattr(record_data, 'publication_year', record_data.get('issued', 'n.d.'))
        
        return f"""@book{{{record_id},
  title = {{{title}}},
  author = {{{author}}},
  year = {{{year}}},
  url = {{https://trove.nla.gov.au/work/{record_id}}},
  note = {{Trove work ID: {record_id}}}
}}"""
    else:
        return f"@misc{{{record_id},\n  note = {{Trove {record_type} ID: {record_id}}}\n}}"


def _generate_basic_csl_json(record_data: Any, record_type: str, record_id: str) -> str:
    """Generate basic CSL-JSON citation."""
    import json
    
    # Simplified CSL-JSON generation
    csl_data = {
        "id": record_id,
        "type": "book" if record_type == "work" else "webpage",
        "URL": f"https://trove.nla.gov.au/{record_type}/{record_id}"
    }
    
    if record_type == "work":
        csl_data.update({
            "title": getattr(record_data, 'primary_title', record_data.get('title', 'Untitled')),
            "author": [{"literal": getattr(record_data, 'primary_contributor', 'Unknown')}]
        })
        
        year = getattr(record_data, 'publication_year', None)
        if year:
            csl_data["issued"] = {"date-parts": [[year]]}
    
    return json.dumps(csl_data, indent=2)


@mcp.resource("trove://categories")
def get_valid_categories() -> str:
    """List of valid Trove search categories with descriptions from official API docs"""
    import json
    
    categories_info = {
        "description": "Valid categories for Trove API v3 searches",
        "categories": [
            {"code": "all", "name": "Everything except the Web", "description": "All available categories"},
            {"code": "book", "name": "Books & Libraries", "description": "Books and library materials"},
            {"code": "diary", "name": "Diaries, Letters & Archives", "description": "Personal papers and archival materials"},
            {"code": "image", "name": "Images, Maps & Artefacts", "description": "Visual materials and objects (includes maps, photographs, artworks, etc.)"},
            {"code": "list", "name": "Lists", "description": "User-created lists"},
            {"code": "magazine", "name": "Magazines & Newsletters", "description": "Periodical publications"},
            {"code": "music", "name": "Music, Audio & Video", "description": "Audio and video materials"},
            {"code": "newspaper", "name": "Newspapers & Gazettes", "description": "Newspaper and gazette articles"},
            {"code": "people", "name": "People & Organisations", "description": "Person and organisation records"},
            {"code": "research", "name": "Research & Reports", "description": "Research publications and reports"}
        ],
        "usage_notes": [
            "Use the category code as the identifier in searches",
            "Multiple categories can be specified in the categories array", 
            "Search specific categories for faster responses",
            "Note: Maps are included in the 'image' category, not as a separate 'map' category"
        ]
    }
    return json.dumps(categories_info, indent=2)


@mcp.resource("trove://api-capabilities")
def get_api_capabilities() -> str:
    """Comprehensive guide to Trove MCP server capabilities"""
    import json
    
    capabilities = {
        "server_info": {
            "name": "Trove MCP Server",
            "version": "1.0.0",
            "description": "Access to Australia's National Library Trove collection via MCP"
        },
        "tools": {
            "search_page": {
                "description": "Search Trove records across categories with filtering",
                "required_parameters": ["categories"],
                "optional_parameters": ["query", "page_size", "sort_by", "limits", "facets", "record_level"],
                "examples": [
                    {
                        "name": "Basic book search",
                        "parameters": {
                            "categories": ["book"],
                            "query": "Australian history",
                            "page_size": 10
                        }
                    },
                    {
                        "name": "Newspaper search with filters",
                        "parameters": {
                            "categories": ["newspaper"],
                            "query": "federation",
                            "limits": {"decade": ["190"], "state": ["NSW"]}
                        }
                    }
                ]
            },
            "get_work": {
                "description": "Retrieve specific work record by ID",
                "parameters": ["record_id", "include_fields", "record_level"]
            },
            "get_article": {
                "description": "Retrieve newspaper or gazette article by ID", 
                "parameters": ["article_id", "article_type", "include_fields", "record_level"],
                "examples": [
                    {
                        "name": "Get article with full text",
                        "parameters": {
                            "article_id": "19488715",
                            "article_type": "newspaper",
                            "include_fields": ["articletext"],
                            "record_level": "full"
                        }
                    }
                ]
            }
        },
        "search_options": {
            "sort_by": ["relevance", "date_asc", "date_desc"],
            "record_level": ["brief", "full"],
            "common_limits": {
                "decade": "e.g., ['200'] for 2000s",
                "year": "e.g., ['2020', '2021']",
                "state": "e.g., ['NSW', 'VIC']"
            }
        },
        "common_mistakes": {
            "invalid_categories": "Don't use 'article', 'collection', 'map' - these are not valid categories",
            "limits_format": "Use object format: {\"decade\": [\"183\"]} not string format",
            "include_fields": "Always use array format: [\"articletext\"] not string \"articletext\"",
            "category_mapping": {
                "article": "Use 'newspaper' or 'magazine' instead",
                "collection": "Use 'list' instead", 
                "map": "Use 'image' instead"
            }
        }
    }
    return json.dumps(capabilities, indent=2)


@mcp.resource("trove://status")
def get_server_status() -> str:
    """Current server status and configuration"""
    import json
    
    status_info = {
        "status": "active",
        "api_key_configured": bool(os.getenv('TROVE_API_KEY')),
        "rate_limit": "configured",
        "cache_backend": "memory",
        "supported_categories": sorted(VALID_CATEGORIES),
        "available_tools": [
            "search_page", "get_work", "get_article", 
            "get_people", "get_list", "resolve_pid", 
            "cite_bibtex", "cite_csl_json"
        ],
        "resources": [
            "trove://categories - Valid search categories",
            "trove://api-capabilities - API usage guide", 
            "trove://status - This status information"
        ]
    }
    return json.dumps(status_info, indent=2)


@mcp.prompt()
def historical_research_workflow(topic: str, time_period: str = "1900s", location: str = "Australia") -> str:
    """
    Step-by-step workflow for conducting historical research using Trove newspapers.
    Essential for comprehensive historical investigation.
    """
    decade_map = {
        "1800s": "180", "1810s": "181", "1820s": "182", "1830s": "183", "1840s": "184",
        "1850s": "185", "1860s": "186", "1870s": "187", "1880s": "188", "1890s": "189",
        "1900s": "190", "1910s": "191", "1920s": "192", "1930s": "193", "1940s": "194",
        "1950s": "195", "1960s": "196", "1970s": "197", "1980s": "198", "1990s": "199",
        "2000s": "200", "2010s": "201", "2020s": "202"
    }
    
    decade = decade_map.get(time_period, "190")
    
    return f"""
# Historical Research Workflow: {topic} ({time_period})

🗞️ **NEWSPAPERS ARE YOUR PRIMARY SOURCE** - they contain the richest historical information!

## Step 1: Exploratory Search (Start Here)
```
search_page(
    categories=['newspaper'], 
    query='{topic}', 
    facets=['decade', 'state'], 
    page_size=1
)
```
**Purpose:** Understand data distribution across time and location

## Step 2: Focused Location Search (Single Decade)
```
search_page(
    categories=['newspaper'], 
    query='{topic}', 
    limits={{'decade': ['{decade}'], 'state': ['{location}']}},
    page_size=50
)
```
**Purpose:** Get substantial results from your target time/place

## Step 2b: Search Additional Decades (If Needed)
For topics spanning multiple decades, search each decade separately:
```
search_page(
    categories=['newspaper'], 
    query='{topic}', 
    limits={{'decade': ['183'], 'state': ['{location}']}},  # 1830s
    page_size=50
)
```
**Note:** Never combine decades like ['183','184'] - search each separately!

## Step 3: Detailed Record Retrieval
For each interesting article from Step 2:
```
get_article(
    article_id='[from search results]', 
    include_fields=['articletext'], 
    record_level='full'
)
```
**Purpose:** Get full text and detailed information

## Step 4: Citation Generation
```
cite_bibtex(source='[article PID or URL]')
```
**Purpose:** Generate proper academic citations

## 💡 Research Tips:
- Try both broad terms ('{topic}') and specific phrases ('{topic} ceremony')
- Search multiple decades to see how coverage changed over time
- Look for obituaries and social pages for biographical information
- Check advertisements for economic and social context
- Use different state filters to get diverse perspectives

## 🔍 Alternative Categories (if needed):
- **book**: Academic sources and published works about {topic}
- **image**: Photographs and illustrations related to {topic}  
- **people**: Biographical records of key figures
"""


@mcp.prompt()
def newspaper_search_guide(research_goal: str = "general historical research") -> str:
    """
    Quick reference guide for newspaper searching strategies and filter combinations.
    """
    return f"""
# Newspaper Search Quick Guide ({research_goal})

## 🎯 Search Strategy for Historical Research

### Start with Location + Time Period
Most effective approach for newspapers:
```
categories=['newspaper']
limits={{'state': ['New South Wales'], 'decade': ['190']}}
```

### Add Specific Years When Needed
```
limits={{'state': ['Victoria'], 'decade': ['190'], 'year': ['1901']}}
```

### Get Specific with Months
```
limits={{'decade': ['190'], 'year': ['1901'], 'month': ['01']}}
```

## 📍 Australian States (use full names):
- 'New South Wales' - Most digitized newspapers
- 'Victoria' - Strong 19th/20th century coverage  
- 'Queensland' - Good regional coverage
- 'South Australia' - Early colonial period
- 'Western Australia' - Mining and development
- 'Tasmania' - Oldest Australian newspapers (1803+)

## 📅 Time Periods (decades):
- '180' = 1800-1809 (early colonial)
- '190' = 1900-1909 (federation era) 
- '194' = 1940-1949 (WWII period)
- '200' = 2000-2009 (modern digital era)

## 🔍 Search Query Tips:
- **People**: Use full names, try variations
- **Events**: Use contemporary terms (not modern descriptions)
- **Places**: Try historical names and current names
- **Topics**: Start broad, then narrow with filters

## ⚠️ Critical Rules:
1. **ALWAYS specify state** for newspaper searches
2. **ALWAYS include decade when using year**
3. **Use facets first** to understand data distribution
4. **Try multiple search terms** for the same concept

## 📊 Use Facets for Data Analysis:
```
facets=['decade', 'state', 'format']
page_size=1  # Just need the facets, not results
```
"""


@mcp.completion()
async def complete_search_parameters(
    ref: Union[str, dict],
    argument: dict,
    ctx: Context[ServerSession, TroveContext]
) -> list[str]:
    """Provide completion suggestions for search parameters"""
    arg_name = argument.get("name", "")
    arg_value = argument.get("value", "")
    
    if arg_name == "categories":
        # Return categories that match current input, with newspaper first
        categories = ["newspaper"] + [cat for cat in sorted(VALID_CATEGORIES) if cat != "newspaper"]
        if arg_value:
            matching = [cat for cat in categories if cat.lower().startswith(arg_value.lower())]
            return matching
        return categories
    
    elif arg_name == "sort_by":
        sort_options = ["relevance", "date_desc", "date_asc"]
        if arg_value:
            matching = [opt for opt in sort_options if opt.startswith(arg_value.lower())]
            return matching
        return sort_options
    
    elif arg_name == "record_level":
        return ["brief", "full"]
    
    elif arg_name == "article_type":
        return ["newspaper", "gazette"]
        
    elif arg_name == "limits" and "state" in str(arg_value):
        # Suggest Australian states
        states = [
            "New South Wales", "Victoria", "Queensland", "South Australia", 
            "Western Australia", "Tasmania", "Northern Territory", "Australian Capital Territory"
        ]
        return states
    
    return []


def main():
    """Main entry point for the MCP server."""
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="Trove MCP Server")
    parser.add_argument(
        "--transport", 
        default="stdio",
        choices=["stdio", "sse", "streamable-http"],
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
    
    # Run server
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()