"""Firecrawl search via MCP (stdio). Used by the research agent tool."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

from utils.log_sanitizer import redact_secrets
from utils.mcp_config import find_npx

load_dotenv()

logger = logging.getLogger(__name__)

FIRECRAWL_KEY = os.getenv("FIRECRAWL_KEY", "").strip()


def _mcp_result_to_text(result) -> str:
    parts: list[str] = []
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts) if parts else str(result)


def mcp_available() -> bool:
    return bool(FIRECRAWL_KEY and find_npx())


async def mcp_firecrawl_search(query: str, limit: int = 3) -> str:
    """Spawn firecrawl-mcp over stdio and call firecrawl_search."""
    if not FIRECRAWL_KEY:
        raise ValueError("FIRECRAWL_KEY is not configured")

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    npx = find_npx()
    if not npx:
        raise RuntimeError("npx not found")

    params = StdioServerParameters(
        command=npx,
        args=["-y", "firecrawl-mcp"],
        env={**os.environ, "FIRECRAWL_API_KEY": FIRECRAWL_KEY},
    )

    logger.info("firecrawl_search via MCP (stdio)")
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "firecrawl_search",
                arguments={"query": query, "limit": max(1, min(int(limit), 10))},
            )
            return _mcp_result_to_text(result)
