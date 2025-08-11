# Trove Resource Access Guide

This guide covers how to access individual Trove records using the Stage 3 resource endpoints: works, articles, people, lists, and titles.

## Table of Contents

- [Overview](#overview)
- [Resource Factory](#resource-factory)
- [Work Resources](#work-resources)
- [Article Resources](#article-resources)
- [People Resources](#people-resources)
- [List Resources](#list-resources)
- [Title Resources](#title-resources)
- [Common Parameters](#common-parameters)
- [Error Handling](#error-handling)
- [Async Operations](#async-operations)
- [Best Practices](#best-practices)

## Overview

The Trove SDK provides dedicated resource classes for accessing individual records through the Trove API v3. These resources complement the search functionality by allowing direct access to specific items using their unique identifiers.

### Supported Resource Types

- **Work Resources** (`/v3/work/{id}`) - Books, images, maps, music, sound, video, archives, journal articles
- **Article Resources** (`/v3/newspaper/{id}`, `/v3/gazette/{id}`) - Newspaper and gazette articles  
- **People Resources** (`/v3/people/{id}`) - People and organization records
- **List Resources** (`/v3/list/{id}`) - User-created lists
- **Title Resources** (`/v3/{type}/title/{id}`) - Newspaper, magazine, and gazette titles

## Resource Factory

The `ResourceFactory` provides a centralized way to create and manage resource instances:

```python
from trove.config import TroveConfig
from trove.transport import TroveTransport
from trove.cache import MemoryCache
from trove.resources import ResourceFactory

# Set up configuration
config = TroveConfig.from_env()
cache = MemoryCache()
transport = TroveTransport(config, cache)

# Create resource factory
factory = ResourceFactory(transport)

# Get resource instances
work_resource = factory.get_work_resource()
newspaper_resource = factory.get_newspaper_resource()
people_resource = factory.get_people_resource()
```

The factory caches resource instances, so calling the same method multiple times returns the same object.

## Work Resources

Work resources provide access to books, images, maps, music, and other creative works.

### Basic Usage

```python
work_resource = factory.get_work_resource()

# Get a work by ID
work = work_resource.get("123456")
print(f"Title: {work['title']}")
print(f"Contributor: {work.get('contributor', [])}")
```

### Include Parameters

Works support several include parameters to get additional information:

```python
# Get work with tags and comments
work = work_resource.get("123456", include=['tags', 'comments'])

# Get full work details
work = work_resource.get("123456", include=['all'], reclevel='full')

# Get work with library holdings
work = work_resource.get("123456", include=['holdings'])
```

**Valid include options for works:**
- `all` - Include all available fields
- `comments` - Public comments on the work
- `holdings` - Library holdings information
- `links` - Related links
- `lists` - Public lists containing this work
- `subscribinglibs` - Subscribing libraries
- `tags` - Public tags on the work
- `workversions` - Different versions/editions

### Convenience Methods

Work resources provide helper methods for common operations:

```python
# Get all versions of a work
versions = work_resource.get_versions("123456")
for version in versions:
    print(f"Version: {version.get('title')}")

# Get library holdings
holdings = work_resource.get_holdings("123456")
for holding in holdings:
    print(f"Library: {holding.get('nuc')}")

# Get public tags
tags = work_resource.get_tags("123456")
for tag in tags:
    print(f"Tag: {tag.get('value')}")

# Get public comments
comments = work_resource.get_comments("123456")
for comment in comments:
    print(f"Comment: {comment.get('text')}")
```

## Article Resources

Article resources provide access to newspaper and gazette articles.

### Basic Usage

```python
# Newspaper articles
newspaper_resource = factory.get_newspaper_resource()
article = newspaper_resource.get("18341291")

# Gazette articles  
gazette_resource = factory.get_gazette_resource()
gazette = gazette_resource.get("12345")
```

### Include Parameters

Articles support these include parameters:

```python
# Get article with full text
article = newspaper_resource.get("18341291", include=['articletext'])

# Get article with all additional data
article = newspaper_resource.get("18341291", include=['all'])
```

**Valid include options for articles:**
- `all` - Include all available fields
- `articletext` - Full text of the article
- `comments` - Public comments
- `lists` - Public lists containing this article
- `tags` - Public tags

### Convenience Methods

```python
# Get full article text
full_text = newspaper_resource.get_full_text("18341291")
if full_text:
    print(f"Article length: {len(full_text)} characters")

# Get PDF URLs for the article pages
pdf_urls = newspaper_resource.get_pdf_urls("18341291")
for url in pdf_urls:
    print(f"PDF: {url}")

# Check article status
if newspaper_resource.is_coming_soon("18341291"):
    print("Article is coming soon")
elif newspaper_resource.is_withdrawn("18341291"):
    print("Article has been withdrawn")
else:
    print("Article is available")

# Get tags and comments
tags = newspaper_resource.get_tags("18341291")
comments = newspaper_resource.get_comments("18341291")
```

## People Resources

People resources provide access to people and organization records.

### Basic Usage

```python
people_resource = factory.get_people_resource()
person = people_resource.get("1234")
```

### Include Parameters

**Valid include options for people:**
- `all` - Include all available fields
- `comments` - Public comments
- `lists` - Public lists containing this person/organization
- `raweaccpf` - Raw EAC-CPF XML record
- `tags` - Public tags

```python
# Get person with biography information
person = people_resource.get("1234", reclevel='full')

# Get raw EAC-CPF XML
eac_cpf = people_resource.get_raw_eac_cpf("1234")
```

### Convenience Methods

```python
# Check entity type
if people_resource.is_person("1234"):
    print("This is a person record")
    occupations = people_resource.get_occupations("1234")
    print(f"Occupations: {', '.join(occupations)}")
elif people_resource.is_organization("1234"):
    print("This is an organization record")

# Get names
primary_name = people_resource.get_primary_name("1234")
alternate_names = people_resource.get_alternate_names("1234")

print(f"Primary name: {primary_name}")
if alternate_names:
    print(f"Also known as: {', '.join(alternate_names)}")

# Get biographical information
biographies = people_resource.get_biographies("1234")
for bio in biographies:
    print(f"Biography from {bio.get('contributor')}")
```

## List Resources

List resources provide access to user-created lists.

### Basic Usage

```python
list_resource = factory.get_list_resource()
list_data = list_resource.get("21922")
```

### Include Parameters

**Valid include options for lists:**
- `all` - Include all available fields
- `comments` - Public comments on the list
- `listitems` - Items in the list
- `tags` - Public tags on the list

```python
# Get list with all items
list_data = list_resource.get("21922", include=['listitems'])
```

### Convenience Methods

```python
# Get list metadata
title = list_resource.get_title("21922")
creator = list_resource.get_creator("21922")
item_count = list_resource.get_item_count("21922")
description = list_resource.get_description("21922")
last_updated = list_resource.get_last_updated("21922")

print(f"List: {title}")
print(f"Created by: {creator}")
print(f"Contains {item_count} items")
print(f"Description: {description}")
print(f"Last updated: {last_updated}")

# Get list items
items = list_resource.get_items("21922")
for item in items:
    if 'work' in item:
        print(f"Work: {item['work'].get('title')}")
    elif 'article' in item:
        print(f"Article: {item['article'].get('heading')}")
```

## Title Resources

Title resources provide access to newspaper, magazine, and gazette title information.

### Basic Usage

```python
# Newspaper titles
newspaper_titles = factory.get_newspaper_title_resource()
title = newspaper_titles.get("11")  # Sydney Morning Herald

# Magazine titles  
magazine_titles = factory.get_magazine_title_resource()

# Gazette titles
gazette_titles = factory.get_gazette_title_resource()
```

### Searching Titles

```python
# Search newspaper titles by state
results = newspaper_titles.search(state='nsw', limit=10)

# Search with geographic filters
results = newspaper_titles.search(
    state='vic',
    place=['Melbourne', 'Ballarat'],
    limit=20
)

# Search gazette titles (more limited state options)
gazette_results = gazette_titles.search(state='nsw', limit=5)
```

**Valid states:**
- **Newspapers**: `nsw`, `act`, `qld`, `tas`, `sa`, `nt`, `wa`, `vic`, `national`, `international`
- **Gazettes**: `nsw`, `national`, `international`

### Getting Publication Years

```python
# Get years when a title was published
years = newspaper_titles.get_publication_years("11")
for year_info in years:
    print(f"Year: {year_info.get('value')}, Issues: {year_info.get('count')}")

# Get years within a specific date range
years = newspaper_titles.get_publication_years(
    "11", 
    date_range="20100101-20201231"
)
```

## Common Parameters

### Record Level (reclevel)

Controls the amount of detail returned:

```python
# Brief record (default)
record = resource.get("123", reclevel='brief')

# Full record with all available fields
record = resource.get("123", reclevel='full')

# Using enum
from trove.resources import RecLevel
record = resource.get("123", reclevel=RecLevel.FULL)
```

### Encoding

Controls the response format:

```python
# JSON format (default)
record = resource.get("123", encoding='json')

# XML format
record = resource.get("123", encoding='xml')

# Using enum
from trove.resources import Encoding
record = resource.get("123", encoding=Encoding.JSON)
```

## Error Handling

Resources provide structured error handling:

```python
from trove.exceptions import ResourceNotFoundError, ValidationError

try:
    work = work_resource.get("999999999")
except ResourceNotFoundError:
    print("Work not found")

try:
    work = work_resource.get("123", include=['invalid'])
except ValidationError as e:
    print(f"Invalid parameters: {e}")
```

### Common Errors

- **ResourceNotFoundError** - Resource doesn't exist (HTTP 404)
- **ValidationError** - Invalid parameters
- **AuthenticationError** - Invalid API key (HTTP 401)
- **RateLimitError** - Rate limit exceeded (HTTP 429)
- **TroveAPIError** - General API errors

## Async Operations

All resource methods have async equivalents:

```python
import asyncio

async def fetch_resources():
    # Async resource access
    work = await work_resource.aget("123456")
    
    # Async convenience methods
    versions = await work_resource.aget_versions("123456")
    holdings = await work_resource.aget_holdings("123456")
    
    # Articles
    article = await newspaper_resource.aget("18341291")
    full_text = await newspaper_resource.aget_full_text("18341291")
    
    # People
    person = await people_resource.aget("1234")
    is_person = await people_resource.ais_person("1234")
    
    # Lists
    list_data = await list_resource.aget("21922")
    items = await list_resource.aget_items("21922")

# Run async operations
asyncio.run(fetch_resources())
```

## Best Practices

### 1. Use the Resource Factory

Always use the `ResourceFactory` to create resource instances:

```python
# Good
factory = ResourceFactory(transport)
work_resource = factory.get_work_resource()

# Avoid creating resources directly
work_resource = WorkResource(transport)  # Works but not recommended
```

### 2. Request Only What You Need

Use appropriate `reclevel` and `include` parameters:

```python
# Good - only get what you need
work = work_resource.get("123", reclevel='brief')

# Avoid - unnecessary data transfer
work = work_resource.get("123", include=['all'], reclevel='full')
```

### 3. Handle Errors Gracefully

Always handle potential errors:

```python
try:
    work = work_resource.get(work_id)
    process_work(work)
except ResourceNotFoundError:
    logger.warning(f"Work {work_id} not found")
    return None
except RateLimitError as e:
    logger.warning(f"Rate limited: {e.retry_after}")
    return None
```

### 4. Use Convenience Methods

Leverage convenience methods for common operations:

```python
# Good - use convenience method
versions = work_resource.get_versions("123")

# Verbose - manual extraction
work = work_resource.get("123", include=['workversions'], reclevel='full')
versions = work.get('version', [])
if isinstance(versions, dict):
    versions = [versions]
```

### 5. Batch Operations with Async

Use async operations for better performance when fetching multiple resources:

```python
async def fetch_multiple_works(work_ids):
    tasks = [work_resource.aget(work_id) for work_id in work_ids]
    return await asyncio.gather(*tasks, return_exceptions=True)

# Filter out errors
results = [r for r in results if not isinstance(r, Exception)]
```

### 6. Cache Resource Instances

The `ResourceFactory` automatically caches instances, but you can store references:

```python
class TroveClient:
    def __init__(self, config):
        self.transport = TroveTransport(config, cache)
        self.factory = ResourceFactory(self.transport)
        
        # Cache frequently used resources
        self.works = self.factory.get_work_resource()
        self.newspapers = self.factory.get_newspaper_resource()
        self.people = self.factory.get_people_resource()
```

This guide covers the core functionality of Trove resource access. For more advanced usage patterns, see the example files in the `examples/` directory.