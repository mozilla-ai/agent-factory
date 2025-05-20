# Agentic Workflow Builder

A tool for generating Python code for agentic workflows using `any-agent` library. Describe your workflow in natural language, and the agent will generate the necessary code to implement that workflow using available tools (Python functions or via MCP servers).

## Features

- Generate Python code from natural language, that implements an agentic workflow adhering to any-agent library
- Utilize any-agent library (search_web, visit_webpage, etc.) and available tools from tools/available_tools.md
- Automatically generate appropriate agent configurations
- Generates run instructions for the generated workflow

## Installation

### Prerequisites

- Python 3.11 or higher
- Docker should be up and running in the background (for filesystem operations)

### Setup

1. Install dependencies using your preferred Python package manager:
   ```bash
   uv pip install -e .
   source .venv/bin/activate
   ```

2. Install pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

3. Set your OpenAI API key (required):
   ```bash
   export OPENAI_API_KEY=sk-...
   ```

## Usage

Run the main script with your prompt as an argument:

```bash
python -m src.main "Summarize text content from a given webpage URL"
```

This will generate Python code for an agentic workflow that can summarize text content from a given webpage URL. The generated code will be saved in the `generated_workflows/` directory. The two files generated are:

1. `agent.py`: The Python code for the agentic workflow
2. `INSTRUCTIONS.md`: Setup and run instructions for the generated workflow

Note: The generated agent.py will reference tools from tools/ directory. Hence, you would need to run the agent as:
```bash
python generated_workflows/agent.py arg1
```

## License

See the [LICENSE](LICENSE) file for details.
