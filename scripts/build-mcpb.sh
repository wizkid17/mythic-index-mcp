#!/usr/bin/env bash
# Build the Claude Desktop Extension (.mcpb) from the current mcp_server.py.
# Regenerates mcpb-build/server/ (a copy of mcp_server.py with PEP 723 inline
# deps so `uv run` resolves mcp+httpx at install time), then packs the bundle.
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf mcpb-build/server && mkdir -p mcpb-build/server
{
  printf '# /// script\n'
  printf '# requires-python = ">=3.10"\n'
  printf '# dependencies = ["mcp>=1.0.0", "httpx>=0.27.0"]\n'
  printf '# ///\n'
  cat mcp_server.py
} > mcpb-build/server/mcp_server.py

npx -y @anthropic-ai/mcpb validate mcpb-build/manifest.json
npx -y @anthropic-ai/mcpb pack mcpb-build mythic-index.mcpb
echo "Built mythic-index.mcpb"
