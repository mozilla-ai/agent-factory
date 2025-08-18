from any_llm import completion


def translate_text_with_llm(
    text: str, source_language: str, target_language: str, model: str = "openai/gpt-4o-mini"
) -> str:
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
