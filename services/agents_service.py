from crewai import Crew, Agent, Task
from crewai.tools import tool
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import logging
import os

import requests
from dotenv import load_dotenv

from utils.log_sanitizer import configure_safe_logging, redact_secrets, register_secrets_from_env
from utils.mcp_config import build_firecrawl_mcp_config
from utils.crewai_safe_console import patch_crewai_console_redaction

load_dotenv()
configure_safe_logging()
register_secrets_from_env()
patch_crewai_console_redaction()

FIRECRAWL_KEY = os.getenv("FIRECRAWL_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

logger = logging.getLogger(__name__)

extracted_links: list[str] = []


def get_llm_model():
    """Returns the LLM model string for CrewAI (LiteLLM / Gemini)."""
    if GOOGLE_API_KEY and GOOGLE_API_KEY.strip():
        logger.info("Using Google Gemini as LLM")
        if not os.getenv("GEMINI_API_KEY"):
            os.environ["GEMINI_API_KEY"] = GOOGLE_API_KEY
        return "gemini/gemini-2.5-flash-lite"
    raise ValueError("Google API key is not configured. Please set GOOGLE_API_KEY in .env file.")


def get_firecrawl_mcp_config():
    """Firecrawl MCP via stdio when npx is available; otherwise None (use REST tool)."""
    if not FIRECRAWL_KEY or not FIRECRAWL_KEY.strip():
        raise ValueError("Firecrawl API key is not configured. Please set FIRECRAWL_KEY in .env file.")
    return build_firecrawl_mcp_config(FIRECRAWL_KEY.strip())


def _collect_urls_from_payload(payload) -> None:
    """Append URLs found in search/MCP JSON responses to extracted_links."""
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


@tool("FirecrawlSearchDirect")
def firecrawl_search_direct(query: str) -> str:
    """Fast direct Firecrawl web search. Use when the MCP search tool times out or fails."""
    try:
        response = requests.post(
            "https://api.firecrawl.dev/v1/search",
            headers={
                "Authorization": f"Bearer {FIRECRAWL_KEY}",
                "Content-Type": "application/json",
            },
            json={"query": query, "limit": 5},
            timeout=45,
        )
        if response.status_code == 200:
            data = response.json()
            _collect_urls_from_payload(data)
            return json.dumps(data, indent=2)
        return f"Firecrawl search failed ({response.status_code}): {redact_secrets(response.text[:500])}"
    except Exception as e:
        logger.error("Direct Firecrawl search failed: %s", redact_secrets(str(e)))
        return f"Direct Firecrawl search error: {redact_secrets(str(e))}"


@tool("GeminiKnowledgeFallback")
def gemini_knowledge_fallback(query: str) -> str:
    """Provide background knowledge when web search is unavailable or insufficient."""
    if not GOOGLE_API_KEY or not GOOGLE_API_KEY.strip():
        return f"No fallback LLM available. Query was: {query}"
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3,
            convert_system_message_to_human=True,
        )
        response = llm.invoke([
            HumanMessage(
                content=(
                    f"Please provide a clear explanation about: {query}. "
                    "Include definition, features, and common use cases."
                )
            )
        ])
        return response.content
    except Exception as e:
        logger.error(f"Gemini fallback failed: {e}")
        return f"LLM fallback unavailable. Query was: {query}"


def setup_agents_and_tasks(query, breadth, depth):
    global extracted_links
    extracted_links = []

    llm_model = get_llm_model()
    mcp_config = get_firecrawl_mcp_config()
    mcps = [mcp_config] if mcp_config else []

    logger.info(f"Setting up agents with LLM model: {llm_model}")
    if mcp_config:
        logger.info("Research agent: Firecrawl MCP (firecrawl_search) + direct search fallback")
    else:
        logger.info("Research agent: FirecrawlSearchDirect REST + Gemini fallback (no MCP)")

    if mcp_config:
        search_strategy = """Search strategy (in order):
        1. Try firecrawl_search MCP tool with limit=3 per query.
        2. If MCP times out or fails, use FirecrawlSearchDirect for the same query.
        3. Only use GeminiKnowledgeFallback if both search methods fail."""
    else:
        search_strategy = """Search strategy (in order):
        1. Use FirecrawlSearchDirect for all web searches (limit=5 per query).
        2. Only use GeminiKnowledgeFallback if search fails."""

    researcher = Agent(
        name="Research Agent",
        role="Web searcher and data collector",
        goal="Conduct deep recursive web research",
        backstory="Expert in online information mining and query generation",
        mcps=mcps,
        tools=[firecrawl_search_direct, gemini_knowledge_fallback],
        llm=llm_model,
        verbose=True,
        allow_delegation=False,
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

        Include source URLs in your notes whenever available.

        Ensure you explore the topic from multiple perspectives.""",
        expected_output="Raw web content from multiple search angles, source links, and detailed notes organized by search angle",
        agent=researcher,
    )

    task_summarize = Task(
        description=(
            "Summarize the research findings from the previous task into structured bullet points. "
            "Do not ask the user for more information."
        ),
        expected_output="Summarized bullets categorized by topic",
        agent=summarizer,
        context=[task_research],
    )

    task_present = Task(
        description=(
            "Using the summary from the previous task, write a complete professional research report. "
            "Include sections: Introduction, Key Findings, and Conclusion. "
            "Cite source URLs when available; if none exist, state that findings are from general knowledge. "
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
