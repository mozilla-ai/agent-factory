from litellm import completion


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

    system_prompt = (
        f"You are an expert in generating {database_type} queries from natural language."
        " Pay close attention to the provided schema if available."
    )

    schema_info_prompt = ""
    if database_schema and database_schema.strip():
        schema_info_prompt = f"\n\nUse the following database schema as a reference:\n---\n{database_schema}\n---"
    else:
        schema_info_prompt = (
            "\n\nNo specific database schema was provided. "
            "Make reasonable assumptions if necessary, or state if the query cannot be formed without a schema."
        )

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
