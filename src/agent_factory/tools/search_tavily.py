import os

from tavily.tavily import TavilyClient


def search_tavily(query: str, include_images: bool = False) -> str:
    """Perform a Tavily web search based on your query and return the top search results.

    See https://blog.tavily.com/getting-started-with-the-tavily-search-api for more information.

    Args:
        query (str): The search query to perform.
        include_images (bool): Whether to include images in the results.

    Returns:
        The top search results as a formatted string.

    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "TAVILY_API_KEY environment variable not set."
    try:
        client = TavilyClient(api_key)
        response = client.search(query, include_images=include_images)
        results = response.get("results", [])
        output = []
        for result in results:
            output.append(f"[{result.get('title', 'No Title')}]({result.get('url', '#')})\n{result.get('content', '')}")
        if include_images and "images" in response:
            output.append("\nImages:")
            for image in response["images"]:
                output.append(image)
        return "\n\n".join(output) if output else "No results found."
    except Exception as e:
        return f"Error performing Tavily search: {e!s}"
