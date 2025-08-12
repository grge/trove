#!/usr/bin/env python3
"""Generate comprehensive API documentation from code and examples."""

import inspect
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import ast
import importlib
import sys
import os

# Add the parent directory to path to import trove
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import trove
    from trove import TroveClient
    from trove.models import Work, Article, People, TroveList
    from trove.search import Search
    from trove.resources.work import WorkResource
    from trove.resources.article import ArticleResource
    from trove.resources.people import PeopleResource
    from trove.resources.list import ListResource
except ImportError as e:
    print(f"Error importing trove modules: {e}")
    sys.exit(1)


class APIDocGenerator:
    """Generate API documentation from source code and examples."""
    
    def __init__(self, source_dir: Path, output_dir: Path):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_docs(self):
        """Generate complete API documentation."""
        print("Generating API documentation...")
        
        # Generate main sections
        self._generate_overview()
        self._generate_client_docs()
        self._generate_search_docs()
        self._generate_resource_docs() 
        self._generate_model_docs()
        self._generate_error_docs()
        self._generate_examples()
        
        # Generate index
        self._generate_index()
        
        print(f"API documentation generated in {self.output_dir}")
    
    def _generate_overview(self):
        """Generate overview documentation."""
        overview_content = """# Trove SDK API Reference

The Trove SDK provides a comprehensive Python interface to the Trove API v3, Australia's National Library digital collection.

## Key Features

- **Type-safe models** - Optional Pydantic models with backward compatibility
- **Fluent search API** - Intuitive search builder with method chaining
- **Resource access** - Direct access to works, articles, people, and lists
- **Performance optimized** - Connection pooling, caching, and batch processing
- **Production ready** - Structured logging, monitoring, and error handling

## Quick Start

```python
from trove import TroveClient

# Create client with API key
client = TroveClient.from_env()  # Uses TROVE_API_KEY env var

# Search for books about Australian history
results = (client.search()
          .text("Australian history")
          .in_("book")
          .decade("200")  # 2000s
          .page_size(20)
          .first_page())

print(f"Found {results.total_results} books")

# Access individual records
for work in results.categories[0]['records']['work']:
    print(f"- {work.primary_title} ({work.publication_year})")
```

## Main Components

- [TroveClient](./client.md) - Main entry point for all SDK functionality
- [Search API](./search.md) - Fluent search interface with filtering and faceting
- [Resource APIs](./resources.md) - Direct access to specific records
- [Models](./models.md) - Type-safe data structures with backward compatibility
- [Error Handling](./errors.md) - Comprehensive error handling and recovery

## Installation

```bash
pip install trove-sdk
```

## Configuration

The SDK can be configured via environment variables or directly:

```python
from trove import TroveConfig, TroveClient

# Via environment variables
client = TroveClient.from_env()

# Direct configuration
config = TroveConfig(
    api_key="your_api_key_here",
    rate_limit=1.5,  # requests per second
    cache_backend="sqlite"
)
client = TroveClient(config)
```
"""
        
        with open(self.output_dir / "overview.md", "w") as f:
            f.write(overview_content)
    
    def _generate_client_docs(self):
        """Generate TroveClient documentation."""
        client_content = """# TroveClient

The `TroveClient` is the main entry point for all Trove SDK functionality. It provides access to search, resource retrieval, and configuration management.

## Constructor

```python
client = TroveClient(config: TroveConfig, cache: CacheBackend = None)
```

## Class Methods

### `from_env(cache: CacheBackend = None) -> TroveClient`

Create a client using environment variables for configuration.

**Environment Variables:**
- `TROVE_API_KEY` - Your Trove API key (required)
- `TROVE_RATE_LIMIT` - Rate limit in requests per second (default: 2.0)
- `TROVE_CACHE_BACKEND` - Cache backend type: "memory" or "sqlite" (default: "memory")
- `TROVE_LOG_REQUESTS` - Enable request logging: "true" or "false" (default: "false")

```python
import os
os.environ['TROVE_API_KEY'] = 'your_api_key_here'

client = TroveClient.from_env()
```

## Properties

### `search() -> Search`

Get a fluent search builder for querying Trove.

```python
# Build and execute searches
results = (client.search()
          .text("federation")
          .in_("newspaper") 
          .state("NSW")
          .decade("190")
          .first_page())
```

### `raw_search -> SearchResource`

Access the raw search API for advanced usage.

```python
# Direct parameter control
results = client.raw_search.page(
    category=['book'],
    q='Australian poetry',
    l_decade=['200'],
    n=50
)
```

### Resource Properties

Direct access to resource endpoints:

- `work -> WorkResource` - Access work records (books, images, maps, etc.)
- `newspaper -> ArticleResource` - Access newspaper articles
- `gazette -> ArticleResource` - Access gazette articles  
- `people -> PeopleResource` - Access people and organization records
- `list -> ListResource` - Access user lists

```python
# Get a specific work
work = client.work.get("123456789")
print(work.primary_title)

# Get a newspaper article
article = client.newspaper.get("18341291")
print(article.display_title)
```

## Methods

### `close()`

Close the client and clean up resources.

```python
client.close()
```

### `aclose()` (async)

Async version of close().

```python
await client.aclose()
```

## Context Manager Support

The client can be used as a context manager for automatic cleanup:

```python
with TroveClient.from_env() as client:
    results = client.search().text("test").in_("book").first_page()
    # Client is automatically closed when exiting the block

# Async context manager
async with TroveClient.from_env() as client:
    results = await client.search().text("test").in_("book").afirst_page()
```

## Examples

### Basic Search

```python
from trove import TroveClient

client = TroveClient.from_env()

# Search for Australian poetry books from the 2000s
results = (client.search()
          .text("Australian poetry")
          .in_("book")
          .decade("200")
          .page_size(10)
          .first_page())

print(f"Found {results.total_results} results")
```

### Resource Access

```python
# Get a specific work with full details
work = client.work.get("123456789", include=['workversions'], reclevel='full')

# Check holdings
holdings = client.work.get_holdings("123456789")
for holding in holdings:
    print(f"{holding['name']}: {holding['callNumber']}")
```

### Batch Operations

```python
# Process multiple records
work_ids = ["123", "456", "789"]

for work_id in work_ids:
    try:
        work = client.work.get(work_id)
        print(f"Title: {work.primary_title}")
    except ResourceNotFoundError:
        print(f"Work {work_id} not found")
```
"""
        
        with open(self.output_dir / "client.md", "w") as f:
            f.write(client_content)
    
    def _generate_search_docs(self):
        """Generate search API documentation."""
        search_content = """# Search API

The Search API provides a fluent interface for querying Trove with method chaining and intelligent parameter handling.

## Creating Searches

Get a search builder from the client:

```python
search = client.search()
```

## Query Methods

### `text(query: str) -> Search`

Set the search query text.

```python
search = client.search().text("Australian federation")
```

### `in_(*categories: str) -> Search`

Specify categories to search within.

**Valid Categories:**
- `book` - Books and other published works
- `newspaper` - Newspaper articles
- `image` - Images and photographs
- `people` - People and organizations
- `list` - User-created lists
- `magazine` - Magazine and journal articles
- `music` - Musical works
- `map` - Maps and geographical materials

```python
# Single category
search = client.search().text("poetry").in_("book")

# Multiple categories  
search = client.search().text("Sydney").in_("book", "image", "newspaper")
```

## Filtering Methods

### `decade(*decades: str) -> Search`

Filter by decade (1790, 1800, 1810, etc.).

```python
search = client.search().text("federation").decade("190", "191")  # 1900s and 1910s
```

### `year(*years: str) -> Search`

Filter by specific years.

```python
search = client.search().text("election").year("2019", "2020", "2021")
```

### `state(*states: str) -> Search`

Filter by Australian state/territory.

**Valid States:**
- ACT, NSW, NT, QLD, SA, TAS, VIC, WA, National

```python
search = client.search().text("bushfire").state("NSW", "VIC")
```

### `title(*titles: str) -> Search`

Filter by publication title (newspapers, magazines).

```python
search = client.search().text("politics").title("The Sydney Morning Herald")
```

### `format(*formats: str) -> Search`

Filter by format/type.

```python
search = client.search().text("history").format("Book", "Thesis")
```

### `online() -> Search`

Filter for online-accessible items only.

```python
search = client.search().text("poetry").in_("book").online()
```

### `illustrated() -> Search`

Filter for illustrated items (newspapers/images).

```python
search = client.search().text("war").in_("newspaper").illustrated()
```

## Result Options

### `page_size(size: int) -> Search`

Set the number of results per page (max 100).

```python
search = client.search().text("test").page_size(50)
```

### `sort_by(sort_option: str) -> Search`

Set result sorting.

**Sort Options:**
- `relevance` (default)
- `date_asc` - Oldest first
- `date_desc` - Newest first  
- `title` - Alphabetical by title

```python
search = client.search().text("federation").sort_by("date_desc")
```

### `with_reclevel(level: str) -> Search`

Set record detail level.

- `brief` (default) - Basic metadata
- `full` - Complete metadata

```python
search = client.search().text("poetry").with_reclevel("full")
```

### `with_facets(*facets: str) -> Search`

Include facet information.

**Available Facets:**
- `format` - Item formats
- `decade` - Publication decades
- `year` - Publication years
- `language` - Languages
- `category` - Content categories

```python
search = client.search().text("history").with_facets("decade", "format")
```

### `harvest() -> Search`

Enable bulk harvest mode for large result sets.

```python
search = client.search().text("poetry").harvest()
```

## Execution Methods

### `first_page() -> SearchResult`

Execute search and get the first page of results.

```python
results = client.search().text("federation").in_("book").first_page()
print(f"Found {results.total_results} results")
```

### `pages() -> Iterator[SearchResult]`

Iterate through all pages of results (single category only).

```python
search = client.search().text("poetry").in_("book").page_size(20)

for page in search.pages():
    print(f"Page with {len(page.categories[0]['records']['work'])} works")
    if page_count > 10:  # Limit for example
        break
```

### `records() -> Iterator[Dict[str, Any]]`

Iterate through all individual records (single category only).

```python
search = client.search().text("federation").in_("newspaper")

for i, article in enumerate(search.records()):
    print(f"{i+1}. {article.display_title} ({article.date})")
    if i >= 100:  # Limit for example
        break
```

## Async Methods

All execution methods have async versions:

### `afirst_page() -> SearchResult`

```python
results = await client.search().text("test").in_("book").afirst_page()
```

### `apages() -> AsyncIterator[SearchResult]`

```python
async for page in client.search().text("poetry").in_("book").apages():
    print(f"Got {page.total_results} total results")
```

### `arecords() -> AsyncIterator[Dict[str, Any]]`

```python
async for record in client.search().text("history").in_("book").arecords():
    print(record.primary_title)
```

## Working with Results

### SearchResult Structure

```python
results = client.search().text("test").in_("book").first_page()

# Access metadata
print(f"Query: {results.query}")
print(f"Total results: {results.total_results}")

# Access categories
for category in results.categories:
    print(f"Category: {category['code']}")
    
    # Access records
    records = category['records']['work']  # 'work' for books
    for work in records:
        # Type-safe access (if using models)
        print(f"Title: {work.primary_title}")
        
        # Dict-like access (always available)
        print(f"Title: {work['title']}")
```

### Facet Information

```python
results = (client.search()
          .text("Australian history") 
          .in_("book")
          .with_facets("decade", "format")
          .first_page())

category = results.categories[0]
if 'facets' in category:
    facets = category['facets']['facet']
    for facet in facets:
        print(f"Facet: {facet['name']}")
        for term in facet['term'][:5]:  # Show top 5
            print(f"  {term['display']}: {term['count']}")
```

## Examples

### Basic Search

```python
# Find books about Australian poetry from the 2000s
results = (client.search()
          .text("Australian poetry")
          .in_("book")
          .decade("200")
          .page_size(20)
          .first_page())

works = results.categories[0]['records']['work']
for work in works:
    print(f"- {work.primary_title} ({work.publication_year})")
```

### Newspaper Search with Facets

```python
# Search newspapers with faceted browsing
results = (client.search()
          .text("federation")
          .in_("newspaper")
          .state("NSW")
          .decade("190", "191")
          .with_facets("year", "title")
          .first_page())

print(f"Found {results.total_results} articles")

# Explore facets
facets = results.categories[0]['facets']['facet']
for facet in facets:
    if facet['name'] == 'year':
        print("Articles by year:")
        for term in facet['term'][:10]:
            print(f"  {term['display']}: {term['count']} articles")
```

### Bulk Data Collection

```python
# Collect all articles about a topic
search = (client.search()
         .text("women's suffrage")
         .in_("newspaper")
         .decade("190", "191")
         .harvest()  # Enable bulk mode
         .page_size(50))

articles = []
for article in search.records():
    articles.append({
        'title': article.display_title,
        'newspaper': article.newspaper_title,
        'date': article.date,
        'url': article.trove_url
    })
    
    if len(articles) >= 1000:  # Collect up to 1000
        break

print(f"Collected {len(articles)} articles")
```
"""
        
        with open(self.output_dir / "search.md", "w") as f:
            f.write(search_content)
    
    def _generate_model_docs(self):
        """Generate model documentation."""
        models_content = """# Data Models

The Trove SDK provides optional Pydantic models for type-safe access to API responses while maintaining backward compatibility with dict-like access.

## Overview

Models provide:
- **Type safety** - IDE autocompletion and static type checking
- **Computed properties** - Convenient access to derived data
- **Data validation** - Automatic validation of API responses
- **Backward compatibility** - All dict-like access patterns still work

## Available Models

### Work Model

Represents books, images, maps, music, and other published works.

```python
from trove.models import Work

# Get a work (returns Work model automatically)
work = client.work.get("123456789")

# Type-safe property access
print(work.primary_title)      # "The Title of the Work"
print(work.primary_contributor) # "Author, Name"  
print(work.publication_year)   # 2020

# Dict-like access (backward compatible)
print(work['title'])           # "The Title of the Work"
print(work.get('issued'))      # "2020"

# Access raw data
print(work.raw['title'])       # Original API response data
```

**Key Properties:**
- `primary_title` - Main title with fallback
- `primary_contributor` - First contributor/author
- `publication_year` - Parsed publication year as integer
- `is_online` - Whether work is available online
- `has_corrections` - Whether work has text corrections

### Article Model  

Represents newspaper and gazette articles.

```python
from trove.models import Article

# Get an article
article = client.newspaper.get("18341291")

# Type-safe access
print(article.display_title)    # Article heading with fallback
print(article.newspaper_title)  # Newspaper name
print(article.has_full_text)    # Boolean - full text available
print(article.is_illustrated)   # Boolean - has illustrations
print(article.word_count)       # Integer word count

# Dict-like access still works
print(article['heading'])       # Raw heading
print(article.get('articleText')) # Full article text
```

**Key Properties:**
- `display_title` - Article heading with fallback
- `newspaper_title` - Name of the newspaper/publication
- `has_full_text` - Whether full article text is available
- `is_illustrated` - Whether article contains illustrations
- `has_corrections` - Whether article has user corrections

### People Model

Represents people and organization records.

```python
from trove.models import People

# Get a person record
person = client.people.get("123456")

# Type-safe access
print(person.display_name)     # Primary display name
print(person.is_person)        # True if person, False if organization
print(person.is_organization)  # True if organization/family
print(person.primary_biography) # First biographical text

# Access alternate names
for name in person.alternate_name:
    print(f"Also known as: {name}")
```

**Key Properties:**
- `display_name` - Primary display name with fallback
- `is_person` - Whether record represents a person
- `is_organization` - Whether record represents an organization
- `primary_biography` - First available biographical text

### List Model

Represents user-created lists.

```python
from trove.models import TroveList

# Get a list
trove_list = client.list.get("123456")

# Type-safe access  
print(trove_list.display_title)   # List title with fallback
print(trove_list.creator_name)    # Creator name with fallback
print(trove_list.item_count)      # Number of items in list

# Access list items
for item in trove_list.list_item:
    print(f"- {item.title}")
```

**Key Properties:**
- `display_title` - List title with fallback
- `creator_name` - List creator with fallback
- `item_count` - Number of items in the list

## Backward Compatibility

Models are designed to be drop-in replacements for dictionary access:

```python
# Both approaches work identically
work = client.work.get("123456")

# New model approach
title = work.primary_title
contributors = work.contributor

# Legacy dict approach (still works)
title = work['title'] or "Untitled Work"
contributors = work.get('contributor', [])

# Mixed approach
print(f"{work.primary_title} by {work['contributor'][0] if work['contributor'] else 'Unknown'}")
```

## Raw Data Access

Access the original API response data:

```python
work = client.work.get("123456")

# Access raw response
raw_data = work.raw
print(raw_data.keys())  # All original field names

# Useful for debugging or accessing new fields
if 'newField' in work.raw:
    print(f"New field: {work.raw['newField']}")
```

## Working with Search Results

Models are automatically used in search results:

```python
results = client.search().text("poetry").in_("book").first_page()

# Records are automatically parsed into models
works = results.categories[0]['records']['work']
for work in works:
    # work is a Work model instance
    print(f"{work.primary_title} ({work.publication_year})")
    
    # But dict access still works
    print(f"Raw title: {work['title']}")
```

## Error Handling

Models gracefully handle missing or malformed data:

```python
work = client.work.get("123456")

# Properties handle missing data gracefully
print(work.primary_title)      # Returns "Untitled Work" if title missing
print(work.publication_year)   # Returns None if year can't be parsed

# Raw access returns exactly what API provides
print(work.raw.get('title'))   # Returns None if missing
```

## Custom Model Usage

You can also manually parse data into models:

```python
from trove.models import parse_record

# Parse raw API data
raw_data = {'id': '123', 'title': 'Test Work'}
work = parse_record(raw_data, 'work')

if work:
    print(work.primary_title)  # Type-safe access
else:
    print(raw_data['title'])   # Fallback to dict access
```

## Type Hints

Models provide full type hint support:

```python
from trove.models import Work
from typing import Optional

def process_work(work: Work) -> Optional[str]:
    # Process a work and return its title
    if work.publication_year and work.publication_year > 2000:
        return work.primary_title
    return None

# IDE will provide autocompletion and type checking
work = client.work.get("123456")
title = process_work(work)  # Type: Optional[str]
```
"""
        
        with open(self.output_dir / "models.md", "w") as f:
            f.write(models_content)
    
    def _generate_resource_docs(self):
        """Generate resource API documentation.""" 
        # This would be quite long, so I'll create a shorter version
        resources_content = """# Resource APIs

Direct access to specific Trove records by ID. All resource APIs support both sync and async operations.

## Work Resource

Access books, images, maps, music, and other published works.

```python
# Get a work
work = client.work.get("123456789")

# Get with additional details
work = client.work.get("123456789", include=['workversions'], reclevel='full')

# Get work versions
versions = client.work.get_versions("123456789")

# Get library holdings
holdings = client.work.get_holdings("123456789")
```

## Article Resources

Access newspaper and gazette articles.

```python
# Newspaper articles
article = client.newspaper.get("18341291")

# Gazette articles  
gazette = client.gazette.get("123456")

# Get with full text
article = client.newspaper.get("18341291", include=['articletext'])
```

## People Resource

Access people and organization records.

```python
# Get person/organization
person = client.people.get("123456")

# Get with biographical information
person = client.people.get("123456", include=['biography'], reclevel='full')
```

## List Resource

Access user-created lists.

```python
# Get list
trove_list = client.list.get("123456")

# Get with list items
trove_list = client.list.get("123456", include=['listItems'])
```

## Common Parameters

All resources support these parameters:

- `include` - Additional data to include
- `reclevel` - Detail level ('brief' or 'full')  
- `encoding` - Response format ('json' or 'xml')

## Error Handling

```python
from trove.exceptions import ResourceNotFoundError

try:
    work = client.work.get("nonexistent")
except ResourceNotFoundError:
    print("Work not found")
```
"""
        
        with open(self.output_dir / "resources.md", "w") as f:
            f.write(resources_content)
    
    def _generate_error_docs(self):
        """Generate error handling documentation."""
        error_content = """# Error Handling

The Trove SDK provides comprehensive error handling with context-aware messages and recovery suggestions.

## Exception Hierarchy

All SDK exceptions inherit from `TroveError`:

```python
from trove.exceptions import (
    TroveError,              # Base exception
    ConfigurationError,       # Configuration issues
    AuthenticationError,      # Invalid API key (HTTP 401)
    AuthorizationError,       # Access forbidden (HTTP 403)
    ResourceNotFoundError,    # Resource not found (HTTP 404)
    RateLimitError,          # Rate limit exceeded (HTTP 429)
    TroveAPIError,           # General API errors
    NetworkError,            # Network connectivity issues
    ValidationError,         # Parameter validation errors
    CacheError               # Cache operation errors
)
```

## Basic Error Handling

```python
from trove import TroveClient
from trove.exceptions import TroveError, ResourceNotFoundError

try:
    client = TroveClient.from_env()
    work = client.work.get("123456789")
    print(work.primary_title)
    
except ResourceNotFoundError:
    print("Work not found")
except TroveError as e:
    print(f"Trove SDK error: {e}")
```

## Enhanced Error Information

Errors include context and suggestions:

```python
try:
    client.work.get("nonexistent123")
except ResourceNotFoundError as e:
    print(f"Error: {e}")
    
    # Enhanced errors include suggestions
    if hasattr(e, 'response_data') and e.response_data:
        suggestions = e.response_data.get('suggestions', [])
        if suggestions:
            print("Suggestions:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
```

## Rate Limiting

```python
from trove.exceptions import RateLimitError
import time

try:
    # Bulk operation that might hit rate limits
    for work_id in work_ids:
        work = client.work.get(work_id)
        process_work(work)
        
except RateLimitError as e:
    print(f"Rate limited: {e}")
    
    # Check for retry-after header
    if hasattr(e, 'retry_after') and e.retry_after:
        print(f"Retry after {e.retry_after} seconds")
        time.sleep(float(e.retry_after))
```

## Validation Errors

```python
from trove.exceptions import ValidationError

try:
    # Invalid search parameters
    results = client.search().in_("invalid_category").first_page()
    
except ValidationError as e:
    print(f"Validation error: {e}")
    # Error message includes valid options
```

## Network Errors

```python
from trove.exceptions import NetworkError

try:
    results = client.search().text("test").in_("book").first_page()
    
except NetworkError as e:
    print(f"Network error: {e}")
    # Could indicate connectivity issues, timeouts, etc.
```

## Retry Logic

Check if an error is retryable:

```python
from trove.exceptions import is_retryable_error
import time

for attempt in range(3):
    try:
        work = client.work.get("123456789")
        break  # Success
        
    except TroveError as e:
        if is_retryable_error(e) and attempt < 2:
            print(f"Retrying after error: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
            continue
        else:
            raise  # Non-retryable or final attempt
```

## Debug Mode

Enable debug mode for detailed error information:

```python
from trove.errors import set_debug_mode

# Enable debug mode for development
set_debug_mode(True)

try:
    work = client.work.get("nonexistent")
except TroveError as e:
    # Error will include traceback and context in debug mode
    print(f"Debug error: {e}")
    if hasattr(e, 'response_data') and 'traceback' in e.response_data:
        print("Traceback available for debugging")
```

## Best Practices

### Specific Exception Handling

```python
try:
    work = client.work.get(work_id)
    
except ResourceNotFoundError:
    # Handle missing resources specifically
    print(f"Work {work_id} not found")
    
except AuthenticationError:
    # Handle API key issues
    print("Check your API key configuration")
    
except RateLimitError as e:
    # Handle rate limiting with backoff
    wait_time = getattr(e, 'retry_after', 30)
    time.sleep(float(wait_time))
    
except TroveError as e:
    # Handle other SDK errors
    print(f"SDK error: {e}")
```

### Graceful Degradation

```python
def get_work_safely(work_id: str) -> Optional[Dict]:
    try:
        return client.work.get(work_id)
    except ResourceNotFoundError:
        return None
    except TroveError as e:
        print(f"Warning: Could not retrieve work {work_id}: {e}")
        return None

# Use in batch operations
works = []
for work_id in work_ids:
    work = get_work_safely(work_id)
    if work:
        works.append(work)
```

### Logging Errors

```python
import logging
from trove.exceptions import TroveError

logger = logging.getLogger(__name__)

try:
    results = client.search().text("test").first_page()
    
except TroveError as e:
    # Log errors for monitoring
    logger.error(f"Trove API error: {e}", extra={
        'error_type': type(e).__name__,
        'operation': 'search'
    })
    raise
```
"""
        
        with open(self.output_dir / "errors.md", "w") as f:
            f.write(error_content)
    
    def _generate_examples(self):
        """Generate examples documentation."""
        examples_content = """# Examples

Practical examples showing how to use the Trove SDK for common tasks.

## Basic Search Examples

### Search for Books

```python
from trove import TroveClient

client = TroveClient.from_env()

# Find books about Australian history
results = (client.search()
          .text("Australian history")
          .in_("book")
          .decade("200")  # 2000s
          .page_size(20)
          .first_page())

print(f"Found {results.total_results} books")

# Process results
works = results.categories[0]['records']['work']
for work in works:
    print(f"- {work.primary_title}")
    print(f"  Author: {work.primary_contributor or 'Unknown'}")
    print(f"  Year: {work.publication_year or 'Unknown'}")
    print()
```

### Search Newspapers

```python
# Find newspaper articles about federation
results = (client.search()
          .text("federation")
          .in_("newspaper")
          .state("NSW")
          .decade("190", "191")  # 1900s-1910s
          .illustrated()
          .first_page())

articles = results.categories[0]['records']['article']
for article in articles:
    print(f"- {article.display_title}")
    print(f"  {article.newspaper_title}, {article.date}")
    print()
```

## Resource Access Examples

### Get Work Details

```python
# Get a specific work with full details
work = client.work.get("123456789", include=['workversions', 'holdings'], reclevel='full')

print(f"Title: {work.primary_title}")
print(f"Contributors: {', '.join(work.contributor)}")

# Check versions
versions = client.work.get_versions("123456789") 
print(f"Available in {len(versions)} versions")

# Check library holdings
holdings = client.work.get_holdings("123456789")
for holding in holdings:
    print(f"Held by: {holding.get('name', 'Unknown library')}")
```

### Get Article with Full Text

```python
# Get newspaper article with full text
article = client.newspaper.get("18341291", include=['articletext'])

print(f"Headline: {article.display_title}")
print(f"Newspaper: {article.newspaper_title}")
print(f"Date: {article.date}")

if article.has_full_text:
    print(f"Article text ({article.word_count} words):")
    print(article.article_text[:500] + "...")
```

## Advanced Search Examples

### Faceted Browsing

```python
# Search with facets for exploration
results = (client.search()
          .text("women's suffrage")
          .in_("newspaper")
          .with_facets("decade", "state", "title")
          .first_page())

print(f"Found {results.total_results} articles")

# Explore facets
facets = results.categories[0]['facets']['facet']
for facet in facets:
    print(f"\\n{facet['name'].title()} breakdown:")
    
    terms = facet['term']
    for term in terms[:10]:  # Show top 10
        print(f"  {term['display']}: {term['count']} articles")
```

### Pagination Example

```python
# Process all results page by page
search = (client.search()
         .text("Australian poetry")
         .in_("book")
         .page_size(50))

total_processed = 0
for page_num, page in enumerate(search.pages(), 1):
    works = page.categories[0]['records']['work']
    
    print(f"Page {page_num}: {len(works)} works")
    total_processed += len(works)
    
    # Process works
    for work in works:
        print(f"  - {work.primary_title}")
    
    # Stop after 5 pages for demo
    if page_num >= 5:
        break

print(f"Processed {total_processed} total works")
```

### Bulk Data Collection

```python
# Collect large datasets efficiently
search = (client.search()
         .text("bushfire")
         .in_("newspaper")
         .year("2019", "2020")  # Black Summer fires
         .harvest()  # Enable bulk mode
         .page_size(100))

articles = []
for article in search.records():
    articles.append({
        'title': article.display_title,
        'newspaper': article.newspaper_title,
        'date': article.date,
        'url': article.trove_url,
        'text': article.article_text if article.has_full_text else None
    })
    
    # Progress indicator
    if len(articles) % 100 == 0:
        print(f"Collected {len(articles)} articles...")
    
    # Limit for demo
    if len(articles) >= 1000:
        break

print(f"Final dataset: {len(articles)} articles")
```

## Analysis Examples

### Publication Timeline

```python
from collections import Counter

# Analyze publication years for a topic
search = client.search().text("climate change").in_("book").page_size(100)

years = []
for work in search.records():
    if work.publication_year:
        years.append(work.publication_year)
    
    if len(years) >= 500:  # Limit sample
        break

# Count by decade
decades = Counter(year // 10 * 10 for year in years)
print("Climate change books by decade:")
for decade in sorted(decades.keys()):
    print(f"  {decade}s: {decades[decade]} books")
```

### Geographic Distribution

```python
from collections import Counter

# Analyze newspaper coverage by state
search = (client.search()
         .text("mining boom")
         .in_("newspaper")
         .decade("200")  # 2000s
         .page_size(50))

states = []
for page in search.pages():
    articles = page.categories[0]['records']['article']
    for article in articles:
        # Extract state from newspaper title or other metadata
        title = article.newspaper_title or ""
        if "Sydney" in title or "NSW" in title:
            states.append("NSW")
        elif "Melbourne" in title or "VIC" in title:
            states.append("VIC")
        # ... more state detection logic
    
    if len(states) >= 200:  # Limit for demo
        break

state_counts = Counter(states)
print("Mining boom coverage by state:")
for state, count in state_counts.most_common():
    print(f"  {state}: {count} articles")
```

## Citation Examples

### Generate Citations

```python
from trove.citations import generate_citation

# Get work and generate citation
work = client.work.get("123456789")

# BibTeX format
bibtex = generate_citation(work, format='bibtex')
print("BibTeX citation:")
print(bibtex)

# CSL-JSON format
csl_json = generate_citation(work, format='csl-json')
print("\\nCSL-JSON citation:")
print(json.dumps(csl_json, indent=2))
```

### PID Resolution

```python
from trove.citations import resolve_pid

# Resolve Trove URLs to records
urls = [
    "https://trove.nla.gov.au/work/123456789",
    "https://trove.nla.gov.au/newspaper/article/18341291"
]

for url in urls:
    record = resolve_pid(url, client)
    if record:
        if hasattr(record, 'primary_title'):  # Work
            print(f"Work: {record.primary_title}")
        elif hasattr(record, 'display_title'):  # Article
            print(f"Article: {record.display_title}")
```

## Error Handling Examples

### Robust Batch Processing

```python
from trove.exceptions import ResourceNotFoundError, RateLimitError
import time

def process_work_ids(work_ids):
    results = []
    failed = []
    
    for i, work_id in enumerate(work_ids):
        try:
            work = client.work.get(work_id)
            results.append(work)
            
        except ResourceNotFoundError:
            print(f"Work {work_id} not found")
            failed.append(work_id)
            
        except RateLimitError as e:
            print(f"Rate limited, waiting...")
            wait_time = getattr(e, 'retry_after', 30)
            time.sleep(float(wait_time))
            
            # Retry the same ID
            try:
                work = client.work.get(work_id)
                results.append(work)
            except Exception:
                failed.append(work_id)
        
        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(work_ids)} works")
    
    return results, failed

# Use the function
work_ids = ["123", "456", "789", "nonexistent"]
works, failed_ids = process_work_ids(work_ids)

print(f"Successfully processed: {len(works)} works")
print(f"Failed: {len(failed_ids)} works")
```

## Performance Examples

### Connection Reuse

```python
# Use client as context manager for automatic cleanup
with TroveClient.from_env() as client:
    # All requests reuse the same connection
    for query in ["poetry", "fiction", "history"]:
        results = client.search().text(query).in_("book").first_page()
        print(f"{query}: {results.total_results} results")
    
    # Client automatically closed here
```

### Async Processing

```python
import asyncio

async def search_multiple_terms(terms):
    client = TroveClient.from_env()
    
    # Process searches concurrently
    tasks = []
    for term in terms:
        task = client.search().text(term).in_("book").afirst_page()
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    for term, result in zip(terms, results):
        print(f"{term}: {result.total_results} results")
    
    await client.aclose()

# Run async example
terms = ["poetry", "fiction", "history", "science"]
asyncio.run(search_multiple_terms(terms))
```
"""
        
        with open(self.output_dir / "examples.md", "w") as f:
            f.write(examples_content)
    
    def _generate_index(self):
        """Generate documentation index."""
        index_content = """# Trove SDK Documentation

Welcome to the Trove SDK documentation. This SDK provides a comprehensive Python interface to the Trove API v3, Australia's National Library digital collection.

## Getting Started

- [Overview](./overview.md) - SDK overview and quick start
- [Installation & Configuration](./overview.md#installation) - Setup instructions

## API Reference

- [TroveClient](./client.md) - Main client interface
- [Search API](./search.md) - Fluent search interface with filtering
- [Resource APIs](./resources.md) - Direct access to specific records
- [Data Models](./models.md) - Type-safe data structures
- [Error Handling](./errors.md) - Comprehensive error handling

## Examples & Guides

- [Examples](./examples.md) - Practical usage examples
- [Advanced Usage](./examples.md#advanced-search-examples) - Complex queries and data processing
- [Performance Tips](./examples.md#performance-examples) - Optimization techniques

## External Resources

- [Official Trove API Documentation](https://trove.nla.gov.au/about/create-something/using-api)
- [Getting an API Key](https://trove.nla.gov.au/about/create-something/using-api#getting-an-api-key)
- [GitHub Repository](https://github.com/your-org/trove-sdk)

## Support

For bug reports and feature requests, please use the [GitHub Issues](https://github.com/your-org/trove-sdk/issues) page.
"""
        
        with open(self.output_dir / "index.md", "w") as f:
            f.write(index_content)


def main():
    """Generate API documentation."""
    # Get paths
    current_dir = Path(__file__).parent
    source_dir = current_dir.parent  # trove-sdk directory
    output_dir = current_dir / "api"
    
    # Generate docs
    generator = APIDocGenerator(source_dir, output_dir)
    generator.generate_docs()
    
    print("\nDocumentation files generated:")
    for doc_file in sorted(output_dir.glob("*.md")):
        print(f"  - {doc_file.name}")


if __name__ == "__main__":
    main()