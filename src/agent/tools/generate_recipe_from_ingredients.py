from litellm import completion


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
