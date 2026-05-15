"""Redact secrets from CrewAI Rich console output (not covered by logging filters)."""

from __future__ import annotations

from typing import Any

from utils.log_sanitizer import redact_secrets


def _sanitize_text(text: str) -> str:
    return redact_secrets(text)


def _sanitize_rich_text(obj: Any) -> Any:
    from rich.text import Text

    if isinstance(obj, Text):
        return Text(_sanitize_text(obj.plain))
    return obj


def _sanitize_panel(obj: Any) -> Any:
    from rich.panel import Panel
    from rich.text import Text

    if not isinstance(obj, Panel):
        return obj

    renderable = obj.renderable
    if isinstance(renderable, Text):
        renderable = Text(_sanitize_text(renderable.plain))

    title = obj.title
    if isinstance(title, str):
        title = _sanitize_text(title)

    return Panel(
        renderable,
        title=title,
        border_style=obj.border_style,
        padding=obj.padding,
    )


def _sanitize_console_arg(arg: Any) -> Any:
    from rich.panel import Panel
    from rich.text import Text

    if isinstance(arg, Panel):
        return _sanitize_panel(arg)
    if isinstance(arg, Text):
        return _sanitize_rich_text(arg)
    if isinstance(arg, str):
        return _sanitize_text(arg)
    return arg


def patch_crewai_console_redaction() -> None:
    """Monkey-patch CrewAI ConsoleFormatter.print to redact secrets in all panels."""
    from crewai.events.utils.console_formatter import ConsoleFormatter

    if getattr(ConsoleFormatter, "_secrets_redaction_patched", False):
        return

    original_print = ConsoleFormatter.print

    def safe_print(self: ConsoleFormatter, *args: Any, **kwargs: Any) -> None:
        sanitized = tuple(_sanitize_console_arg(arg) for arg in args)
        original_print(self, *sanitized, **kwargs)

    ConsoleFormatter.print = safe_print  # type: ignore[method-assign]
    ConsoleFormatter._secrets_redaction_patched = True  # type: ignore[attr-defined]
