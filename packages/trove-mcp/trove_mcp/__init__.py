"""Trove MCP Server - Model Context Protocol server for Trove API access."""

__version__ = "1.0.0"

from .server import mcp, main

__all__ = ["mcp", "main"]