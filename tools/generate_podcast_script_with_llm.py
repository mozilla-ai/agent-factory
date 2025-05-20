from litellm import completion


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
