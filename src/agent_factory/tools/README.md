# Available Tools

Below is a list of all available files that contain the tool function.

- `extract_text_from_url.py`: Extract all text content from a given URL using BeautifulSoup.
- `translate_text_with_llm.py`: Translate text from a source language to a target language using an LLM.
- `summarize_text_with_llm.py`: Summarize a given text using an LLM with customizable summary length or style.
- `combine_mp3_files_for_podcast.py`: Combine a list of MP3 audio files into a single MP3 podcast file using `ffmpeg`.
- `extract_text_from_markdown_or_html.py`: Process raw input content (Markdown or HTML) to extract plain text.
- `generate_podcast_script_with_llm.py`: Write a podcast script from a given text document using an LLM with
  configurable number of hosts/speakers.
- `review_code_with_llm.py`: Review a given piece of code for errors, bugs, security issues, and style violations using
  an LLM.
- `visit_webpage.py`: Visit a webpage at the given url and read its content as a markdown string.
- `search_tavily.py`: Perform a Tavily web search based on a given query and return the top search results.

Each of the above tools has a corresponding `.py` file in the `tools/` directory that implements its function. If a
tool's filename and description seem relevant, read its `.py` file to understand the implementation, parameters, and
usage before configuring the agent to use it.

> General Note on LiteLLM and API Keys:
> The functions using LiteLLM (e.g., for OpenAI API calls) require API keys to be configured in your environment.
> For OpenAI, one would set the `OPENAI_API_KEY` environment variable.
