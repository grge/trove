# Trove API Documentation

This project contains a python library for the Trove API v3, which provides access to Australia's National Library digital collection. It also contains an MCP server implementation that is currently under development.

Key folders:
- trove-sdk: The main SDK library for accessing the Trove API.
- trove-mcp: The MCP server implementation for the Trove API.
- api_docs: LLM friendly description of the Trove API endpoints, and raw OpenAPI spec.
- trove-sdk/docs/api: Documentation for the SDK, including usage examples and API reference.

## MCP REWRITE PROJECT

We are currently trying to write a good MCP server

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
