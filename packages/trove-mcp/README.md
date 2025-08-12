# Trove MCP Server

A Model Context Protocol (MCP) server that provides AI agents with access to Australia's National Library Trove digital collection through a secure, stateless interface.

## Features

- **8 MCP Tools** for comprehensive Trove API access
- **Stateless Operation** - No server-side state, suitable for serverless environments
- **JSON Schema Validation** - All inputs and outputs strictly validated
- **Security First** - API keys from environment only, never from client inputs
- **Shared Infrastructure** - Uses same cache and rate limiting as Trove SDK

## Available Tools

### Search Tools
- `search_page` - Search Trove records with full parameter support and pagination

### Record Retrieval Tools
- `get_work` - Retrieve work records (books, images, maps, music, etc.)
- `get_article` - Retrieve newspaper and gazette articles
- `get_people` - Retrieve people and organization records
- `get_list` - Retrieve user-created lists

### Utility Tools
- `resolve_pid` - Resolve PIDs and URLs to record information
- `citation_bibtex` - Generate BibTeX citations
- `citation_csl_json` - Generate CSL-JSON citations

## Installation

```bash
# Install from local package
cd packages/trove-mcp
uv sync

# Or install in development mode
uv pip install -e .
```

## Configuration

Set your Trove API key in environment variables:

```bash
export TROVE_API_KEY="your_api_key_here"
```

Optional environment variables:
```bash
export TROVE_RATE_LIMIT=2.0
export TROVE_CACHE_BACKEND=memory
export TROVE_LOG_REQUESTS=false
```

## Usage

### Running the MCP Server

```bash
# Start the server (stdio transport)
trove-mcp

# With debug logging
trove-mcp --debug
```

### Using with Claude Code

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "trove": {
      "command": "uv",
      "args": ["run", "trove-mcp"],
      "cwd": "/path/to/trove2/packages/trove-mcp",
      "env": {
        "TROVE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Example Tool Usage

#### Search for Books
```json
{
  "tool": "search_page",
  "arguments": {
    "categories": ["book"],
    "query": "Australian history",
    "page_size": 10,
    "sort_by": "relevance"
  }
}
```

#### Get a Work Record
```json
{
  "tool": "get_work", 
  "arguments": {
    "record_id": "12345",
    "include_fields": ["holdings", "tags"],
    "record_level": "full"
  }
}
```

#### Generate a Citation
```json
{
  "tool": "citation_bibtex",
  "arguments": {
    "source": "https://nla.gov.au/nla.obj-123456789"
  }
}
```

#### Resolve a PID
```json
{
  "tool": "resolve_pid",
  "arguments": {
    "identifier": "nla.news-article18341291"
  }
}
```

## Development

### Running Tests

```bash
# Run all tests
uv run python -m pytest -v

# Run only unit tests (no API key required)
uv run python -m pytest -m "not integration" -v

# Run only integration tests (requires API key)
uv run python -m pytest -m integration -v
```

### Code Quality

```bash
# Format code
uv run black .

# Lint code
uv run ruff check .

# Type checking
uv run mypy .
```

## Error Handling

The server maps Trove SDK errors to appropriate MCP errors:

- `AuthenticationError` → "Authentication failed"
- `ResourceNotFoundError` → "Resource not found"
- `ValidationError` → "Invalid parameters"
- `RateLimitError` → "Rate limit exceeded"
- `TroveAPIError` → "API error" with HTTP status

## Security

- API keys are only read from environment variables
- No server-side state is maintained
- All inputs are validated with JSON Schema
- Sensitive information is never logged

## Performance

- Shared cache and rate limiting with Trove SDK
- Async operations throughout
- Conservative rate limits for reliable operation
- Stateless design for horizontal scaling

## License

MIT License - see LICENSE file for details.