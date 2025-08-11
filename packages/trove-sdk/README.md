# Trove SDK

A Python SDK for accessing Australia's National Library Trove API v3. Provides both synchronous and asynchronous access to Trove's digital collections with built-in rate limiting, caching, and error handling.

## Features

- **Simple & Pythonic API** - Clean interface for all Trove API operations
- **Async & Sync Support** - Use with `asyncio` or traditional synchronous code
- **Built-in Rate Limiting** - Respectful API usage with token bucket algorithm  
- **Smart Caching** - Memory and SQLite caching to reduce API calls
- **Comprehensive Error Handling** - Structured exceptions with automatic retries
- **Type Hints** - Full type safety with modern Python

## Quick Start

### Installation

```bash
# Using pip
pip install trove-sdk

# Using uv (recommended for development)
uv add trove-sdk
```

### Get an API Key

1. Visit [Trove API Registration](https://trove.nla.gov.au/about/create-something/using-api)
2. Register for a free API key
3. Set your API key in a `.env` file (recommended) or environment variable:

**Option 1: Create `.env` file** (recommended)
```bash
# Create .env file in your project root
echo "TROVE_API_KEY=your_api_key_here" > .env
```

**Option 2: Environment variable**
```bash
export TROVE_API_KEY="your_api_key_here"
```

The SDK automatically loads `.env` files from your project directory or parent directories.

### Basic Usage

```python
from trove import TroveConfig, TroveTransport, MemoryCache

# Configure the client
config = TroveConfig.from_env()
cache = MemoryCache()
transport = TroveTransport(config, cache)

try:
    # Search for books about Australian history
    response = transport.get('/v3/result', {
        'category': 'book',
        'q': 'Australian history',
        'n': 10,
        'encoding': 'json'
    })
    
    # Process results
    if 'category' in response:
        category = response['category'][0]
        total_results = category['records']['total']
        works = category['records'].get('work', [])
        
        print(f"Found {total_results} results")
        for work in works[:5]:
            print(f"- {work.get('title', 'Unknown Title')}")

finally:
    transport.close()
```

### Async Usage

```python
import asyncio
from trove import TroveConfig, TroveTransport, MemoryCache

async def search_trove():
    config = TroveConfig.from_env()
    cache = MemoryCache()
    
    async with TroveTransport(config, cache) as transport:
        response = await transport.aget('/v3/result', {
            'category': 'book',
            'q': 'Australian history',
            'n': 5
        })
        
        return response

# Run the async function
results = asyncio.run(search_trove())
```

## Configuration

The SDK can be configured through environment variables or directly:

### Environment Variables

```bash
export TROVE_API_KEY="your_api_key_here"         # Required
export TROVE_RATE_LIMIT="2.0"                    # Requests per second (default: 2.0)
export TROVE_CACHE_BACKEND="memory"              # Cache type: memory|sqlite|none
export TROVE_LOG_REQUESTS="false"                # Log requests (default: false)
```

### Direct Configuration

```python
from trove import TroveConfig

config = TroveConfig(
    api_key="your_api_key_here",
    rate_limit=1.0,               # Be conservative
    burst_limit=3,                # Allow short bursts
    max_concurrency=2,            # Max concurrent requests
    cache_backend="sqlite",       # Use persistent cache
    log_requests=True             # Enable request logging
)
```

## API Examples

### Search Operations

```python
# Basic search
response = transport.get('/v3/result', {
    'category': 'book',
    'q': 'kangaroo',
    'n': 10
})

# Advanced search with facets
response = transport.get('/v3/result', {
    'category': 'newspaper',
    'q': 'gold rush',
    'facet': 'decade,state',
    'l-decade': '190',           # 1900s
    'n': 20
})

# Multiple categories
response = transport.get('/v3/result', {
    'category': 'book,article',
    'q': 'Indigenous Australia',
    'n': 15
})
```

### Individual Records

```python
# Get specific work
work = transport.get('/v3/work/12345', {
    'reclevel': 'full',
    'include': 'holdings,links'
})

# Get newspaper article  
article = transport.get('/v3/newspaper/67890', {
    'reclevel': 'full'
})

# Get people/organization record
person = transport.get('/v3/people/11111', {
    'reclevel': 'brief'
})
```

## Caching

The SDK includes intelligent caching to reduce API load:

```python
from trove.cache import MemoryCache, SqliteCache

# Memory cache (default, fast but temporary)
cache = MemoryCache()

# SQLite cache (persistent across sessions)
cache = SqliteCache()

# Custom SQLite location
cache = SqliteCache(db_path=Path('/tmp/trove_cache.db'))

# No caching
from trove.cache import NoCache
cache = NoCache()
```

## Error Handling

The SDK provides structured exceptions for different error types:

```python
from trove.exceptions import (
    TroveError,           # Base exception
    AuthenticationError,  # Invalid API key
    RateLimitError,      # Rate limit exceeded
    ResourceNotFoundError, # 404 errors
    NetworkError         # Connection issues
)

try:
    response = transport.get('/v3/result', {
        'category': 'book',
        'q': 'test query'
    })
except AuthenticationError:
    print("Invalid API key - check your credentials")
except RateLimitError as e:
    if e.retry_after:
        print(f"Rate limited - retry after {e.retry_after} seconds")
except ResourceNotFoundError:
    print("Resource not found")
except NetworkError:
    print("Network connection failed")
except TroveError as e:
    print(f"Other Trove API error: {e}")
```

## Rate Limiting

The SDK automatically handles rate limiting to be respectful of the Trove API:

- **Default limit**: 2 requests per second
- **Burst capacity**: 5 requests
- **Automatic backoff**: Exponential backoff with jitter for retries
- **Respect Retry-After**: Honors `Retry-After` headers from the API

```python
# Configure custom rate limits
config = TroveConfig(
    api_key="your_key",
    rate_limit=1.0,    # 1 request per second
    burst_limit=3,     # Allow bursts of 3
    max_concurrency=2  # Max 2 concurrent requests
)
```

## Development

### Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- API key from [Trove](https://trove.nla.gov.au/about/create-something/using-api)

### Installation for Development

```bash
# Clone the repository
git clone https://github.com/your-org/trove-sdk
cd trove-sdk/packages/trove-sdk

# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and create virtual environment
uv sync

# Create .env file with your API key (required for integration tests)
echo "TROVE_API_KEY=your_api_key_here" > ../../.env
```

### Running Tests

The test suite automatically loads your API key from the `.env` file:

```bash
# Run all tests (unit + integration)
uv run python -m pytest

# Run with verbose output
uv run python -m pytest -v

# Run unit tests only (no API key required)
uv run python -m pytest -m "not integration"

# Run integration tests only
uv run python -m pytest -m integration

# Run with coverage
uv run python -m pytest --cov=trove
```

### Environment Setup

The SDK automatically searches for `.env` files in:
1. Current working directory
2. Parent directories (up to 3 levels)
3. Specific path if provided to `TroveConfig.from_env(dotenv_path="/path/to/.env")`

Your `.env` file should contain:
```env
# Required for integration tests and examples
TROVE_API_KEY=your_api_key_here

# Optional configuration
TROVE_RATE_LIMIT=2.0
TROVE_CACHE_BACKEND=memory
TROVE_LOG_REQUESTS=false
```

## API Reference

### Core Classes

- **`TroveConfig`** - Configuration management
- **`TroveTransport`** - HTTP client with rate limiting and caching
- **`MemoryCache`** / **`SqliteCache`** - Caching backends
- **`RateLimiter`** - Token bucket rate limiting

### Exception Hierarchy

- **`TroveError`** - Base exception
  - **`ConfigurationError`** - Configuration issues
  - **`AuthenticationError`** - Invalid API key (401)
  - **`AuthorizationError`** - Access forbidden (403)  
  - **`ResourceNotFoundError`** - Resource not found (404)
  - **`RateLimitError`** - Rate limit exceeded (429)
  - **`NetworkError`** - Connection issues
  - **`ValidationError`** - Parameter validation errors
  - **`CacheError`** - Cache operation failures

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v1.0.0 (Stage 1 - Foundation)

- Initial release with core functionality
- HTTP transport with authentication
- Rate limiting and caching
- Basic error handling
- Support for search and individual record endpoints
- Full async/await support
- Comprehensive test suite

## Related Projects

- [Trove API Documentation](https://trove.nla.gov.au/about/create-something/using-api)
- [Trove MCP Server](../trove-mcp/) - Model Context Protocol server built on this SDK

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/trove-sdk/issues)
- **Documentation**: [Full API Documentation](https://your-org.github.io/trove-sdk)
- **Trove Support**: [Trove Help](https://trove.nla.gov.au/about/create-something/using-api)