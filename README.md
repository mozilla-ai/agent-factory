# Agent Factory

Agent Factory is an **Agent2Agent (A2A) protocol-compatible server** designed to simplify agent creation and evaluation.
Describe your workflow in natural language, and the agent will generate the necessary code to implement that workflow
using available tools (Python functions or via MCP servers).

Under the hood, it leverages the [`any-agent`](https://github.com/mozilla-ai/any-agent) library, allowing you to easily
swap between Agent frameworks with minimal code changes.

## Key Capabilities

* **Natural Language to Code:** Transform natural language prompts directly into executable Python code for agentic
  workflows, powered by the `any-agent` library.
* **Smart Tooling & Integration:** Automatically identify the most relevant tools or MCP servers for your generated
  agents.
* **Agent Execution:** Effortlessly create runnable agents complete with their operational instructions and dependency
  files.
* **Agent Evaluation:** Evaluate the generated agents against automatically or manually defined criteria to ensure they
  meet the desired performance standards.

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)
- Docker (for containerized deployment)

### Installation

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

5. Set up your OpenAI API key (required):
   ```bash
   export OPENAI_API_KEY=sk-...
   ```

6. Set up your [Tavily](https://www.tavily.com/) API key (required):
   ```bash
   export TAVILY_API_KEY=tvly_...
   ```

> [!NOTE]
> Alternatively, you can create a `.env` file in the project root with your keys. This is the recommended approach.

### Run the Server

You can run the server either locally or using Docker.

#### Locally

To run the server locally, execute the following command from the `src/agent_factory` directory:

```bash
cd src/agent_factory && uv run . --host 0.0.0.0 --port 8080
```

The server will be available at `http://localhost:8080`.

In addition to `host` and `port`, you can also pass the following arguments:

-   `framework`: The Agent framework to use (default: `openai`).
-   `model`: The model ID to use (default: `o3`).
-   `log_level`: The logging level (default: `info`).

> [!NOTE]
> Visit the any-agent [documentation](https://mozilla-ai.github.io/any-agent/) for more details on the supported
> frameworks.

#### Using Docker

To run the server in a Docker container, follow these steps.

1.  **Build the Docker image:**

    From the root of the project, run the following commands to build the Docker image:

    ```bash
    export VER=$(git describe --tags --dirty)
    docker build --build-arg APP_VERSION=$VER  -t agent-factory .
    ```

2.  **Run the Docker container:**

    Create a `.env` file in the project root with your `OPENAI_API_KEY`:

    ```
    OPENAI_API_KEY=sk-...
    ```

    Then, run the container, passing the `.env` file:

    ```bash
    docker run --rm -p 8080:8080 --env-file .env agent-factory
    ```

    The server will be available at `http://localhost:8080`.

### Generate an Agentic Workflow

Once the server is running, run the `agent-factory` CLI tool with your desired workflow prompt:

```bash
uv run agent-factory "Summarize text content from a given webpage URL"
```

The client will send the message to the server, print the response, and save the generated agent's files (`agent.py`,
`README.md`, and `requirements.txt`) into a new directory inside the `generated_workflows` directory.

### Run the Generated Workflow

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

## License

See the [LICENSE](LICENSE) file for details.
