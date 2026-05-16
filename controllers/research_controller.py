from services.langchain_pipeline import extracted_links, run_research_pipeline
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


def run_deep_research(query, breadth, depth):
    raw_output = run_research_pipeline(query, breadth, depth)
    if _is_incomplete_report(raw_output):
        raise RuntimeError(
            "The model produced an incomplete report (missing URLs). "
            "Try LLM_PROVIDER=gemini or a larger Ollama model."
        )

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
