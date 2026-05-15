from services.agents_service import setup_agents_and_tasks, extracted_links
from models.pdf_generator import create_pdf
from utils.markdown_cleaner import clean_markdown, extract_urls
import base64
import re


_INCOMPLETE_REPORT_PATTERNS = (
    r"please provide the source urls",
    r"once i have them",
    r"please provide.*urls",
)


def _is_incomplete_report(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in _INCOMPLETE_REPORT_PATTERNS)


def _resolve_report_output(result) -> str:
    """Prefer a complete task output when the crew's final output is incomplete."""
    if hasattr(result, "raw") and result.raw and not _is_incomplete_report(result.raw):
        return result.raw

    if hasattr(result, "tasks_output") and result.tasks_output:
        for task_output in reversed(result.tasks_output):
            raw = getattr(task_output, "raw", None) or str(task_output)
            if raw and not _is_incomplete_report(raw):
                return raw

    return result.raw if hasattr(result, "raw") else str(result)


def run_deep_research(query, breadth, depth):
    crew = setup_agents_and_tasks(query, breadth, depth)
    result = crew.kickoff()
    raw_output = _resolve_report_output(result)
    cleaned_output = clean_markdown(raw_output)

    links = list(extracted_links)
    for url in extract_urls(raw_output):
        if url not in links:
            links.append(url)

    summary_text = f"Summary for research topic: {query}"
    pdf_path = create_pdf(summary_text, cleaned_output, links)

    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
        base64_pdf = base64.b64encode(pdf_data).decode("utf-8")

    return cleaned_output, pdf_data, base64_pdf
