from litellm import completion


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
