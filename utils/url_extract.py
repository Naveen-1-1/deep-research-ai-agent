"""Collect HTTP(S) URLs from Firecrawl JSON or nested structures."""

from __future__ import annotations

import json
from typing import Any


def collect_urls_from_payload(payload: Any, into: list[str]) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in ("url", "sourceURL", "source_url") and isinstance(value, str) and value.startswith("http"):
                if value not in into:
                    into.append(value)
            else:
                collect_urls_from_payload(value, into)
    elif isinstance(payload, list):
        for item in payload:
            collect_urls_from_payload(item, into)


def collect_urls_from_text(text: str, into: list[str]) -> None:
    try:
        collect_urls_from_payload(json.loads(text), into)
    except (json.JSONDecodeError, TypeError):
        collect_urls_from_payload(text, into)
