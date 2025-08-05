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
* **Multi-Turn and One-Shot Workflows:** Support for both multi-turn conversations and one-shot tasks, enabling flexible
  interaction patterns.

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

5. Create a `.env` file in the project root and add your OpenAI API key and Tavily API key (required). You can get a free Tavily API key by signing up [here](https://www.tavily.com/).
   ```bash
   OPENAI_API_KEY=sk-...
   TAVILY_API_KEY=tvly_...
   ```

### Run the Server

You can run the server either locally or using Docker.

#### Locally

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

#### Using Docker

The Makefile enables you to run the server using Docker. Before starting, make sure that [Docker Desktop](https://www.docker.com/products/docker-desktop/) is installed and running.

**Run the server** (this will also build the image if needed):
   ```bash
   make run
   ```
   The server will be available at `http://localhost:8080/.well-known/agent.json`.

> [!NOTE]
> You can modify the behavior of the server by passing environment variables to the `make run` command. For example, to
> run the server with the `tinyagent` framework and a specific model, in chat mode, you can use:
> ```bash
> make run FRAMEWORK=tinyagent MODEL=mistral/mistral-small-latest CHAT=1
> ```

> [!NOTE]
> After generating your agents using the `agent-factory` command (described below), don't forget to stop the server using:
> ```bash
> make stop
> ```

### (Optional) Setting Up Storage Backends

By default, agent outputs are **saved to the local filesystem**. You can configure the agent factory to use AWS S3 or a local MinIO instance for storage.

#### S3 & MinIO Configuration

To customize the S3/MinIO configuration, you can create a `.env` file in the project root and override the following values from `.default.env`:

-   `STORAGE_BACKEND`: Set to `s3` for AWS S3 or `minio` for MinIO.
-   `AWS_ACCESS_KEY_ID`: Your AWS or MinIO access key.
-   `AWS_SECRET_ACCESS_KEY`: Your AWS or MinIO secret key.
-   `AWS_DEFAULT_REGION`: The AWS region for your S3 bucket.
-   `S3_BUCKET`: The name of the S3 or MinIO bucket.
-   `AWS_ENDPOINT_URL`: **(For MinIO only)** The URL of your MinIO instance (e.g., `http://localhost:9000`).

When using these settings, the application will automatically create the specified bucket if it does not already exist.

#### Running a Local MinIO Instance

If you do not have access to AWS S3, you can run a local MinIO instance using Docker:

```bash
docker run -p 9000:9000 -p 9091:9091 \
  --name minio-dev \
  -e "MINIO_ROOT_USER=agent-factory" \
  -e "MINIO_ROOT_PASSWORD=agent-factory" \
  quay.io/minio/minio server /data --console-address ":9091"
```

Once the container is running, you can access the MinIO console at `http://localhost:9091`.

### Generate an Agentic Workflow




> [!IMPORTANT]
> Always run the server in non-chat mode (`--nochat`) when generating agents using the `agent-factory` command.
> For multi-turn conversations, see the section on [Multi-Turn Conversations](#multi-turn-conversations).

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

## Multi-Turn Conversations

Agent Factory supports multi-turn conversations. You can run the Chainlit application to interact with the Agent server
in a conversational manner:

```bash
uv run chainlit run src/agent_factory/chainlit.py
```

## License

See the [LICENSE](LICENSE) file for details.
