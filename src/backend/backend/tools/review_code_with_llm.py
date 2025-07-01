from litellm import completion


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
