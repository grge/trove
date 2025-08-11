# Trove API Documentation

This project contains fragmented documentation for the Trove API v3, designed for optimal AI agent consumption.

## Key Resources

- **[api_docs/trove-api-index.md](./api_docs/trove-api-index.md)** - Complete documentation index
- **[api_docs/trove-api-v3.yaml](./api_docs/trove-api-v3.yaml)** - Original OpenAPI specification  
- **[api_docs/trove-search-parameters.md](./api_docs/trove-search-parameters.md)** - Search guide
- **[api_docs/trove-api-authentication.md](./api_docs/trove-api-authentication.md)** - API key setup

See [api_docs/CLAUDE.md](./api_docs/CLAUDE.md) for detailed AI agent guidance.

## Development Setup

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- Trove API key from [trove.nla.gov.au](https://trove.nla.gov.au/about/create-something/using-api)

### Environment Configuration

1. **Create `.env` file** in the project root with your API key:
   ```bash
   echo "TROVE_API_KEY=your_api_key_here" > .env
   ```

2. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Working with the SDK

```bash
# Navigate to SDK package
cd packages/trove-sdk

# Install dependencies
uv sync

# Run all tests (automatically loads .env)
uv run python -m pytest -v

# Run only unit tests (no API key required)
uv run python -m pytest -m "not integration" -v

# Run only integration tests (requires API key)
uv run python -m pytest -m integration -v

# Run example script
uv run python examples/first_request.py
```

### Environment Variables

The SDK automatically loads `.env` files from:
- Project root directory
- Current working directory  
- Parent directories (up to 3 levels)

Supported variables:
```env
# Required
TROVE_API_KEY=your_api_key_here

# Optional (with defaults)
TROVE_RATE_LIMIT=2.0
TROVE_CACHE_BACKEND=memory
TROVE_LOG_REQUESTS=false
```

## External Links

- [Official Trove API Documentation](https://trove.nla.gov.au/about/create-something/using-api)
- [Getting an API Key](https://trove.nla.gov.au/about/create-something/using-api#getting-an-api-key)
