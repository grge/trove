# TroveClient

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
