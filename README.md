# Agent Factory
A tool for generating Python code for agentic workflows using `any-agent` library. Describe your workflow in natural language, and the agent will generate the necessary code to implement that workflow using available tools (Python functions or via MCP servers). Think of it as "[Lovable](https://lovable.dev/) for building agentic workflows".

## Key Capabilities

- Generate Python code for agentic workflows from natural language prompts
- Automatically create runnable agents and instructions using the `any-agent` library and available tools
- (Manually) Execute generated workflows save agent trace
- Generate evaluation cases and JSON configs for automated testing
- (Manually) Run automated evaluations and view detailed criteria-based results

## Setup

### Option A: GitHub Codespaces

[![Try on Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=984695018&skip_quickstart=true&machine=standardLinux32gb&geo=EuropeWest&devcontainer_path=.devcontainer%2Fdevcontainer.json)


Activate the virtual environment. All the dependencies are preinstalled for this codespaces demo, but it's recommended to run all commands below to ensure everything it's up to date (and also, to activate the virtual env!)

```bash
source .venv/bin/activate
uv sync --dev
```
### Option B: Local installation

#### Prerequisites:
- Python 3.11 or higher
- Docker should be up and running in the background (for filesystemMCP operations) - download and install [from here](https://www.docker.com/products/docker-desktop)

Install dependencies using your preferred Python package manager:

```bash
uv venv
source .venv/bin/activate
uv sync --dev
uv pip install -e .
```

Install pre-commit hooks:

```bash
pre-commit install
```

## Getting Started

Follow these steps to generate, run, trace, and evaluate an agentic workflow:

Before running the agent factory, you need to set up your OpenAI API key (required):
> Set it as an environment variable:
> ```bash
> export OPENAI_API_KEY=sk-...
> ```

You will need a Tavily API key to use the `search_tavily` tool. You can get a free API key by signing up at [Tavily](https://app.tavily.com/).
> Set it as an environment variable:
> ```bash
> export TAVILY_API_KEY=tvly_...
> ```

> [!TIP]
> If you do not want to create an API key for web search, you can specify in your workflow definition that you want to use DuckDuckGo as the search tool (e.g., "use DuckDuckGo for web search"). This does not require an API key. However, please note that for complex workflows, you may hit the cap of searches per minute with DuckDuckGo.

### 1. Generate the workflow


Run the agent-factory with your desired workflow prompt:

```bash
agent-factory "Summarize text content from a given webpage URL" "generated_workflows/latest"
```

This will generate Python code for an agentic workflow that can summarize text content from a given webpage URL. The generated code will be saved in the `generated_workflows/latest` directory.
The three files generated are:

1. `agent.py`: The Python code for the agentic workflow
2. `INSTRUCTIONS.md`: Setup and run instructions for the generated workflow
3. `requirements.txt`: Python dependencies required to run the agent

> [!NOTE]
> You might need to add additional API keys, depending on the generated agent and the tools it uses, for example if it uses the elevenlabs-mcp:

> Set it as an environment variable:
> ```bash
> export ELEVENLABS_API_KEY=sk_...
> ```

### 2. Run the Generated Workflow

Note: The generated agent.py will reference tools from tools/ directory. Hence, you would need to run the agent from the root directory as:

```bash
uv run --with-requirements generated_workflows/latest/requirements.txt --python 3.11 python generated_workflows/latest/agent.py --arg1 "value1"
```

This will run the agent and save the agent trace as `agent_eval_trace.json` in the `generated_workflows/latest` directory.

> [!NOTE]
> The agent-factory has been instructed to set the `max_turns` (the max number of steps that the generated agent can take to complete the workflow) to 20. Please inspect the generated agent code and override this value if needed (if you see the generated agent run failing due to `AgentRunError` caused by `MaxTurnsExceeded`).

### 3. Generate Evaluation Case JSON

Run the evaluation case generator agent with your desired evaluation case prompt:
```bash
python -m eval.generate_evaluation_case
```

This will generate a JSON file in the `generated_workflows/latest` directory with evaluation criteria.

### 4. Run Evaluation Script

Evaluate the agent's execution trace against the generated evaluation case:

```bash
python -m eval.run_generated_agent_evaluation
```
This will display the evaluation criteria and show how the agent performed on each.


## How to run the API

See detailed instructions in [api/README.md](api/README.md).

## How to run the UI

See detailed instructions in [ui/README.md](ui/README.md).

## Multi-turn Agent Building with Chainlit

You can interact with the agent-factory using [Chainlit](https://docs.chainlit.io/get-started/overview) for multi-turn conversations:

A sample Chainlit app is provided in `src/agent_factory/chainlit_playground.py` for interactive workflow building and testing. It uses any-agent under the hood to generate the agent code.

To launch the Chainlit UI for your agent workflow, run:
```bash
uv sync --group chainlit-demo
chainlit run src/agent_factory/chainlit_playground.py
# or for interactive mode - to hot reload the app on code changes
chainlit run src/agent_factory/chainlit_playground.py - w
```

This will start a local web server on `http://localhost:8000`. Open the URL in your browser to interact with your agent in a chat-like interface.

## Sample Agents: Manual End-to-End Regression Tests

The [`sample_agents/`](sample_agents/) folder contains end-to-end example scripts that serve as manual regression tests for the Agent Factory system. Each script demonstrates the full workflow: from generating an agent based on a natural language prompt, to running the generated agent in a clean, isolated environment. See [`sample_agents/README.md`](sample_agents/README.md) for details on their purpose, usage, and how they help ensure the reliability of agent generation and execution.

## License

See the [LICENSE](LICENSE) file for details.
