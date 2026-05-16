"""
LangChain multi-step research: ReAct Research Agent → Summarizer → Presenter.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

from services.firecrawl_mcp import FIRECRAWL_KEY, mcp_available, mcp_firecrawl_search
from utils.llm_config import LLM_PROVIDER, get_langchain_llm
from utils.log_sanitizer import configure_safe_logging, register_secrets_from_env, redact_secrets
from utils.tool_names import TOOL_FIRECRAWL_SEARCH
from utils.url_extract import collect_urls_from_text

load_dotenv()
configure_safe_logging()
register_secrets_from_env()

logger = logging.getLogger(__name__)

extracted_links: list[str] = []


def _record_urls(text: str) -> None:
    collect_urls_from_text(text, extracted_links)


def _message_content(message: Any) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return str(content)


@tool(TOOL_FIRECRAWL_SEARCH)
def firecrawl_search(query: str, limit: int = 3) -> str:
    """
    Search the web via Firecrawl MCP. Use for all web research.
    Args: query (required), limit (optional, default 3, max 10).
    """
    if not FIRECRAWL_KEY or not FIRECRAWL_KEY.strip():
        return "FIRECRAWL_KEY is not configured."
    if not mcp_available():
        return "MCP not available. Install Node.js (npx) for firecrawl-mcp."
    try:
        logger.info("Research agent calling %s: %s", TOOL_FIRECRAWL_SEARCH, query)
        result = asyncio.run(mcp_firecrawl_search(query, limit))
        _record_urls(result)
        return result
    except Exception as exc:
        logger.warning("MCP search failed: %s", redact_secrets(str(exc)))
        return f"MCP search failed: {redact_secrets(str(exc))}"


def _research_system_prompt(breadth: int, depth: int) -> str:
    return f"""You are the Research Agent — an autonomous web researcher and data collector.

You have one tool: `{TOOL_FIRECRAWL_SEARCH}`. Use it whenever you need live web data.

Research approach (you decide the exact queries and when to stop):
- Explore the topic from about {breadth} different angles (distinct search queries).
- For each angle, investigate about {depth} levels deep (initial search plus follow-ups on important findings).
- After each tool call, extract titles, key facts, and real URLs from the JSON into your working notes.
- When you have enough coverage, output final research notes with cited URLs from tool results only.
- Never invent URLs or placeholders (e.g. example.com).
- Do not ask the user for more input."""


def _summarize_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are the Summarization Agent. Condense research notes into structured "
                "bullet points by theme. Keep cited URLs from the notes. "
                "Use only facts from the research context.",
            ),
            ("human", "Research notes:\n{notes}\n\nStructured summary:"),
        ]
    )


def _report_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are the Presentation Agent. Write a complete professional research report "
                "in markdown with sections: Introduction, Key Findings, Conclusion. "
                "Cite source URLs from the context. Never use placeholder URLs. "
                "Deliver the full report without asking the user for input.",
            ),
            (
                "human",
                "Topic: {topic}\n\nSummary:\n{summary}\n\nResearch notes:\n{notes}\n\n"
                "Final report:",
            ),
        ]
    )


def _extract_research_output(agent_result: dict) -> str:
    """Build research notes from agent messages (tool results + final answer)."""
    messages = agent_result.get("messages", [])
    parts: list[str] = []

    for message in messages:
        if isinstance(message, ToolMessage):
            text = _message_content(message).strip()
            if text:
                parts.append(text)
        elif isinstance(message, AIMessage):
            text = _message_content(message).strip()
            tool_calls = getattr(message, "tool_calls", None) or []
            if text and not tool_calls:
                parts.append(text)

    if parts:
        return "\n\n---\n\n".join(parts)

    if messages:
        return _message_content(messages[-1]).strip()
    return ""


def _max_agent_steps(breadth: int, depth: int) -> int:
    return max(20, breadth * depth * 7)


def run_research_pipeline(topic: str, breadth: int, depth: int) -> str:
    """
    Run Research Agent (ReAct + firecrawl_search) → Summarizer → Presenter.
    Populates module-level extracted_links.
    """
    global extracted_links
    extracted_links = []

    if not FIRECRAWL_KEY:
        raise ValueError("Firecrawl API key is not configured. Please set FIRECRAWL_KEY in .env file.")
    if not mcp_available():
        raise ValueError(
            "Firecrawl MCP requires npx (Node.js). Install Node or set NPX_PATH in .env."
        )

    llm = get_langchain_llm()
    max_steps = _max_agent_steps(breadth, depth)
    logger.info(
        "LangChain agents (%s) | breadth=%s depth=%s | research recursion_limit=%s",
        LLM_PROVIDER,
        breadth,
        depth,
        max_steps,
    )

    research_agent = create_agent(
        llm,
        tools=[firecrawl_search],
        system_prompt=_research_system_prompt(breadth, depth),
        name="Research Agent",
    )

    logger.info("Research Agent: starting autonomous research")
    agent_result = research_agent.invoke(
        {"messages": [("user", f"Research topic: {topic}")]},
        config={"recursion_limit": max_steps},
    )

    research_notes = _extract_research_output(agent_result)
    _record_urls(research_notes)
    if not research_notes.strip():
        raise RuntimeError(
            "Research Agent returned empty output. "
            "Try a larger Ollama model or LLM_PROVIDER=gemini."
        )
    logger.info("Research Agent: finished (%s chars)", len(research_notes))

    logger.info("Summarization Agent: starting")
    summary = _message_content(
        (_summarize_prompt() | llm).invoke({"notes": research_notes})
    )
    logger.info("Summarization Agent: finished")

    logger.info("Presentation Agent: starting")
    report = _message_content(
        (_report_prompt() | llm).invoke(
            {"topic": topic, "summary": summary, "notes": research_notes}
        )
    )
    _record_urls(report)
    logger.info("Presentation Agent: finished")

    return report.strip()
