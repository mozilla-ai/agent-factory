import requests
from bs4 import BeautifulSoup


def extract_text_from_url(url: str) -> str:
    """Extracts all text content from a given URL.

    This function fetches the HTML content of the URL and uses BeautifulSoup
    to parse and extract all human-readable text.

    Args:
        url: The URL from which to extract text (e.g., "https://example.com").

    Returns:
        A string containing the extracted text. If an error occurs (e.g.,
        network issue, invalid URL), it returns an error message string.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Get text
        text = soup.get_text(separator=" ", strip=True)
        return text
    except requests.exceptions.RequestException as e:
        return f"Error fetching URL: {e}"
    except Exception as e:
        return f"An unexpected error occurred during URL text extraction: {e}"
