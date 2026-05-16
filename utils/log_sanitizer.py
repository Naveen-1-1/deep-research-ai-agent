"""Redact API keys and secrets from application logs."""

import logging
import os
import re
from re import Pattern

from dotenv import load_dotenv

_REDACTED = "[REDACTED]"

_LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Hosted Firecrawl MCP puts the API key in the URL path.
_FIRECRAWL_MCP_URL: Pattern[str] = re.compile(
    r"https://mcp\.firecrawl\.dev/[^/\s\"']+/",
    re.IGNORECASE,
)

# Legacy hosted MCP tool names may embed key segments in the name.
_FIRECRAWL_MCP_TOOL_PREFIX: Pattern[str] = re.compile(
    r"mcp_firecrawl_dev_[a-z0-9_]{8,}",
    re.IGNORECASE,
)

# Common API key shapes (Firecrawl, Google, Bearer tokens).
_STATIC_PATTERNS: list[Pattern[str]] = [
    re.compile(r"\bBearer\s+[A-Za-z0-9._\-]+\b", re.IGNORECASE),
    re.compile(r"\bfc-[A-Za-z0-9_-]+\b"),
    re.compile(r"\bAIza[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)(api[_-]?key|authorization|token)\s*[:=]\s*['\"]?[A-Za-z0-9._\-]+"),
]

_registered_secrets: set[str] = set()


def register_secret(value: str | None) -> None:
    """Register a secret value to redact from all log output."""
    if not value or not value.strip():
        return
    secret = value.strip()
    _registered_secrets.add(secret)
    _registered_secrets.add(secret.replace("-", "_"))


def register_secrets_from_env() -> None:
    """Load secrets from environment variables used by this app."""
    for name in ("FIRECRAWL_KEY", "FIRECRAWL_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"):
        register_secret(os.getenv(name))


def redact_secrets(text: str) -> str:
    """Remove known secrets and sensitive URL segments from text."""
    if not text:
        return text

    result = _FIRECRAWL_MCP_URL.sub(f"https://mcp.firecrawl.dev/{_REDACTED}/", text)
    result = _FIRECRAWL_MCP_TOOL_PREFIX.sub(f"mcp_firecrawl_{_REDACTED}", result)

    for pattern in _STATIC_PATTERNS:
        result = pattern.sub(_REDACTED, result)

    for secret in sorted(_registered_secrets, key=len, reverse=True):
        if secret in result:
            result = result.replace(secret, _REDACTED)

    return result


class SecretRedactingFilter(logging.Filter):
    """Logging filter that redacts secrets from every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            return True

        sanitized = redact_secrets(message)
        if sanitized != message:
            record.msg = sanitized
            record.args = ()
        return True


def resolve_log_level() -> int:
    """Read LOG_LEVEL from the environment (default INFO)."""
    raw = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    return _LOG_LEVELS.get(raw, logging.INFO)


def configure_safe_logging(level: int | None = None) -> None:
    """
    Install secret redaction on loggers. Re-registers env secrets on each call
    (safe after load_dotenv). Call at application startup before other imports emit logs.

    Adds a stderr StreamHandler when the root logger has none, so pipeline INFO
    logs appear in the terminal (e.g. under `streamlit run`).
    """
    load_dotenv()
    register_secrets_from_env()
    redact_filter = SecretRedactingFilter()

    if level is None:
        level = resolve_log_level()

    root = logging.getLogger()
    root.setLevel(level)
    if not any(isinstance(f, SecretRedactingFilter) for f in root.filters):
        root.addFilter(redact_filter)

    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s", datefmt="%H:%M:%S")
        )
        handler.addFilter(redact_filter)
        root.addHandler(handler)
    else:
        for handler in root.handlers:
            if not any(isinstance(f, SecretRedactingFilter) for f in handler.filters):
                handler.addFilter(redact_filter)

    # httpx/httpcore log full request URLs including embedded API keys.
    for logger_name in (
        "httpx",
        "httpcore",
        "mcp",
        "mcp.client",
        "mcp.client.streamable_http",
        "urllib3",
    ):
        lib_logger = logging.getLogger(logger_name)
        lib_logger.addFilter(redact_filter)
