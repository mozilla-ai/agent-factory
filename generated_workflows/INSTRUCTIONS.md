# Instructions to Run the Sushi Restaurant Agent

This project uses the [any-agent](https://mozilla-ai.github.io/any-agent/) library to search for the best sushi restaurant in Berlin using an OpenAI-based agent with structured output.

## Requirements

- Python 3.9+
- Install dependencies:
  - any-agent
  - pydantic
  - (For OpenAI, you may need environment variables for authentication)

Install via pip (modify as needed):
```sh
pip install 'pydantic>=2' any-agent
```

## Setup

If required, set your OpenAI API key (if not already configured):
```sh
export OPENAI_API_KEY=sk-...yourkey...
```

## Running the Agent

1. Make sure you are in the project directory.
2. Run the agent script:

```sh
python agent.py
```

The agent will search for the best sushi restaurant in Berlin and print a structured output (Pydantic model with top choice and alternatives).

## Output

The result will be printed as an instance of the `RestaurantResults` Pydantic model, for example:

```
best_restaurant=RestaurantInfo(name='Sushi XYZ', rating=4.7, address='Alexanderplatz 1, 10178 Berlin', description='Trendy spot with authentic omakase.', url='https://sushi-xyz.de') alternatives=[...]
```

## Customization

- You can modify the `model_id` or prompt/instructions in `agent.py` to adjust the agent's behavior or use a different LLM model.
