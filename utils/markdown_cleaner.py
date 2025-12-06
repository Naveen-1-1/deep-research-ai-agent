import re

# Clean markdown
def clean_markdown(md_text):
    md_text = re.sub(r'#+ ', '', md_text)  # Remove headings
    md_text = re.sub(r'\\*\\*(.*?)\\*\\*', r'\g<1>', md_text)
    md_text = re.sub(r'\\*(.*?)\\*', r'\g<1>', md_text)
    md_text = re.sub(r'`(.*?)`', r'\g<1>', md_text)
    md_text = re.sub(r'- ', '• ', md_text)
    return md_text.strip()
