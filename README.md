# Trove API Toolkit

A comprehensive Python toolkit for Australia's National Library Trove digital collection, featuring both a powerful SDK and an MCP server for AI agent integration.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-0.5.0+-green.svg)](https://modelcontextprotocol.io/)

## Overview

This project provides two powerful ways to access Australia's vast digital heritage collection:

### 📦 [Trove SDK](packages/trove-sdk/) 
A full-featured Python SDK for direct integration with Trove API v3:
- **🔍 Ergonomic Search API** - Fluent, chainable interface for intuitive research workflows
- **📊 Complete Parameter Support** - All 60+ Trove search parameters with validation
- **📚 Resource Access** - Individual records for works, articles, people, lists, and titles
- **📝 Citation Management** - Generate BibTeX, CSL-JSON citations with PID resolution
- **⚡ Performance Features** - Async/sync support, intelligent caching, rate limiting
- **🛡️ Production Ready** - Comprehensive error handling, type hints, extensive testing

### 🤖 [Trove MCP Server](packages/trove-mcp/)
A Model Context Protocol server that enables AI agents to access Trove through 8 specialized tools:
- **🔍 search_page** - Advanced search across 10+ content categories  
- **📚 get_work** - Access books, images, maps, music, and other works
- **📰 get_article** - Retrieve newspaper articles with full text
- **👥 get_people** - Access biographical records and authority files
- **📝 get_list** - Retrieve user-created lists and collections
- **🔗 resolve_pid** - Resolve PIDs and URLs to record information
- **📚 cite_bibtex** - Generate BibTeX format citations
- **📄 cite_csl_json** - Generate CSL-JSON format citations
- **📊 Structured Output** - Rich Pydantic models for reliable AI integration
- **🔒 Security First** - Environment-only API keys, input validation

## Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Trove API key from [trove.nla.gov.au](https://trove.nla.gov.au/about/create-something/using-api)

### Environment Setup

1. **Get a free Trove API key**:
   ```bash
   # Visit: https://trove.nla.gov.au/about/create-something/using-api
   ```

2. **Clone and configure**:
   ```bash
   git clone <repository-url>
   cd trove2
   
   # Create .env file with your API key
   echo "TROVE_API_KEY=your_api_key_here" > .env
   
   # Install uv (if needed)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Using the SDK

```bash
# Navigate to SDK directory
cd packages/trove-sdk

# Install dependencies
uv sync

# Run the basic example
uv run python examples/first_request.py
```

**Basic SDK Usage:**
```python
from trove import TroveClient

# Initialize client (automatically loads .env)
client = TroveClient.from_env()

# Ergonomic search interface
with client:
    results = (client.search()
              .text("Australian history")
              .in_("book")
              .online()  # Free online access
              .australian_content()
              .page_size(10)
              .first_page())
    
    print(f"Found {results.total_results} books")
    
    # Access results
    for category in results.categories:
        works = category['records'].get('work', [])
        for work in works[:5]:
            print(f"- {work.get('title', 'Unknown Title')}")
```

**Advanced Ergonomic Search:**
```python
# Complex search with method chaining
results = (client.search()
          .text("federation")
          .in_("newspaper")
          .decade("190")  # 1900s
          .state("NSW", "VIC")  # Multiple states
          .illustrated()  # Has illustrations
          .sort_by("date_desc")
          .with_facets("year", "title")
          .page_size(50)
          .first_page())

# Systematic data collection
for record in (client.search()
              .text("women's suffrage")
              .in_("newspaper")
              .decade("190", "191")  # 1900s and 1910s
              .records()):
    title = record.get('heading', 'Unknown')
    date = record.get('date', 'Unknown')
    print(f"{date}: {title}")
```

**Resource Access:**
```python
# Access individual records
work = client.resources.get_work_resource().get('123456')
article = client.resources.get_newspaper_resource().get('18341291')
person = client.resources.get_people_resource().get('1')

# Generate citations
citation = client.citations.extract_from_record(work, RecordType.WORK)
bibtex = client.citations.cite_bibtex(citation)
csl_json = client.citations.cite_csl_json(citation)
```

### Using the MCP Server

```bash
# Navigate to MCP server
cd packages/trove-mcp

# Install dependencies  
uv sync

# Start the server
uv run trove-mcp
```

**With Claude Code** - Add to `~/.config/claude-code/mcp.json`:
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

**MCP Tools (8 total):**
- `search_page` - Search with categories, query, filters, pagination
- `get_work` - Access books, images, maps, music with detailed information
- `get_article` - Retrieve newspaper articles with full text and metadata
- `get_people` - Access biographical records and authority files
- `get_list` - Retrieve user-created lists and collections
- `resolve_pid` - Resolve PIDs and URLs to record information
- `cite_bibtex` - Generate BibTeX format citations
- `cite_csl_json` - Generate CSL-JSON format citations

## Project Structure

```
trove2/
├── packages/
│   ├── trove-sdk/              # Complete Python SDK
│   │   ├── trove/              # Core SDK package
│   │   │   ├── resources/      # Resource access (works, articles, etc.)
│   │   │   ├── citations/      # Citation generation and PID resolution
│   │   │   └── cache.py        # Intelligent caching with statistics
│   │   ├── examples/           # Real working examples
│   │   │   ├── first_request.py
│   │   │   ├── ergonomic_search.py
│   │   │   ├── citations_example.py
│   │   │   └── resources_example.py
│   │   ├── docs/               # Comprehensive documentation
│   │   └── tests/              # Extensive test suite
│   └── trove-mcp/              # MCP server implementation
│       ├── trove_mcp/          # MCP server package
│       │   ├── server.py       # FastMCP-based server
│       │   ├── models.py       # Pydantic output models
│       │   └── utils.py        # Validation and utilities
│       └── tests/              # MCP-specific tests
├── api_docs/                   # LLM-optimized API documentation
├── specs/                      # Technical specifications
└── CLAUDE.md                   # Project development instructions
```

## Key Features

### 🔍 Comprehensive Search Capabilities
- **All Content Types**: Books, newspapers, images, music, people, maps, lists
- **Rich Filtering**: Date ranges, states, formats, availability, languages
- **Smart Pagination**: Automatic cursor management for large result sets
- **Faceted Browsing**: Explore data through facets like decade, format, language

### 📰 Specialized Newspaper Research
- **Historical Coverage**: Millions of digitized pages from 1803+
- **Full-Text Search**: OCR-processed content with text corrections
- **Geographic Filtering**: Search by state, city, or specific publications
- **Temporal Navigation**: Precise date and decade filtering with validation

### 📚 Individual Record Access
- **Works**: Books, maps, images, music with holdings and tags
- **Articles**: Newspaper and magazine articles with full text
- **People**: Biographical records, occupations, alternate names
- **Lists**: User-curated collections and bibliographies
- **Titles**: Newspaper and magazine publication information

### 📝 Advanced Citation Management
- **Multiple Formats**: BibTeX, CSL-JSON with plans for APA and Chicago
- **PID Resolution**: Handle Trove persistent identifiers and URLs
- **Automatic Extraction**: Smart citation data extraction from records
- **Bibliography Generation**: Create bibliographies from multiple sources

### ⚡ Performance & Reliability
- **Intelligent Caching**: Content-aware TTL with performance statistics
- **Rate Limiting**: Respectful API usage with token bucket algorithm
- **Async Support**: Full async/await support for concurrent operations
- **Error Handling**: Structured exceptions with helpful messages

## Real Examples

### Historical Research Workflow
```python
# Search 1850s newspapers for gold rush coverage
results = (client.search()
          .text("gold rush")
          .in_("newspaper")
          .decade("185")  # 1850s
          .state("Victoria")
          .sort_by("date_desc")
          .first_page())

# Get detailed articles with full text
for record in results.categories[0]['records']['article'][:5]:
    article = client.resources.get_newspaper_resource().get(record['id'])
    full_text = client.resources.get_newspaper_resource().get_full_text(record['id'])
    print(f"Article: {article.get('heading')}")
    print(f"Date: {article.get('date')}")
    print(f"Text length: {len(full_text)} characters")
```

### Academic Bibliography Generation
```python
# Search for academic sources
books = (client.search()
        .text("Australian literature")
        .in_("book")
        .decade("200")  # 2000s
        .australian_content()
        .first_page())

# Generate bibliography
citations = []
for record in books.categories[0]['records']['work'][:10]:
    citation = client.citations.extract_from_record(record, RecordType.WORK)
    citations.append(citation)

# Create BibTeX bibliography
bibliography = client.citations.bibliography_bibtex(citations)
print(bibliography)
```

### Multi-Category Research
```python
# Search across multiple content types
for record in (client.search()
              .text("Eureka Stockade")
              .in_("book", "newspaper", "image")
              .records()):
    record_type = "book" if 'title' in record else "article" if 'heading' in record else "other"
    title = record.get('title') or record.get('heading') or 'Unknown'
    print(f"{record_type}: {title}")
```

## Documentation

### SDK Documentation
- [SDK Overview](packages/trove-sdk/docs/api/overview.md) - Getting started guide
- [Searching Guide](packages/trove-sdk/docs/searching_guide.md) - Advanced search techniques  
- [Resources Guide](packages/trove-sdk/docs/resources_guide.md) - Working with individual records
- [Citations Guide](packages/trove-sdk/docs/citations_guide.md) - Citation generation and management
- [Complete API Reference](packages/trove-sdk/docs/api/) - Full API documentation

### MCP Server Documentation
- [MCP Server README](packages/trove-mcp/README.md) - Complete setup and usage guide
- Built-in MCP resources:
  - `trove://categories` - Content category descriptions and guidance
  - `trove://newspaper-search` - Newspaper research best practices
  - `trove://about` - Server capabilities and version information

### API Documentation
- [Complete API Index](api_docs/trove-api-index.md) - Full Trove API reference
- [Search Parameters](api_docs/trove-search-parameters.md) - All search options explained
- [Response Formats](api_docs/trove-response-formats.md) - Understanding API responses

## Development

### Running Tests

```bash
# Test the SDK
cd packages/trove-sdk
uv run python -m pytest -v

# Test the MCP server  
cd packages/trove-mcp
uv run python -m pytest -v

# Run integration tests (requires API key)
uv run python -m pytest -m integration -v

# Run with coverage
uv run python -m pytest --cov=trove --cov-report=html
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

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes with tests
4. Ensure all tests pass: `uv run python -m pytest`
5. Submit a pull request

## Environment Configuration

```bash
# Required
TROVE_API_KEY=your_api_key_here

# Optional (with defaults)
TROVE_RATE_LIMIT=2.0           # Requests per second
TROVE_CACHE_BACKEND=memory     # memory|sqlite|none
TROVE_LOG_REQUESTS=false       # Enable request logging
```

The SDK automatically searches for `.env` files in your project directory and parent directories.

## Common Use Cases

### 📚 Academic Research
- Search peer-reviewed sources across multiple formats
- Generate properly formatted citations and bibliographies
- Access full metadata including holdings and tags
- Export citations to reference management tools

### 🗞️ Historical Investigation  
- Search millions of historical newspaper pages
- Filter by precise date ranges, locations, and publications
- Access full-text OCR content with corrections
- Track stories across time and geographic regions

### 🖼️ Visual & Cultural Research
- Discover historical photographs, maps, and artwork
- Find multimedia content including audio and video
- Access descriptive metadata and subject classifications
- Identify culturally sensitive or First Nations content

### 🎓 Educational Projects
- Build reading lists and course bibliographies
- Demonstrate historical research methodologies
- Access age-appropriate content with availability filters
- Create multimedia presentations with diverse source types

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links & Resources

### Official Trove Resources
- [Trove Homepage](https://trove.nla.gov.au/)
- [Trove API Documentation](https://trove.nla.gov.au/about/create-something/using-api)
- [Get API Key](https://trove.nla.gov.au/about/create-something/using-api#getting-an-api-key)
- [Trove Help & Support](https://trove.nla.gov.au/help)

### Technical Resources
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Python httpx Library](https://www.python-httpx.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

### Research & Education
- [National Library Research Guides](https://www.nla.gov.au/research/guide/)
- [Digital Research Methods](https://glam-workbench.net/trove/)
- [Historical Newspaper Analysis](https://glam-workbench.net/trove-newspapers/)

## Support

### For SDK Issues
1. Check the [SDK documentation](packages/trove-sdk/docs/)
2. Review [working examples](packages/trove-sdk/examples/)
3. Search existing issues
4. Create a new issue with reproduction steps

### For MCP Server Issues  
1. Check the [MCP README](packages/trove-mcp/README.md)
2. Use built-in resources (`trove://categories`, `trove://about`)
3. Verify your API key and MCP configuration
4. Create an issue with error logs and configuration

### For API Questions
1. Consult [official Trove documentation](https://trove.nla.gov.au/about/create-something/using-api)
2. Check the [complete API reference](api_docs/trove-api-index.md)
3. Contact Trove support for API-specific issues

---

**Ready to explore Australia's digital heritage?** Start with the [basic example](packages/trove-sdk/examples/first_request.py) or integrate the [MCP server](packages/trove-mcp/) with your AI agent today!