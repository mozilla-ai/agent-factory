# Run Instructions for agent.py

## Setup
1. Ensure you have Python 3.9+ installed.
2. Install dependencies (you may wish to use a virtual environment):

```
pip install any-agent[openai] pydantic
```
- You must also have access to the OpenAI API (set your `OPENAI_API_KEY` environment variable).

## Running the Code

From the root directory, run:

```
python agent.py
```

The agent will search for the best sushi restaurant in Berlin and print the structured results to the console.
