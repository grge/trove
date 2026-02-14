# Repository Structure

## What This Is

`/code/trove` is the **Trove SDK and MCP Server** - a Python library and Model Context Protocol server for accessing Australia's National Library digitized collections.

The repository contains:
- `packages/trove-sdk/` - The Python SDK (the tool itself)
- `packages/trove-mcp/` - MCP server implementation
- `README.md` - Project documentation

## What This Is NOT

This repository does NOT contain:
- Research scripts or genealogy work
- Test/debug/analysis code
- Data processing pipelines
- User-specific applications

## Where Research Code Goes

Research scripts that **use** the Trove SDK belong in `~/code/fam/` (the family history research project), not here.

Examples of what should be in `~/code/fam/`:
- `search_mark_dickeson.py` - Query scripts
- `fact_extractor.py` - Data extraction for genealogy
- `research_bridge.py` - Integration layer for research workflows
- Research data files and results

## Separation of Concerns

**Tool** (this repo):
- SDK source code
- API client implementation
- MCP server

**Usage** (~/code/fam/):
- How George uses the tool for genealogy research
- Scripts specific to his research
- Data files and results from research

This keeps the tool clean and reusable, and makes research workflows reproducible and documented.

## Git Best Practices for This Repository

- Commit ONLY SDK and server code
- Use `.gitignore` to prevent research files
- Don't commit test data or research scripts here
- Each commit should be about the tool, not its usage

## Learning from the Mess

On 2026-02-14, this repository got cluttered with ~40 research scripts and markdown docs. This made it:
- Hard to find actual SDK code
- Mixed the tool with its usage
- Created confusing commit history
- Made it unclear what the project actually is

The fix:
1. Created `.gitignore` to prevent research files
2. Removed clutter from working directory
3. Documented the proper structure

Future: Remember this separation when working on the tool.
