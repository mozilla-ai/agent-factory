# Sushi in Berlin Agent: Setup & Running Guide

This agent helps you discover the best sushi restaurant in Berlin using Mozilla's [any-agent](https://github.com/mozilla-ai/any-agent) library with the OpenAI framework, web search, and structured output.

---

## **Requirements**

- Python 3.9+
- pip (Python package manager)
- OpenAI API key (for access to GPT-4.1)
- (Recommended) Virtual environment

---

## **Dependencies Installation**

1. **Clone or copy the generated files**

2. **Create a virtual environment (recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install the required packages:**

    ```bash
    pip install any-agent pydantic
    ```

    If you don’t have any-agent installed yet,
    you might need to install it from source or GitHub per official docs:
    ```bash
    pip install 'git+https://github.com/mozilla-ai/any-agent.git'
    ```

    > **Note:** Ensure you have the latest `pydantic` (v2). If unsure, run:
    > `pip install --upgrade pydantic`

4. **Set your OpenAI API key (required):**

    ```bash
    export OPENAI_API_KEY=sk-...   # Replace with your actual key
    ```
    Or on Windows:
    ```cmd
    set OPENAI_API_KEY=sk-...
    ```

---

## **How to Run the Agent**

From within the `/app/generated_workflows/` directory, run:

```bash
python agent.py
```

- The script will print a structured JSON summary of Berlin’s best sushi restaurant, with justification and sources.

---

## **Customization / Notes**
- To change the task or search target, edit the main prompt in `agent.py` or modify the step-by-step `INSTRUCTIONS`.
- The agent uses both `search_web` and `visit_webpage` for optimal factual accuracy.
- Output structure is controlled by the `RestaurantInfo` Pydantic model.
- If you want to see execution traces, or further debug, check [any-agent tracing documentation](https://mozilla-ai.github.io/any-agent/tracing/).

---

## **Documentation References**
- [AnyAgent API Docs](https://mozilla-ai.github.io/any-agent/agents/)
- [Tools Reference](https://mozilla-ai.github.io/any-agent/tools/)
- [OpenAI Framework Config](https://mozilla-ai.github.io/any-agent/frameworks/openai/)

---

Enjoy finding the best sushi in Berlin!
