# Agent Factory
A tool for generating Python code for agentic workflows using `any-agent` library. Describe your workflow in natural language, and the agent will generate the necessary code to implement that workflow using available tools (Python functions or via MCP servers). Think of it as "[Lovable](https://lovable.dev/) for building agentic workflows".

## Key Capabilities

- Generate Python code for agentic workflows from natural language prompts
- Automatically create runnable agents and instructions using the `any-agent` library and available tools
- (Manually) Execute generated workflows save agent trace
- Generate evaluation cases and YAML configs for automated testing
- (Manually) Run automated evaluations and view detailed criteria-based results

## Setup

### Option A: GitHub Codespaces

[![Try on Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=984695018&skip_quickstart=true&machine=standardLinux32gb&geo=EuropeWest&devcontainer_path=.devcontainer%2Fdevcontainer.json)


Activate the virtual environment. All the dependencies are preinstalled for this codespaces demo, but it's recommended to run all commands below to ensure everything it's up to date (and also, to activate the virtual env!)
```bash
source .venv/bin/activate
uv pip install -e .
```
### Option B: Local installation

#### Prerequisites: 
- Python 3.11 or higher
- Docker should be up and running in the background (for filesystem operations)

Install dependencies using your preferred Python package manager:
```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

Install pre-commit hooks:
```bash
uv pip install pre-commit
pre-commit install
```

## Getting Started
Follow these steps to generate, run, trace, and evaluate an agentic workflow:

Before running the agent factory, you need to set up your OpenAI API key (required):
> Set it as an environment variable:
> ```bash
> export OPENAI_API_KEY=sk-...
> ```
You will need a Brave Search API key to use the `brave_web-search` tool. Create an account at [Brave Search](https://brave.com/search/api/) and obtain your API key.
> Set it as an environment variable:
> ```bash
> export BRAVE_API_KEY=BS...
> ```


### 1. Generate the workflow 
Run the code generator agent with your desired workflow prompt:
```bash
python -m src.main "Summarize text content from a given webpage URL"
```

This will generate Python code for an agentic workflow that can summarize text content from a given webpage URL. The generated code will be saved in the `generated_workflows/` directory.  The three files generated are:

1. `agent.py`: The Python code for the agentic workflow
2. `INSTRUCTIONS.md`: Setup and run instructions for the generated workflow
3. `requirements.txt`: Python dependencies required to run the agent

> [!NOTE]
> You might need to install the dependencies created for the agent, you can do it with:
>
> ```bash
> uv pip install -r generated_workflows/requirements.txt
> ```

> [!NOTE]
> You might also need to add additional api keys, depending on the generated agent and the tools it uses, for example if it uses the elevenlabs-mcp:

> Set it as an environment variable:
> ```bash
> export ELEVENLABS_API_KEY=sk_...
> ```

### 2. Run the Generated Workflow
Note: The generated agent.py will reference tools from tools/ directory. Hence, you would need to run the agent as:
```bash
python generated_workflows/latest/agent.py arg1
```
This will run the agent and save the agent trace as `agent_trace.json` in the `generated_workflows/` directory.

### 3. Generate Evaluation Case YAML
Run the evaluation case generator agent with your desired evaluation case prompt:
```bash
python -m eval.main
```

This will generate a YAML file in the `generated_workflows/` directory with criteria and points for each evaluation.

### 4. Run Evaluation Script
Evaluate the agent's execution trace against the generated evaluation case:
```bash
python -m eval.run_agent_eval
```
This will display the evaluation criteria and show how the agent performed on each.



## License

See the [LICENSE](LICENSE) file for details.
