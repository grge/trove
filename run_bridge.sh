#!/bin/bash
cd /home/grge/code/trove/packages/trove-sdk
exec uv run python ../../openclaw_mcp_bridge.py "$@"