from services.agents_service import setup_agents_and_tasks
from models.pdf_generator import create_pdf
from utils.markdown_cleaner import clean_markdown
import base64

extracted_links = []

# Task 7: Implements run_deep_research function
def run_deep_research(query, breadth, depth):
    crew, researcher_tool, firecrawl_tool = setup_agents_and_tasks(query, breadth, depth)
    result = crew.kickoff()
    raw_output = result.output if hasattr(result, 'output') else str(result)
    cleaned_output = clean_markdown(raw_output)

    summary_text = f"Summary for research topic: {query}"
    pdf_path = create_pdf(summary_text, cleaned_output, extracted_links)

    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
        base64_pdf = base64.b64encode(pdf_data).decode('utf-8')

    return cleaned_output, pdf_data, base64_pdf