import re

def extract_urls(text: str) -> list[str]:
    """Extract unique HTTP(S) URLs from text (e.g. research report output)."""
    urls = re.findall(r"https?://[^\s\)\]>\'\"]+", text)
    seen = set()
    unique = []
    for url in urls:
        url = url.rstrip(".,;:)")
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


def clean_markdown(md_text):
    md_text = re.sub(r'#+ ', '', md_text)  # Remove headings
    md_text = re.sub(r'\\*\\*(.*?)\\*\\*', r'\g<1>', md_text)
    md_text = re.sub(r'\\*(.*?)\\*', r'\g<1>', md_text)
    md_text = re.sub(r'`(.*?)`', r'\g<1>', md_text)
    md_text = re.sub(r'- ', '• ', md_text)
    return md_text.strip()
