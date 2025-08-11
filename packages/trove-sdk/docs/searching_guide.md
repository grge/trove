# Comprehensive Trove Search Guide

This guide covers all the search functionality implemented in Stage 2 of the Trove SDK, including complete parameter support, pagination, and caching strategies.

## Table of Contents

- [Quick Start](#quick-start)
- [Search Parameters](#search-parameters)
- [Parameter Construction](#parameter-construction-with-build_limits)
- [Pagination](#pagination)
- [Multi-Category Searches](#multi-category-searches)
- [Caching and Performance](#caching-and-performance)
- [Async Operations](#async-operations)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Quick Start

```python
from trove import TroveConfig, TroveTransport, SearchResource, create_cache

# Setup
config = TroveConfig.from_env()  # Reads TROVE_API_KEY from environment
cache = create_cache("memory")
transport = TroveTransport(config, cache)
search = SearchResource(transport)

# Simple search
result = search.page(
    category=['book'],
    q='Australian history',
    n=10
)

print(f"Found {result.total_results} books")
for work in result.categories[0]['records']['work']:
    print(f"- {work['title']}")

transport.close()
```

## Search Parameters

The Trove SDK supports all 60+ search parameters from the Trove API v3. Parameters fall into several categories:

### Core Parameters

```python
result = search.page(
    category=['book', 'image'],        # Required: categories to search
    q='Australian literature',         # Query text
    n=20,                             # Results per page (1-100)
    sortby='datedesc',                # Sort order: relevance, datedesc, dateasc
    bulkHarvest=True,                 # Optimize for harvesting
    reclevel='full',                  # Record detail: brief, full
    encoding='json'                   # Response format: json, xml
)
```

### Date and Time Filters

```python
# Date filtering with dependencies
result = search.page(
    category=['newspaper'],
    q='federation',
    l_decade=['190'],                 # 1900s (required for newspapers)
    l_year=['1901'],                  # Specific year (requires decade for newspapers)
    l_month=['01']                    # Specific month (requires year)
)
```

### Geographic Filters

```python
result = search.page(
    category=['newspaper'],
    q='local news',
    l_state=['NSW', 'VIC'],           # State filters
    l_geocoverage=['Australia']       # Geographic coverage
)

# People location filters
result = search.page(
    category=['people'],
    q='Australian authors',
    l_place=['Sydney', 'Melbourne']   # Birth/establishment place
)
```

### Language and Cultural Filters

```python
result = search.page(
    category=['book'],
    q='Indigenous stories',
    l_language=['English'],           # Content language
    l_austlanguage=['Yolngu Matha'],  # Aboriginal languages
    l_firstAustralians='y',           # First Australians content
    l_culturalSensitivity='y',        # Culturally sensitive content
    l_australian='y'                  # Australian content
)
```

### Content Type Filters

```python
result = search.page(
    category=['book'],
    q='maps',
    l_format=['Map', 'Book'],         # Format filters
    l_availability=['y/f'],           # Free online content
    l_audience=['Academic']           # Target audience
)

# Article-specific filters
result = search.page(
    category=['newspaper'],
    q='advertisements',
    l_artType=['newspaper'],          # newspaper vs gazette
    l_category=['Advertising'],       # Article category
    l_illustrated=True,               # Illustrated articles only
    l_wordCount=['1000+ Words']       # Long articles
)
```

### People-Specific Filters

```python
result = search.page(
    category=['people'],
    q='authors',
    l_occupation=['Author', 'Writer'],
    l_birth=['1850'],                 # Birth year
    l_death=['1920']                  # Death year
)
```

### Faceting and Optional Fields

```python
result = search.page(
    category=['book'],
    q='Australian literature',
    facet=['decade', 'format', 'language'],  # Request facets
    include=['tags', 'comments', 'holdings'] # Optional fields
)

# Access facets
if 'facets' in result.categories[0]:
    for facet in result.categories[0]['facets']['facet']:
        print(f"{facet['name']}: {len(facet['term'])} values")
```

## Parameter Construction with build_limits

For complex searches, use the `build_limits` utility function to construct limit parameters:

```python
from trove import build_limits, SearchParameters

# Build API-ready limit parameters
limits = build_limits(
    decade=['200'],                      # 2000s
    australian='y',                      # Australian content only
    availability=['y/f'],                # Free online
    format=['Book'],                     # Books only
    language=['English']                 # English language
)

# Use with raw API calls
result = search.page(
    category=['book'],
    q='Australian poetry',
    n=50,
    reclevel='full',
    facet=['decade', 'format'],
    include=['tags', 'workversions'],
    **limits  # Spreads API parameters like l-decade, l-australian, etc.
)

# Or create SearchParameters object directly
params = SearchParameters(
    category=['book'],
    q='Australian poetry',
    n=50,                               # Page size
    reclevel='full',                    # Full records
    facet=['decade', 'format'],         # Facets
    include=['tags', 'workversions'],   # Optional fields
    l_decade=['200'],                   # Direct assignment
    l_australian='y',
    l_availability=['y/f'],
    l_format=['Book'],
    l_language=['English']
)

result = search.page(params=params)
```

### Direct SearchParameters Construction

You can also construct SearchParameters directly for maximum control:

```python
from trove import SearchParameters

# Direct construction
params = SearchParameters(
    category=['book', 'image'],          # Multiple categories
    q='Sydney Harbour',                  # Search query
    n=25,                               # Results per page
    sortby='datedesc',                  # Sort order
    bulkHarvest=True,                   # Enable bulk mode
    reclevel='full',                    # Full metadata
    
    # Date filters
    l_decade=['190', '200'],            # Multiple decades
    l_year=['1901'],                    # Specific year
    l_month=['01'],                     # Specific month
    
    # Geographic filters
    l_state=['NSW', 'VIC'],             # Multiple states
    l_place=['Sydney', 'Melbourne'],    # Cities
    l_geographic=['Australia'],         # Coverage
    
    # Content filters
    l_format=['Book', 'Map'],           # Multiple formats
    l_artType=['newspaper'],            # Article type
    l_language=['English', 'French'],   # Languages
    l_availability=['y', 'y/f'],        # Online + free
    l_australian='y',                   # Australian flag
    l_illustrated=True,                 # Illustrated only
    l_wordCount=['1000+ Words'],        # Long articles
    
    # Advanced parameters
    facet=['decade', 'format', 'language'],
    include=['tags', 'comments', 'holdings']
)

result = search.page(params=params)
```
## Pagination

The SDK provides powerful pagination support with different strategies for different use cases.

### Single-Category Pagination

For single-category searches, use the convenient iteration methods:

```python
# Page-by-page iteration
for page in search.iter_pages(category=['book'], q='history', n=20):
    works = page.categories[0]['records']['work']
    print(f"Page with {len(works)} books")
    
    # Can break early
    if some_condition:
        break

# Individual record iteration
total_processed = 0
for record in search.iter_records(category=['book'], q='poetry', n=50):
    print(f"Processing: {record['title']}")
    total_processed += 1
    
    # Process records as they come
    if total_processed >= 1000:
        break
```

### Multi-Category Pagination

Multi-category searches require special handling due to independent pagination cursors:

```python
# Multi-category pagination (handles complexity automatically)
for category_code, page in search.iter_pages_by_category(
    category=['book', 'image'],
    q='Sydney',
    n=10
):
    total_results = page.total_results
    records = page.categories[0]['records']
    
    print(f"{category_code}: {total_results} total results")
    
    # Extract records based on category
    if category_code == 'book':
        works = records.get('work', [])
        for work in works:
            print(f"  Book: {work['title']}")
    elif category_code == 'image':
        works = records.get('work', [])  # Images also use 'work'
        for work in works:
            print(f"  Image: {work['title']}")
```

### Manual Pagination

For fine-grained control, use manual cursor pagination:

```python
params = SearchParameters(category=['book'], q='literature', n=20)
cursor = '*'  # Start cursor

while cursor:
    params.s = cursor
    result = search.page(params=params)
    
    # Process page
    works = result.categories[0]['records']['work']
    print(f"Processing {len(works)} works")
    
    # Get next cursor
    cursor = result.cursors.get('book')  # None if no more pages
```

### Pagination Limitations

**Important**: Due to Trove API architecture, some pagination operations have limitations:

- `iter_pages()` and `iter_records()` only support **single-category** searches
- Multi-category searches must use `iter_pages_by_category()`
- Each category in multi-category searches has independent pagination cursors
- Cursors are opaque and cannot be constructed manually

```python
# ✅ Supported - single category
for page in search.iter_pages(category=['book'], q='test'):
    pass

# ❌ Not supported - multiple categories  
try:
    for page in search.iter_pages(category=['book', 'image'], q='test'):
        pass
except ValidationError as e:
    print("Use iter_pages_by_category() for multiple categories")

# ✅ Supported - multi-category with special method
for category, page in search.iter_pages_by_category(
    category=['book', 'image'], q='test'
):
    pass
```

## Multi-Category Searches

Multi-category searches return results from multiple Trove categories in a single request:

```python
# Single request searches books, images, and newspapers
result = search.page(
    category=['book', 'image', 'newspaper'],
    q='Sydney Harbour Bridge',
    n=10  # 10 results per category
)

print(f"Total results: {result.total_results}")

# Each category has independent results
for category in result.categories:
    cat_name = category['name']
    cat_total = category['records']['total']
    print(f"{cat_name}: {cat_total} total results")
    
    # Different categories use different record containers
    if category['code'] == 'book':
        records = category['records'].get('work', [])
    elif category['code'] == 'newspaper':
        records = category['records'].get('article', [])
    elif category['code'] == 'people':
        records = category['records'].get('people', [])
    else:
        records = category['records'].get('work', [])  # Default for most
```

### Category-Specific Parameters

Some parameters only apply to specific categories:

```python
# Newspaper-specific parameters
newspaper_result = search.page(
    category=['newspaper'],
    q='federation',
    l_decade=['190'],        # Newspapers require decade for year
    l_year=['1901'],
    l_state=['NSW'],         # Newspaper state
    l_artType=['newspaper'], # newspaper vs gazette
    l_illustrated=True       # Illustrated articles
)

# Book-specific parameters  
book_result = search.page(
    category=['book'],
    q='literature',
    l_availability=['y/f'],  # Online availability
    l_format=['Book'],       # Format type
    l_audience=['Academic']  # Target audience
)

# People-specific parameters
people_result = search.page(
    category=['people'],
    q='authors',
    l_occupation=['Author'], # Person occupation
    l_birth=['1850'],        # Birth year
    l_place=['Sydney']       # Birth place
)
```

## Caching and Performance

The SDK includes sophisticated caching with search-specific optimizations.

### Basic Caching

```python
# Simple memory cache
cache = create_cache("memory")

# Persistent SQLite cache
cache = create_cache("sqlite", db_path="trove_cache.db")

# Enhanced cache with statistics and smart TTL
cache = create_cache("memory", enhanced=True)
```

### Enhanced Caching Features

The enhanced cache provides intelligent TTL management and statistics:

```python
from trove import TroveTransport, SearchResource, create_cache

# Setup enhanced cache
config = TroveConfig.from_env()
cache = create_cache("memory", enhanced=True)
transport = TroveTransport(config, cache)
search = SearchResource(transport)

# First search (cache miss)
result1 = search.page(category=['book'], q='test', n=10)

# Second identical search (cache hit - much faster)
result2 = search.page(category=['book'], q='test', n=10)

# Check cache statistics
if hasattr(cache, 'get_stats'):
    stats = cache.get_stats()
    print(f"Hit rate: {stats['hit_rate']:.2%}")
    print(f"Time saved: {stats['cache_savings_seconds']:.1f}s")
    print(f"Total requests: {stats['total_requests']}")
```

### Smart TTL Management

The enhanced cache automatically adjusts TTL based on search characteristics:

```python
# Small result sets get shorter TTL (5 minutes)
small_result = search.page(
    category=['book'],
    q='very specific unique query',  # Likely few results
    n=10
)

# Historical searches get longer TTL (2 hours)
historical_result = search.page(
    category=['book'],
    l_decade=['180'],  # 1800s data is stable
    q='history'
)

# Bulk harvest gets longest TTL (1 hour)
bulk_result = search.page(
    category=['book'],
    bulkHarvest=True,  # Optimized for stability
    l_australian='y'
)

# Dynamic content gets shortest TTL (5 minutes)
dynamic_result = search.page(
    category=['book'],
    q='recently added'  # May change frequently
)
```

### Cache Configuration

```python
# Configure route-specific TTL
if hasattr(cache, 'set_route_ttl'):
    cache.set_route_ttl('/result', 1800)    # 30 minutes for searches
    cache.set_route_ttl('/work', 7200)      # 2 hours for individual works
    cache.set_route_ttl('/people', 86400)   # 24 hours for people records

# Reset statistics
if hasattr(cache, 'reset_stats'):
    cache.reset_stats()
```

### Performance Best Practices

1. **Use appropriate cache backends**:
   ```python
   # Development: fast memory cache
   cache = create_cache("memory")
   
   # Production: persistent cache
   cache = create_cache("sqlite", db_path="/path/to/cache.db")
   
   # Research applications: enhanced cache with statistics
   cache = create_cache("memory", enhanced=True)
   ```

2. **Optimize search parameters**:
   ```python
   # ✅ Good: specific categories only
   result = search.page(category=['book'], q='test')
   
   # ❌ Slower: searching all categories
   result = search.page(category=['all'], q='test')
   ```

3. **Use appropriate record levels**:
   ```python
   # ✅ Fast: brief records for browsing
   result = search.page(category=['book'], q='test', reclevel='brief')
   
   # ❌ Slower: full records only when needed
   result = search.page(category=['book'], q='test', reclevel='full')
   ```

4. **Batch operations efficiently**:
   ```python
   # ✅ Good: larger page sizes reduce requests
   for page in search.iter_pages(category=['book'], q='test', n=100):
       pass
   
   # ❌ Inefficient: tiny pages = many requests  
   for page in search.iter_pages(category=['book'], q='test', n=5):
       pass
   ```

## Async Operations

All search operations support async variants for concurrent processing:

```python
import asyncio
from trove import TroveConfig, TroveTransport, SearchResource, create_cache

async def async_search_example():
    config = TroveConfig.from_env()
    cache = create_cache("memory")
    transport = TroveTransport(config, cache)
    search = SearchResource(transport)
    
    # Async single search
    result = await search.apage(
        category=['book'],
        q='Australian literature',
        n=10
    )
    print(f"Found {result.total_results} books")
    
    # Async pagination
    page_count = 0
    async for page in search.aiter_pages(
        category=['book'],
        q='poetry',
        n=20
    ):
        page_count += 1
        works = page.categories[0]['records']['work']
        print(f"Page {page_count}: {len(works)} works")
        
        if page_count >= 3:  # Limit for example
            break
    
    # Async record iteration
    async for record in search.aiter_records(
        category=['book'],
        q='novels',
        n=25
    ):
        print(f"Processing: {record.get('title', 'Untitled')}")
        # Process records as they arrive
    
    await transport.aclose()

# Run async operations
asyncio.run(async_search_example())
```

### Concurrent Searches

Async operations enable concurrent searches:

```python
async def concurrent_searches():
    config = TroveConfig.from_env()
    cache = create_cache("memory")
    transport = TroveTransport(config, cache)
    search = SearchResource(transport)
    
    # Run multiple searches concurrently
    results = await asyncio.gather(
        search.apage(category=['book'], q='fiction'),
        search.apage(category=['book'], q='non-fiction'),
        search.apage(category=['image'], q='photographs'),
        search.apage(category=['newspaper'], q='headlines')
    )
    
    for i, result in enumerate(results):
        print(f"Search {i+1}: {result.total_results} results")
    
    await transport.aclose()

asyncio.run(concurrent_searches())
```

## Error Handling

The SDK provides comprehensive error handling and validation:

### Parameter Validation

```python
from trove.exceptions import ValidationError

try:
    # Missing required category
    result = search.page(q='test')
except ValueError as e:
    print(f"Validation error: {e}")

try:
    # Invalid category
    result = search.page(category=['invalid'], q='test') 
except ValueError as e:
    print(f"Invalid category: {e}")

try:
    # Parameter dependencies
    result = search.page(
        category=['newspaper'],
        l_month=['03']  # Month requires year
    )
except ValueError as e:
    print(f"Parameter dependency: {e}")
```

### Pagination Errors

```python
try:
    # Multi-category not supported for iter_pages
    for page in search.iter_pages(category=['book', 'image'], q='test'):
        pass
except ValidationError as e:
    print(f"Pagination error: {e}")
    # Use iter_pages_by_category instead
```

### API Errors

```python
from trove.exceptions import TroveAPIError, RateLimitError, NetworkError

try:
    result = search.page(category=['book'], q='test')
except RateLimitError as e:
    print(f"Rate limited: {e}")
    # SDK automatically handles retries with backoff
except NetworkError as e:
    print(f"Network error: {e}")
except TroveAPIError as e:
    print(f"API error: {e}")
```

### Graceful Error Recovery

```python
# Pagination with error handling
def safe_pagination(search, **params):
    try:
        for page in search.iter_pages(**params):
            yield page
    except TroveAPIError as e:
        print(f"API error during pagination: {e}")
        # Pagination iterator handles this gracefully
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Can resume from last successful page if needed

# Usage
for page in safe_pagination(search, category=['book'], q='test'):
    # Process pages safely
    pass
```

## Examples

### Research Workflow

```python
def research_workflow():
    """Example research workflow using all search features."""
    config = TroveConfig.from_env()
    cache = create_cache("sqlite", db_path="research_cache.db", enhanced=True)
    transport = TroveTransport(config, cache)
    search = SearchResource(transport)
    
    # 1. Exploratory search with facets
    print("1. Exploring Australian literature...")
    result = search.page(
        category=['book'],
        q='Australian literature',
        l_decade=['200'],
        facet=['format', 'language', 'decade'],
        n=1  # Just need facets
    )
    
    # Analyze facets
    if 'facets' in result.categories[0]:
        for facet in result.categories[0]['facets']['facet']:
            print(f"  {facet['name']}: {len(facet['term'])} options")
    
    # 2. Focused search based on facets
    print("\n2. Focused search for poetry books...")
    
    # Use direct SearchParameters construction
    poetry_params = SearchParameters(
        category=['book'],
        q='Australian poetry',
        n=50,                           # Page size
        reclevel='full',                # Full records
        include=['tags', 'workversions'], # Optional fields
        l_decade=['200'],               # Direct assignment
        l_format=['Book'],
        l_australian='y',
        l_availability=['y/f']          # Free online
    )
    
    # 3. Systematic collection
    poetry_works = []
    for record in search.iter_records(params=poetry_params):
        poetry_works.append({
            'title': record.get('title'),
            'author': record.get('contributor', [{}])[0].get('name'),
            'year': record.get('issued'),
            'url': record.get('troveUrl')
        })
        
        if len(poetry_works) >= 100:  # Collect 100 works
            break
    
    print(f"Collected {len(poetry_works)} poetry works")
    
    # 4. Cache statistics
    if hasattr(cache, 'get_stats'):
        stats = cache.get_stats()
        print(f"\nCache performance:")
        print(f"  Hit rate: {stats['hit_rate']:.2%}")
        print(f"  Requests: {stats['total_requests']}")
        print(f"  Time saved: {stats['cache_savings_seconds']:.1f}s")
    
    transport.close()
    return poetry_works

# Run research workflow
works = research_workflow()
```

### Comparative Analysis

```python
async def comparative_analysis():
    """Compare results across different time periods."""
    config = TroveConfig.from_env()
    cache = create_cache("memory", enhanced=True)
    transport = TroveTransport(config, cache)
    search = SearchResource(transport)
    
    # Search different decades concurrently
    decades = ['180', '190', '200']  # 1800s, 1900s, 2000s
    
    search_tasks = [
        search.apage(
            category=['newspaper'],
            q='women rights',
            l_decade=[decade],
            n=20
        ) for decade in decades
    ]
    
    results = await asyncio.gather(*search_tasks)
    
    # Analyze results by decade
    for decade, result in zip(decades, results):
        decade_start = int(decade) * 10
        print(f"{decade_start}s: {result.total_results} articles about women's rights")
        
        # Sample articles
        if result.categories[0]['records'].get('article'):
            articles = result.categories[0]['records']['article'][:3]
            for article in articles:
                title = article.get('heading', 'Untitled')
                print(f"  - {title}")
    
    await transport.aclose()

# Run comparative analysis
asyncio.run(comparative_analysis())
```

This comprehensive guide covers all the search functionality implemented in Stage 2. For more examples, see the `examples/` directory and the integration tests.