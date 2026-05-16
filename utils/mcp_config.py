"""Resolve npx for Firecrawl MCP (stdio)."""

import os
import shutil
from pathlib import Path


def find_npx() -> str | None:
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
