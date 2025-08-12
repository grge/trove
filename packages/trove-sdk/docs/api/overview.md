# Trove SDK API Reference

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
