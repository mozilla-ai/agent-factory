# Installation

## Prerequisites

- [curl](https://curl.se/)
- [jq](https://jqlang.org/)
- [Python 3.13+](https://www.python.org/downloads/)
- [uv](https://github.com/astral-sh/uv)
- [Docker](https://www.docker.com/products/docker-desktop/) (for containerized deployment)
- [mcpd](https://github.com/mozilla-ai/mcpd/releases) added to `PATH`, e.g. `/usr/local/bin` (for local deployment)

## Installation

1. Clone the repository and navigate to the agent's source directory:
   ```bash
   git clone https://github.com/mozilla-ai/agent-factory.git && cd agent-factory
   ```

2. Install the dependencies using `uv`:
   ```bash
   uv sync --dev
   ```

3. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

5. Create a `.env` file in the project root and add your OpenAI API key and Tavily API key (required). You can get a free Tavily API key by signing up [here](https://www.tavily.com/).
   ```bash
   OPENAI_API_KEY=sk-...
   TAVILY_API_KEY=tvly_...
   ```

## Run the Server

To run the server locally, execute the following command from the `src/agent_factory` directory:

```bash
cd src/agent_factory && uv run . --host 0.0.0.0 --port 8080
```

The server will be available at `http://localhost:8080/.well-known/agent.json`.

In addition to `host` and `port`, you can also pass the following arguments:

-  `chat` vs `nochat`: `chat` mode enables multi-turn conversations, while `nochat` mode is for one-shot tasks (default:
   `chat`).
-  `framework`: The Agent framework to use (default: `openai`).
-  `model`: The model ID to use (default: `o3`).
-  `log_level`: The logging level (default: `info`).

> [!NOTE]
> Visit the any-agent [documentation](https://mozilla-ai.github.io/any-agent/) for more details on the supported
> frameworks.

## Generate an Agentic Workflow

> [!IMPORTANT]
> Always run the server in non-chat mode (`--nochat`) when generating agents using the `agent-factory` command.
> For multi-turn conversations, see the section on [Multi-Turn Conversations](#multi-turn-conversations).

Once the server is running, run the `agent-factory` CLI tool with your desired workflow prompt:

```bash
uv run agent-factory "Summarize text content from a given webpage URL"
```

The client will send the message to the server, print the response, and save the generated agent's files (`agent.py`,
`README.md`, `requirements.txt`, and `agent_parameters.json`) into a new directory inside the `generated_workflows` directory.

## Run the Generated Workflow

To run the generated agent, navigate to the directory where the agent was saved and execute:

```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py --arg1 "value1"
```

Replace `--arg1 "value1"` with the actual arguments required by the generated agent. The command will execute the agent
and save the agent trace as `agent_trace.json` in the agent's directory.

> [!NOTE]
> You can append the `--help` flag to the command to see the available options for the generated agent.

> [!NOTE]
> The agent-factory has been instructed to set the max_turns (the max number of steps that the generated agent can take
> to complete the workflow) to 20. Please inspect the generated agent code and override this value if needed (if you see
> the generated agent run failing due to AgentRunError caused by MaxTurnsExceeded).

## Evaluate the Generated Agent

Run the evaluation case generator agent with your desired evaluation case prompt:

```bash
uv run -m eval.generate_evaluation_case path/to/the/generated/agent
```

This will generate a JSON file in the generated agent's directory with evaluation criteria. Next, evaluate the agent's
execution trace against the generated evaluation case:

```bash
uv run -m eval.run_generated_agent_evaluation path/to/the/generated/agent
```

This command will display the evaluation criteria and show how the agent performed on each.

## Multi-Turn Conversations

Agent Factory supports multi-turn conversations. You can run the Chainlit application to interact with the Agent server
in a conversational manner:

```bash
uv run chainlit run src/agent_factory/chainlit.py
```
