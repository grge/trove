# Trove SDK

A Python SDK for Australia's National Library Trove API v3.

The main goals are:
- make Trove search easier to work with than the raw API
- provide a usable high-level client without hiding lower-level access
- handle routine concerns like rate limiting, retries, and caching

## Status

This package is the most mature part of the repository.

It has a solid overall structure, but it should still be treated as an active project rather than a fully settled library.

## What it includes

- high-level `TroveClient`
- lower-level transport and resource access
- fluent search builder
- sync and async support
- caching and rate limiting
- citation helpers

## Installation

```bash
pip install trove-sdk
```

For local development in this repo:

```bash
cd packages/trove-sdk
uv sync
```

## Configuration

You need a Trove API key.

```bash
export TROVE_API_KEY="your_api_key_here"
```

`TroveConfig.from_env()` will also load a `.env` file if one is present in the working directory or a nearby parent directory.

## Basic use

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

## Search API

The main convenience layer is the fluent search builder.

```python
results = (
    client.search()
    .text("federation")
    .in_("newspaper")
    .decade("190")
    .state("NSW", "VIC")
    .sort_by("date_desc")
    .page_size(20)
    .first_page()
)
```

For more direct control, use the lower-level search resource and parameter objects.

```python
from trove import TroveClient, SearchParameters

with TroveClient.from_env() as client:
    params = SearchParameters(
        category=["book"],
        q="Australian literature",
        n=10,
    )
    result = client.raw_search.page(params=params)
```

## Main modules

- `trove/config.py` , configuration
- `trove/transport.py` , HTTP transport, retries, caching, rate limiting
- `trove/resources/` , resource-specific accessors
- `trove/search.py` , fluent search builder
- `trove/citations/` , citation support

## Testing

```bash
cd packages/trove-sdk
uv run python -m pytest
```

Integration tests require a valid `TROVE_API_KEY`.

## Documentation

- `docs/searching_guide.md`
- `docs/resources_guide.md`
- `docs/citations_guide.md`
- `docs/api/`
- `examples/`

## Notes

This package is meant to be the core of the repository. The MCP server in `../trove-mcp/` is built on top of it.

## License

MIT
