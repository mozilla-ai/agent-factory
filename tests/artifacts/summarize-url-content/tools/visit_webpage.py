import re

import requests
from markdownify import markdownify
from requests.exceptions import RequestException


def _truncate_content(content: str, max_length: int) -> str:
    if len(content) <= max_length:
        return content
    return (
        content[: max_length // 2]
        + f"\n..._This content has been truncated to stay below {max_length} characters_...\n"
        + content[-max_length // 2 :]
    )


def visit_webpage(url: str, timeout: int = 30, max_length: int = None) -> str:
    """Visits a webpage at the given url and reads its content as a markdown string. Use this to browse webpages.

    Args:
        url: The url of the webpage to visit.
        timeout: The timeout in seconds for the request.
        max_length: The maximum number of characters of text that can be returned.
                    If not provided, the full webpage is returned.

    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        markdown_content = markdownify(response.text).strip()

        markdown_content = re.sub(r"\n{2,}", "\n", markdown_content)

        if max_length:
            return _truncate_content(markdown_content, max_length)

        return str(markdown_content)

    except RequestException as e:
        return f"Error fetching the webpage: {e!s}"
    except Exception as e:
        return f"An unexpected error occurred: {e!s}"
