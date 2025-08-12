# Trove MCP Server Testing Guide for Claude Code

This guide provides step-by-step instructions for testing the Trove MCP server with Claude Code.

## Prerequisites

1. **Trove API Key**: Get your API key from [trove.nla.gov.au](https://trove.nla.gov.au/about/create-something/using-api)
2. **Claude Code**: Installed and configured
3. **Python 3.10+**: With uv package manager

## Setup Instructions

### 1. Environment Configuration

Create a `.env` file in the project root:

```bash
cd /home/george/code/trove2
echo "TROVE_API_KEY=your_actual_api_key_here" > .env
```

### 2. Install Dependencies

```bash
# Navigate to MCP package
cd packages/trove-mcp

# Install dependencies
uv sync

# Verify installation
uv run python -c "import trove_mcp; print('✅ Installation successful')"
```

### 3. Test the MCP Server Locally

```bash
# Test the server starts correctly (will wait for stdin input)
PYTHONPATH="../trove-sdk:$PYTHONPATH" TROVE_API_KEY="your_actual_api_key_here" uv run python -m trove_mcp.server --debug

# Should see output like:
# INFO - Trove MCP Server initialized with 8 tools
# Server listening on stdio...
```

Press `Ctrl+C` to stop the test server.

## Claude Code Integration

### 1. Configure Claude Code MCP Settings

Create or update your Claude Code MCP configuration file:

**Location**: `~/.config/claude-code/mcp.json` (or your Claude Code config directory)

```json
{
  "mcpServers": {
    "trove": {
      "command": "uv",
      "args": ["run", "python", "-m", "trove_mcp.server"],
      "cwd": "/home/george/code/trove2/packages/trove-mcp",
      "env": {
        "PYTHONPATH": "../trove-sdk",
        "TROVE_API_KEY": "your_actual_api_key_here"
      }
    }
  }
}
```

### 2. Restart Claude Code

Restart Claude Code to load the new MCP server configuration.

### 3. Verify MCP Server is Available

In Claude Code, you should see the Trove MCP server listed in available tools:

- `search_page`
- `get_work`
- `get_article`
- `get_people`
- `get_list`
- `resolve_pid`
- `citation_bibtex`
- `citation_csl_json`

## Test Cases for Claude Code

### Test 1: Basic Search

**Prompt**: "Search for 5 books about Australian history using the Trove MCP server."

**Expected Tool Call**:
```json
{
  "tool": "search_page",
  "arguments": {
    "categories": ["book"],
    "query": "Australian history",
    "page_size": 5
  }
}
```

**Expected Result**: JSON response with search results containing books about Australian history.

### Test 2: Get Specific Work

**Prompt**: "Get the details for a specific work record using ID [work_id_from_search]."

**Expected Tool Call**:
```json
{
  "tool": "get_work",
  "arguments": {
    "record_id": "[work_id]",
    "record_level": "brief"
  }
}
```

**Expected Result**: Detailed work record information.

### Test 3: Search with Filters

**Prompt**: "Search for newspaper articles from the 1920s about Melbourne."

**Expected Tool Call**:
```json
{
  "tool": "search_page",
  "arguments": {
    "categories": ["newspaper"],
    "query": "Melbourne",
    "limits": {
      "l-decade": "192"
    },
    "page_size": 10
  }
}
```

**Expected Result**: Filtered search results.

### Test 4: PID Resolution

**Prompt**: "Resolve this Trove identifier: nla.news-article18341291"

**Expected Tool Call**:
```json
{
  "tool": "resolve_pid",
  "arguments": {
    "identifier": "nla.news-article18341291"
  }
}
```

**Expected Result**: Resolved record information with type, ID, URLs, etc.

### Test 5: Citation Generation

**Prompt**: "Generate a BibTeX citation for this Trove URL: https://nla.gov.au/nla.obj-123456789"

**Expected Tool Call**:
```json
{
  "tool": "citation_bibtex",
  "arguments": {
    "source": "https://nla.gov.au/nla.obj-123456789"
  }
}
```

**Expected Result**: Properly formatted BibTeX citation.

### Test 6: Multi-step Workflow

**Prompt**: "Search for books about 'Eureka Stockade', get the first result, and generate a citation for it."

**Expected Sequence**:
1. `search_page` tool call
2. `get_work` tool call with ID from search
3. `citation_bibtex` tool call with the work data

## Troubleshooting

### Common Issues

#### 1. "Required environment variables not set"
- **Cause**: Missing or incorrect `TROVE_API_KEY`
- **Solution**: Verify the API key is set correctly in the MCP configuration

#### 2. "Unknown tool: search_page"
- **Cause**: MCP server not properly registered with Claude Code
- **Solution**: Check MCP configuration file path and restart Claude Code

#### 3. "Authentication failed"
- **Cause**: Invalid API key
- **Solution**: Verify API key is correct and active at trove.nla.gov.au

#### 4. "Rate limit exceeded"
- **Cause**: Too many requests in short time
- **Solution**: Wait a few seconds and retry (built-in rate limiting should prevent this)

### Debug Mode

For detailed debugging, modify the MCP configuration to include debug logging:

```json
{
  "mcpServers": {
    "trove": {
      "command": "uv",
      "args": ["run", "python", "-m", "trove_mcp.server", "--debug"],
      "cwd": "/home/george/code/trove2/packages/trove-mcp",
      "env": {
        "TROVE_API_KEY": "your_actual_api_key_here"
      }
    }
  }
}
```

### Manual Testing

You can also test the MCP server manually:

```bash
cd /home/george/code/trove2/packages/trove-mcp

# Run unit tests
uv run python -m pytest tests/test_mcp_contracts.py -v

# Run integration tests (requires API key)
export TROVE_API_KEY="your_key_here"
uv run python -m pytest tests/test_mcp_integration.py -v
```

## Success Criteria

The MCP server is working correctly when:

1. ✅ All 8 tools are available in Claude Code
2. ✅ Search operations return valid results
3. ✅ Record retrieval works for different record types
4. ✅ PID resolution handles various identifier formats
5. ✅ Citation generation produces properly formatted output
6. ✅ Error handling provides meaningful error messages
7. ✅ Rate limiting prevents API abuse
8. ✅ Multi-step workflows execute seamlessly

## Performance Expectations

- **Search queries**: < 3 seconds response time
- **Record retrieval**: < 2 seconds response time
- **Citation generation**: < 2 seconds response time
- **PID resolution**: < 1 second response time

## Next Steps

Once testing is complete, the MCP server can be:

1. **Published**: Package for distribution
2. **Documented**: Add to official Claude Code MCP registry
3. **Extended**: Add additional tools or features
4. **Optimized**: Performance tuning for production use

## Support

For issues with the MCP server implementation:
1. Check the troubleshooting section above
2. Review the server logs with `--debug` flag
3. Test individual components with the unit tests
4. Verify API key permissions at trove.nla.gov.au