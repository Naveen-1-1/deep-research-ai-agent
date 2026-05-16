from crewai import Crew, Agent, Task
from crewai.tools import tool
import asyncio
import json
import logging
import os

from dotenv import load_dotenv

from services.firecrawl_mcp import mcp_available, mcp_firecrawl_search
from utils.log_sanitizer import configure_safe_logging, register_secrets_from_env
from utils.crewai_safe_console import patch_crewai_console_redaction
from utils.tool_names import TOOL_FIRECRAWL_SEARCH
from utils.llm_config import LLM_PROVIDER, get_crew_llm_model

load_dotenv()
configure_safe_logging()
register_secrets_from_env()
patch_crewai_console_redaction()

FIRECRAWL_KEY = os.getenv("FIRECRAWL_KEY")

logger = logging.getLogger(__name__)

extracted_links: list[str] = []


def _collect_urls_from_payload(payload) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in ("url", "sourceURL", "source_url") and isinstance(value, str) and value.startswith("http"):
                if value not in extracted_links:
                    extracted_links.append(value)
            else:
                _collect_urls_from_payload(value)
    elif isinstance(payload, list):
        for item in payload:
            _collect_urls_from_payload(item)


def _attach_urls_from_result(result: str) -> str:
    try:
        _collect_urls_from_payload(json.loads(result))
    except (json.JSONDecodeError, TypeError):
        _collect_urls_from_payload(result)
    return result


@tool(TOOL_FIRECRAWL_SEARCH)
def firecrawl_search(query: str, limit: int = 3) -> str:
    """
    Search the web via Firecrawl MCP. Use for all web research.
    Args: query (required), limit (optional, default 3).
    """
    if not FIRECRAWL_KEY or not FIRECRAWL_KEY.strip():
        return "FIRECRAWL_KEY is not configured."
    if not mcp_available():
        return "MCP not available. Install Node.js (npx) for firecrawl-mcp."
    try:
        result = asyncio.run(mcp_firecrawl_search(query, limit))
        return _attach_urls_from_result(result)
    except Exception as exc:
        from utils.log_sanitizer import redact_secrets

        logger.warning("MCP search failed: %s", redact_secrets(str(exc)))
        return f"MCP search failed: {redact_secrets(str(exc))}"


def setup_agents_and_tasks(query, breadth, depth):
    global extracted_links
    extracted_links = []

    if not FIRECRAWL_KEY or not FIRECRAWL_KEY.strip():
        raise ValueError("Firecrawl API key is not configured. Please set FIRECRAWL_KEY in .env file.")

    if not mcp_available():
        raise ValueError(
            "Firecrawl MCP requires npx (Node.js). Install Node or set NPX_PATH in .env."
        )

    llm_model = get_crew_llm_model()
    logger.info("Crew agents LLM (%s): %s", LLM_PROVIDER, llm_model)
    logger.info("Research tool: %s (MCP only)", TOOL_FIRECRAWL_SEARCH)

    search_strategy = f"""Search strategy:
        - Use only `{TOOL_FIRECRAWL_SEARCH}` for web research (pass `query` and optional `limit`).
        - After each search, copy titles and URLs from the tool output into your notes.
        - Your final answer must list real URLs from tool results. Never invent links."""

    researcher = Agent(
        name="Research Agent",
        role="Web searcher and data collector",
        goal=f"Research topics using only {TOOL_FIRECRAWL_SEARCH}",
        backstory=(
            f"You only use `{TOOL_FIRECRAWL_SEARCH}`. "
            "Synthesize tool JSON into notes with cited URLs."
        ),
        mcps=[],
        tools=[firecrawl_search],
        llm=llm_model,
        verbose=True,
        allow_delegation=False,
        max_retry_limit=2,
    )

    summarizer = Agent(
        name="Summarization Agent",
        role="Content summarizer",
        goal="Condense detailed findings into concise summaries",
        backstory="Skilled in summarizing complex texts for better understanding",
        tools=[],
        llm=llm_model,
        verbose=True,
        allow_delegation=False,
        max_retry_limit=2,
    )

    presenter = Agent(
        name="Presentation Agent",
        role="Report formatter",
        goal="Create readable and well-structured reports",
        backstory="Experienced in generating polished documents for readers",
        tools=[],
        llm=llm_model,
        verbose=True,
        allow_delegation=False,
        max_retry_limit=2,
    )

    breadth_instruction = f"Generate {breadth} different search queries or angles to explore this topic thoroughly."
    depth_instruction = (
        f"For each angle, perform {depth} levels of investigation "
        f"(initial search + {depth - 1} follow-up searches on interesting findings)."
    )

    task_research = Task(
        description=f"""Perform comprehensive research on: {query}

        Research Parameters:
        - {breadth_instruction}
        - {depth_instruction}

        {search_strategy}

        Ensure you explore the topic from multiple perspectives.""",
        expected_output="Raw web content from multiple search angles, source links, and detailed notes organized by search angle",
        agent=researcher,
    )

    task_summarize = Task(
        description=(
            "Summarize the research findings from the previous task into structured bullet points. "
            "Use only facts and URLs from that context. Do not ask the user for more information."
        ),
        expected_output="Summarized bullets categorized by topic with cited URLs where available",
        agent=summarizer,
        context=[task_research],
    )

    task_present = Task(
        description=(
            "Using the summary from the previous task, write a complete professional research report. "
            "Include sections: Introduction, Key Findings, and Conclusion. "
            "Cite source URLs from the research context. "
            "Never use placeholder URLs (example.com). "
            "Never ask the user for input — always deliver the full report."
        ),
        expected_output="A complete final human-readable report (at least 3 paragraphs)",
        agent=presenter,
        context=[task_research, task_summarize],
    )

    max_steps = max(20, breadth * depth * 7)
    max_time = max(300, breadth * depth * 60)

    crew = Crew(
        agents=[researcher, summarizer, presenter],
        tasks=[task_research, task_summarize, task_present],
        verbose=True,
        max_steps=max_steps,
        max_time=max_time,
    )

    return crew
