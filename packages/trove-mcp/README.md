# Trove MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that provides AI agents with access to Australia's National Library Trove digital collection through a secure, stateless interface.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-0.5.0+-green.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

The Trove MCP Server exposes Australia's national digital collection through three powerful tools designed for AI agents:

- 🔍 **search_page** - Advanced search across 10+ content categories
- 📰 **get_article** - Retrieve newspaper and gazette articles with full text
- 📚 **get_work** - Access books, images, maps, music, and other works

Built on [FastMCP](https://github.com/jlowin/fastmcp) for reliable async operation and structured output.

## Features

- **🚀 Modern Architecture** - Built with FastMCP for optimal performance
- **📊 Structured Output** - Rich Pydantic models with comprehensive typing
- **🔒 Security First** - API keys from environment only, never from client inputs
- **📚 Rich Documentation** - Built-in resources explaining Trove categories and usage
- **⚡ Smart Validation** - Helpful error messages with usage guidance
- **🗞️ Newspaper Focus** - Specialized support for historical newspaper research

## Quick Start

### Installation

```bash
# Clone and install
cd packages/trove-mcp
uv sync

# Or install in development mode
uv pip install -e .
```

### Configuration

1. Get your free API key from [Trove](https://trove.nla.gov.au/about/create-something/using-api)

2. Set environment variable:
```bash
export TROVE_API_KEY="your_api_key_here"
```

### Running the Server

```bash
# Start the MCP server
trove-mcp

# With debug logging
trove-mcp --debug
```

## Usage with Claude Code

Add to your Claude Code MCP configuration (`~/.config/claude-code/mcp.json`):

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

## Available Tools

### 🔍 search_page
Search across Trove's digital collection with advanced filtering.

**Example Usage:**
```json
{
  "tool": "search_page",
  "arguments": {
    "categories": ["newspaper"],
    "query": "Eureka Stockade", 
    "limits": {
      "decade": ["185"]
    },
    "page_size": 10
  }
}
```

**Categories:**
- `newspaper` 🗞️ - Historical newspapers (richest content for research)
- `book` 📚 - Published works and academic sources
- `image` 🖼️ - Photographs, maps, artwork, posters
- `people` 👥 - Biographical records and authority files
- `magazine` 📰 - Periodicals and newsletters
- `music` 🎵 - Audio and video materials
- `diary` 📔 - Diaries, letters, archives
- `list` 📝 - User-created lists
- `research` 🔬 - Research publications and reports

### 📰 get_article
Retrieve detailed newspaper and gazette articles with full text content.

**Example Usage:**
```json
{
  "tool": "get_article",
  "arguments": {
    "record_id": "18341291",
    "include_fields": ["text", "corrections"]
  }
}
```

### 📚 get_work
Access detailed information about books, images, maps, music, and other works.

**Example Usage:**
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

## Built-in Resources

The server provides helpful resources accessible via MCP:

- `trove://categories` - Detailed guide to all Trove categories
- `trove://newspaper-search` - Advanced newspaper search techniques
- `trove://about` - Server information and capabilities

## Example Workflows

### Historical Research
```python
# Search for newspaper articles about the Eureka Stockade
search_result = await search_page(
    categories=["newspaper"],
    query="Eureka Stockade", 
    limits={"decade": ["185"]},
    page_size=20
)

# Get full article text
for article in search_result.categories[0].records.article:
    article_detail = await get_article(
        record_id=article.id,
        include_fields=["text"]
    )
    print(article_detail.data.fulltext)
```

### Academic Research
```python
# Search for books about Australian history
books = await search_page(
    categories=["book"],
    query="Australian history",
    sort_by="relevance",
    page_size=10
)

# Get detailed book information
for book in books.categories[0].records.work:
    book_detail = await get_work(
        record_id=book.id,
        record_level="full",
        include_fields=["holdings", "tags"]
    )
```

## Error Handling

The server provides helpful error messages with guidance:

```json
{
  "error": "Invalid categories: ['invalid_category']",
  "message": "Valid categories for Trove search:\n🗞️ newspaper - START HERE for historical research...",
  "suggestions": ["Use categories=['newspaper'] for historical research"]
}
```

## Development

### Running Tests

```bash
# Run all tests
uv run python -m pytest -v

# Run with coverage
uv run python -m pytest --cov=trove_mcp --cov-report=html
```

### Code Quality

```bash
# Format code
uv run black .

# Lint
uv run ruff check .

# Type check  
uv run mypy .
```

### Testing with MCP Inspector

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Test the server
npx @modelcontextprotocol/inspector uv run trove-mcp
```

## Performance

- **Search queries**: < 3 seconds typical response time
- **Article retrieval**: < 2 seconds with full text
- **Work records**: < 2 seconds with metadata
- **Rate limiting**: Built-in to respect Trove API limits
- **Caching**: Automatic response caching for repeated queries

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes with tests
4. Run the test suite: `uv run python -m pytest`
5. Submit a pull request

## License

MIT License - see [LICENSE](../../LICENSE) file for details.

## Links

- [Trove API Documentation](https://trove.nla.gov.au/about/create-something/using-api)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Get Trove API Key](https://trove.nla.gov.au/about/create-something/using-api#getting-an-api-key)

## Support

For issues with this MCP server:
1. Check the error message guidance
2. Review the built-in resources (`trove://categories`, etc.)
3. Verify your API key is valid at [trove.nla.gov.au](https://trove.nla.gov.au)
4. Open an issue with reproduction steps