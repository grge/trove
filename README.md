# Trove API Toolkit

This repository contains a Python SDK for the Trove API and a separate MCP server built on top of it.

It is aimed at research and library-style use of Australia's National Library Trove API v3.

## What is here

- `packages/trove-sdk/` , the main Python SDK
- `packages/trove-mcp/` , an MCP server that exposes some SDK functionality to AI tools
- `api_docs/` , local API reference material
- `specs/` , design notes and implementation plans

## Status

The SDK is the most mature part of the repository.

The MCP server is usable, but it is a thinner and less settled layer on top of the SDK.

This repo is in decent working shape, but it should still be read as an active project rather than a polished public package set.

## Quick start

### SDK

```bash
cd packages/trove-sdk
uv sync
```

Set an API key:

```bash
export TROVE_API_KEY="your_api_key_here"
```

Basic use:

```python
from trove import TroveClient

with TroveClient.from_env() as client:
    results = (
        client.search()
        .text("Australian history")
        .in_("book")
        .page_size(10)
        .first_page()
    )

    print(results.total_results)
```

### MCP server

```bash
cd packages/trove-mcp
uv sync
uv run trove-mcp
```

## Project shape

The SDK is organised roughly as:
- configuration
- transport
- resources
- search builder
- citations
- optional models

The MCP package is a separate adapter layer that uses the SDK.

## Notes on scope

This repository is for the tool itself.

Research scripts and project-specific usage should live elsewhere. In this workspace, that means `~/code/fam/`, not this repo.

## Documentation

- SDK docs: `packages/trove-sdk/docs/`
- SDK examples: `packages/trove-sdk/examples/`
- MCP README: `packages/trove-mcp/README.md`
- Trove API notes: `api_docs/`

## Development

Run tests from each package directory.

SDK:

```bash
cd packages/trove-sdk
uv run python -m pytest
```

MCP:

```bash
cd packages/trove-mcp
uv run python -m pytest
```

## License

MIT
