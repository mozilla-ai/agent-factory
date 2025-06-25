from openai import OpenAI

from backend.templates import PYPROJECT_PROMPT, PYPROJECT_TEMPLATE, README_PROMPT, README_TEMPLATE

client = OpenAI()


def completion(prompt: str, model: str = "gpt-4o") -> str | None:
    """Generate a completion for the given prompt using the specified model."""
    try:
        chat_completion = client.chat.completions.create(
            model=model,  # Specify the model you want to use
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        if chat_completion.choices:
            return chat_completion.choices[0].message.content
        else:
            return "No response received from the model."
    except Exception as e:
        return f"An error occurred: {e}"


def create_agent_file(file_type: str, python: str) -> str:
    if file_type == "readme":
        user_prompt = README_PROMPT.format(python_code=python, readme_template=README_TEMPLATE)
        model_response = completion(user_prompt)
    elif file_type == "toml":
        user_prompt = PYPROJECT_PROMPT.format(python_code=python, pyproject_template=PYPROJECT_TEMPLATE)
        model_response = completion(user_prompt)

    if not model_response:
        raise ValueError("No response received from the model.")
    return model_response
