# Trove MCP Server

An MCP server built on top of the Trove SDK.

It exposes a subset of Trove functionality to MCP-compatible clients, mainly around search, record lookup, and citation generation.

## Status

This package is usable, but it is less mature than the SDK it depends on.

It should be treated as a secondary adapter layer rather than the centre of the project.

## What it provides

The server currently exposes tools for:
- search
- work lookup
- article lookup
- people lookup
- list lookup
- PID resolution
- BibTeX citation generation
- CSL-JSON citation generation

## Installation

For local development in this repo:

```bash
cd packages/trove-mcp
uv sync
```

You will also need a Trove API key:

```bash
export TROVE_API_KEY="your_api_key_here"
```

## Running

```bash
uv run trove-mcp
```

## Claude Code example

```json
{
  "mcpServers": {
    "trove": {
      "command": "uv",
      "args": ["run", "trove-mcp"],
      "cwd": "/path/to/trove/packages/trove-mcp",
      "env": {
        "TROVE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Notes on packaging

At the moment this package is mainly set up for local development inside this repository.

The dependency on `trove-sdk` is currently wired in a development-oriented way, so this should not yet be read as a polished standalone distribution.

## Development

```bash
cd packages/trove-mcp
uv run python -m pytest
```

## Relationship to the SDK

This package is a thin layer over `packages/trove-sdk/`.

If you are deciding where to spend effort, the SDK is the more important part of the codebase.

## License

MIT
