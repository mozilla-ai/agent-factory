# Available Tools

Below is the list of all available files that can be looked up to fetch the tool function.

- `extract_text_from_url.py`: Extracts all text content from a given URL using BeautifulSoup to parse and extract human-readable text.
- `plot_pandas_series_line_graph.py`: Plots a line graph from a pandas Series and saves it as an image file with a unique filename.
- `generate_recipe_from_ingredients.py`: Generates a recipe using a list of provided ingredients via an LLM.
- `translate_text_with_llm.py`: Translates text from a source language to a target language using an LLM.
- `summarize_text_with_llm.py`: Summarizes a given text using an LLM with customizable summary length or style.
- `combine_mp3_files_for_podcast.py`: Combines a list of MP3 audio files into a single MP3 podcast file using ffmpeg.
- `extract_text_from_markdown_or_html.py`: Preprocesses raw input content (Markdown or HTML) to extract plain text.
- `generate_podcast_script_with_llm.py`: Writes a podcast script from a given text document using an LLM with configurable number of hosts/speakers.
- `generate_database_query_with_llm.py`: Constructs database queries (e.g., SQL) based on natural language requests using an LLM.
- `review_code_with_llm.py`: Reviews a given piece of code for errors, bugs, security issues, and style violations using an LLM.


Each of the above tools has a corresponding .py file in the tools/ directory that implements the function.
If a tool is found relevant based on the filename and description, further read the .py file to understand the tool's implementation and parameters and usage, before using it in the agent configuration.

--- General Note on LiteLLM and API Keys ---
The functions using LiteLLM (e.g., for OpenAI API calls) require API keys
to be configured in your environment. For OpenAI, one would set the OPENAI_API_KEY
environment variable.
