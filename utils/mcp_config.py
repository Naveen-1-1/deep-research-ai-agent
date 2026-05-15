"""Resolve Firecrawl MCP transport (stdio only by default — never embed API key in URLs)."""

import logging
import os
import shutil
from pathlib import Path

from crewai.mcp import MCPServerStdio
from crewai.mcp.config import MCPServerConfig
from crewai.mcp.filters import create_static_tool_filter

logger = logging.getLogger(__name__)

_SEARCH_TOOL_FILTER = create_static_tool_filter(allowed_tool_names=["firecrawl_search"])


def _find_npx() -> str | None:
    """Return path to npx executable, or None if not installed."""
    explicit = os.getenv("NPX_PATH", "").strip()
    if explicit and Path(explicit).is_file():
        return explicit

    found = shutil.which("npx")
    if found:
        return found

    for candidate in (
        "/opt/homebrew/bin/npx",
        "/usr/local/bin/npx",
        Path.home() / ".nvm/current/bin/npx",
    ):
        if Path(candidate).is_file():
            return str(candidate)

    nvm_versions = Path.home() / ".nvm/versions/node"
    if nvm_versions.is_dir():
        for node_dir in sorted(nvm_versions.iterdir(), reverse=True):
            npx_path = node_dir / "bin" / "npx"
            if npx_path.is_file():
                return str(npx_path)

    return None


def build_firecrawl_mcp_config(api_key: str) -> MCPServerConfig | None:
    """
    Build Firecrawl MCP config when safe to do so.

    Default (auto): stdio via npx only — API key stays in process env, never in URLs.
    Hosted HTTP is opt-in via FIRECRAWL_MCP_TRANSPORT=http (keys may appear in CrewAI UI).
  """
    transport = os.getenv("FIRECRAWL_MCP_TRANSPORT", "auto").strip().lower()
    npx_path = _find_npx()

    if transport == "http":
        logger.warning(
            "FIRECRAWL_MCP_TRANSPORT=http embeds your API key in request URLs. "
            "Prefer stdio: install Node.js or set FIRECRAWL_MCP_TRANSPORT=auto."
        )
        from crewai.mcp import MCPServerHTTP

        return MCPServerHTTP(
            url=f"https://mcp.firecrawl.dev/{api_key}/v2/mcp",
            streamable=True,
            cache_tools_list=True,
            tool_filter=_SEARCH_TOOL_FILTER,
        )

    if transport == "stdio" and not npx_path:
        raise RuntimeError(
            "FIRECRAWL_MCP_TRANSPORT=stdio but npx was not found. "
            "Install Node.js from https://nodejs.org/ or set NPX_PATH in .env."
        )

    if npx_path and transport in ("auto", "stdio"):
        logger.info("Firecrawl MCP: local stdio (npx)")
        return MCPServerStdio(
            command=npx_path,
            args=["-y", "firecrawl-mcp"],
            env={"FIRECRAWL_API_KEY": api_key},
            cache_tools_list=True,
            tool_filter=_SEARCH_TOOL_FILTER,
        )

    logger.info(
        "Firecrawl MCP disabled (npx not found). Using FirecrawlSearchDirect REST tool. "
        "Install Node.js for MCP, or set FIRECRAWL_MCP_TRANSPORT=http to force hosted MCP."
    )
    return None
