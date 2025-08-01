from bs4 import BeautifulSoup
from markdown import markdown as md_parser


def extract_text_from_markdown_or_html(content: str, content_type: str) -> str:
    """Preprocesses raw input content (Markdown or HTML) to extract plain text.

    Args:
        content: A string containing the raw Markdown or HTML content.
        content_type: The type of the content, either "md" (for Markdown)
                      or "html" (for HTML). Case-insensitive.

    Returns:
        A string containing the extracted plain text.
        Returns an error message string if the content type is unsupported or an error occurs.
    """
    try:
        content_type_lower = content_type.lower()
        if content_type_lower == "html":
            soup = BeautifulSoup(content, "html.parser")
        elif content_type_lower == "md":
            html_content = md_parser(content)
            soup = BeautifulSoup(html_content, "html.parser")
        else:
            return f"Error: Unsupported content type '{content_type}'. Supported types are 'md' or 'html'."

        # Remove script and style elements that might be in HTML or generated from MD
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return text
    except Exception as e:
        return f"An error occurred during text extraction: {e}"
