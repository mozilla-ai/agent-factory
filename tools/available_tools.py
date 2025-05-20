import subprocess
import uuid
from pathlib import Path

import matplotlib
import pandas as pd
import requests
from bs4 import BeautifulSoup

matplotlib.use("Agg")  # Use Agg backend for non-interactive environments
import matplotlib.pyplot as plt
from litellm import completion
from markdown import markdown as md_parser

# --- General Note on LiteLLM and API Keys ---
# The functions using LiteLLM (e.g., for OpenAI API calls) require API keys
# to be configured in your environment. For OpenAI, set the OPENAI_API_KEY
# environment variable. Refer to LiteLLM documentation for configuring other providers.


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


def plot_pandas_series_line_graph(
    series: pd.Series, title: str = "Line Plot", xlabel: str = "Index", ylabel: str = "Value", output_dir: str = "plots"
) -> str:
    """Plots a line graph from a pandas Series and saves it as an image file.

    The function generates a line plot, saves it to the specified directory
    with a unique filename, and returns the absolute path to the saved image.

    Args:
        series: A pandas Series containing the data to plot.
        title: The title of the plot. Defaults to "Line Plot".
        xlabel: The label for the x-axis. Defaults to "Index".
        ylabel: The label for the y-axis. Defaults to "Value".
        output_dir: The directory where the plot image will be saved.
                      Defaults to "plots". Created if it doesn't exist.

    Returns:
        The absolute path to the saved plot image (e.g., "/path/to/plots/plot_uuid.png").
        Returns an error message string if plotting fails.
    """
    try:
        if not isinstance(series, pd.Series):
            return "Error: Input data must be a pandas Series."
        if series.empty:
            return "Error: Input pandas Series is empty."

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots()
        series.plot(kind="line", ax=ax)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        plt.tight_layout()

        filename = f"plot_{uuid.uuid4().hex}.png"
        filepath = Path(output_dir) / filename

        plt.savefig(filepath)
        plt.close(fig)  # Close the figure to free memory

        return str(Path(filepath).resolve())
    except Exception as e:
        return f"An error occurred during plotting: {e}"


def generate_recipe_from_ingredients(ingredients: list[str], model: str = "gpt-4o-mini") -> str:
    """Generates a recipe using a list of provided ingredients via an LLM.

    Args:
        ingredients: A list of strings, where each string is an ingredient
                     (e.g., ["chicken breast", "rice", "broccoli"]).
        model: The LLM model to use for generation (default: "gpt-4o-mini").

    Returns:
        A string containing the generated recipe. If an error occurs during
        the LLM call, an error message string is returned.
    """
    if not ingredients:
        return "Error: No ingredients provided."

    ingredients_list_str = ", ".join(ingredients)
    system_prompt = (
        "You are a culinary assistant. Generate a clear, step-by-step recipe based on the provided ingredients."
        "Include preparation time, cooking time, number of servings, and nutritional information if possible."
        "If any crucial ingredient seems missing for a coherent recipe, you can suggest adding it."
    )
    user_prompt = f"Generate a recipe using the following ingredients: {ingredients_list_str}."

    try:
        response = completion(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling LLM for recipe generation: {e}"


def translate_text_with_llm(text: str, source_language: str, target_language: str, model: str = "gpt-4o-mini") -> str:
    """Translates text from a source language to a target language using an LLM.

    Args:
        text: The text to be translated.
        source_language: The source language of the text (e.g., "English", "Spanish", "auto" for auto-detect).
        target_language: The target language for translation (e.g., "French", "German").
        model: The LLM model to use for translation (default: "gpt-4o-mini").

    Returns:
        A string containing the translated text. If an error occurs,
        an error message string is returned.
    """
    if not text.strip():
        return "Error: No text provided for translation."

    system_prompt = "You are a highly proficient multilingual translator."
    user_prompt = f"Translate the following text from {source_language} to {target_language}:\n\n---\n{text}\n---"
    if source_language.lower() == "auto":
        user_prompt = (
            f"Detect the language of the following text and then translate it to {target_language}:\n\n---\n{text}\n---"
        )

    try:
        response = completion(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling LLM for translation: {e}"


def summarize_text_with_llm(text: str, summary_length: str = "a concise paragraph", model: str = "gpt-4o-mini") -> str:
    """Summarizes a given text using an LLM.

    Args:
        text: The text to be summarized.
        summary_length: A description of the desired summary length or style
                        (e.g., "a concise paragraph", "three key bullet points",
                        "approximately 100 words"). Defaults to "a concise paragraph".
        model: The LLM model to use for summarization (default: "gpt-4o-mini").

    Returns:
        A string containing the summary. If an error occurs,
        an error message string is returned.
    """
    if not text.strip():
        return "Error: No text provided for summarization."

    system_prompt = (
        "You are an expert summarizer, skilled in extracting key information and presenting it clearly and concisely."
    )
    user_prompt = (
        f"Summarize the following text. The desired summary style is: {summary_length}.\n\nText:\n---\n{text}\n---"
    )

    try:
        response = completion(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling LLM for summarization: {e}"


def combine_mp3_files_for_podcast(
    mp3_files: list[str], output_filename: str = "podcast.mp3", output_dir: str = "podcasts"
) -> str:
    """Combines a list of MP3 audio files into a single MP3 podcast file using ffmpeg.

    This function requires ffmpeg to be installed and accessible in the system's PATH.
    It creates a temporary file list for ffmpeg's concat demuxer.

    Args:
        mp3_files: A list of absolute or relative paths to the MP3 files to be combined.
                   The order in the list determines the order in the output file.
        output_filename: The name for the combined output MP3 file.
                         Defaults to "podcast.mp3".
        output_dir: The directory where the combined podcast file will be saved.
                    Defaults to "podcasts". Created if it doesn't exist.

    Returns:
        The absolute path to the combined podcast MP3 file if successful.
        Returns an error message string if ffmpeg fails or an error occurs.
    """
    if not mp3_files:
        return "Error: No MP3 files provided for combination."

    for f_path in mp3_files:
        if not Path(f_path).exists():
            return f"Error: Input file not found: {f_path}"

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_filepath = Path(output_dir) / output_filename

    # Create a temporary file list for ffmpeg
    list_filename = f"ffmpeg_list_{uuid.uuid4().hex}.txt"
    try:
        with Path(list_filename).open("w", encoding="utf-8") as f:
            for mp3_file in mp3_files:
                # ffmpeg's concat demuxer requires 'file' directive and paths to be escaped or simple.
                # Using absolute paths and -safe 0 is generally more robust.
                abs_mp3_file = Path(mp3_file).resolve()
                f.write(f"file '{abs_mp3_file}'\n")

        # Construct and run the ffmpeg command
        # -y: overwrite output without asking
        # -f concat: use the concat demuxer
        # -safe 0: allow unsafe file paths (needed for absolute paths in list file)
        # -c copy: copy audio stream without re-encoding (fast, preserves quality)
        command = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_filename,
            "-c",
            "copy",
            str(Path(output_filepath).resolve()),
        ]

        process = subprocess.run(command, capture_output=True, text=True, check=False)

        if process.returncode != 0:
            return f"Error combining MP3 files with ffmpeg: {process.stderr}"

        return str(Path(output_filepath).resolve())

    except FileNotFoundError:
        return "Error: ffmpeg command not found. Please ensure ffmpeg is installed and in your PATH."
    except Exception as e:
        return f"An unexpected error occurred during MP3 combination: {e}"
    finally:
        # Clean up the temporary list file
        if Path(list_filename).exists():
            Path(list_filename).unlink()


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


def generate_podcast_script_with_llm(document_text: str, num_hosts: int = 2, model: str = "gpt-4o-mini") -> str:
    """Writes a podcast script from a given text document using an LLM.
    The number of hosts/speakers in the podcast can be specified.

    Args:
        document_text: The text content to be transformed into a podcast script.
        num_hosts: The number of hosts/speakers for the podcast script (e.g., 1, 2, 3).
                   Defaults to 2.
        model: The LLM model to use for script generation (default: "gpt-4o-mini").

    Returns:
        A string containing the generated podcast script.
        Returns an error message string if an error occurs.
    """
    if not document_text.strip():
        return "Error: No document text provided for script generation."
    if not isinstance(num_hosts, int) or num_hosts <= 0:
        return "Error: Number of hosts must be a positive integer."

    system_prompt = "You are a creative scriptwriter specializing in engaging podcast dialogues. Your task is to convert the provided document into a podcast script."
    user_prompt = (
        f"Generate a podcast script based on the following document. "
        f"The script should feature {num_hosts} distinct hosts. "
        f"Clearly label each host's lines (e.g., Host 1:, Host 2:, etc., or Speaker A:, Speaker B:). "
        f"Make the conversation natural, engaging, and informative, covering the key points of the document. "
        f"Include an introduction and an outro if appropriate.\n\n"
        f"Document:\n---\n{document_text}\n---"
    )

    try:
        response = completion(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling LLM for podcast script generation: {e}"


def generate_database_query_with_llm(
    natural_language_request: str,
    database_schema: str | None = None,
    database_type: str = "SQL",
    model: str = "gpt-4o-mini",
) -> str:
    """Constructs database queries (e.g., SQL) based on natural language requests using an LLM.

    Args:
        natural_language_request: The user's request in natural language
                                  (e.g., "Show me all customers from California").
        database_schema: An optional string describing the database schema
                         (e.g., DDL statements, table and column descriptions).
                         Providing this helps generate more accurate queries.
        database_type: The type of database query to generate (e.g., "SQL", "NoSQL-MongoDB").
                       Defaults to "SQL".
        model: The LLM model to use for query generation (default: "gpt-4o-mini").

    Returns:
        A string containing the generated database query.
        Returns an error message string if an error occurs.
    """
    if not natural_language_request.strip():
        return "Error: No natural language request provided."

    system_prompt = f"You are an expert in generating {database_type} queries from natural language. Pay close attention to the provided schema if available."

    schema_info_prompt = ""
    if database_schema and database_schema.strip():
        schema_info_prompt = f"\n\nUse the following database schema as a reference:\n---\n{database_schema}\n---"
    else:
        schema_info_prompt = "\n\nNo specific database schema was provided. Make reasonable assumptions if necessary, or state if the query cannot be formed without a schema."

    user_prompt = (
        f"Generate a {database_type} query for the following natural language request: "
        f"'{natural_language_request}'."
        f"{schema_info_prompt}"
    )

    try:
        response = completion(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        )
        # LLMs might wrap the query in markdown, try to extract it
        content = response.choices[0].message.content
        if f"```{database_type.lower()}" in content:
            query = content.split(f"```{database_type.lower()}")[1].split("```")[0].strip()
            return query
        elif "```sql" in content:  # common fallback for SQL
            query = content.split("```sql")[1].split("```")[0].strip()
            return query
        elif "```" in content:  # generic code block
            query = content.split("```")[1].split("```")[0].strip()
            # Check if it's likely a query, otherwise return full content
            if any(kw in query.upper() for kw in ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "FROM", "WHERE"]):
                return query
        return content  # Return full content if no clear code block found or simple response
    except Exception as e:
        return f"Error calling LLM for database query generation: {e}"


def review_code_with_llm(code: str, language: str, model: str = "gpt-4o-mini") -> str:
    """Reviews a given piece of code for errors, bugs, security issues, and style violations using an LLM.

    Args:
        code: The source code string to be reviewed.
        language: The programming language of the code (e.g., "python", "javascript", "java").
        model: The LLM model to use for code review (default: "gpt-4o-mini").

    Returns:
        A string containing the code review feedback.
        Returns an error message string if an error occurs.
    """
    if not code.strip():
        return "Error: No code provided for review."
    if not language.strip():
        return "Error: Programming language not specified for the code."

    system_prompt = (
        "You are an expert code reviewer. "
        "Analyze the given code meticulously for errors, bugs, potential security vulnerabilities, "
        "and style violations according to best practices for the specified language. "
        "Provide constructive feedback and actionable suggestions for improvement."
    )
    user_prompt = (
        f"Please review the following {language} code. "
        f"Provide a comprehensive review covering:\n"
        f"1. Errors and Bugs: Identify any logical or syntactical errors.\n"
        f"2. Security Vulnerabilities: Point out potential security risks (e.g., injection flaws, data exposure).\n"
        f"3. Style Violations: Comment on adherence to common style guides for {language} (e.g., PEP 8 for Python).\n"
        f"4. Best Practices & Performance: Suggest improvements for readability, maintainability, and efficiency.\n"
        f"Format your review clearly, perhaps using sections or bullet points for each category.\n\n"
        f"Code:\n"
        f"```{language}\n"
        f"{code}\n"
        f"```"
    )

    try:
        response = completion(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling LLM for code review: {e}"
