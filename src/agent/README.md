# Agent Factory

Agent Factory is an **Agent2Agent protocol-compatible server** designed to simplify agent creation and management. It
leverages the [`any-agent`](https://github.com/mozilla-ai/any-agent) library, allowing you to easily swap between Agent
frameworks without any code changes.

## Key Capabilities

* **Natural Language to Code:** Transform natural language prompts directly into executable Python code for agentic
  workflows, powered by the `any-agent` library.
* **Smart Tooling & Integration:** Automatically identify the most relevant tools or MCP servers for your generated
  agents.
* **Automated Agent Deployment:** Effortlessly create runnable agents complete with their operational instructions and
  dependency files.

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)
- Docker (for containerized deployment)

### Installation

1. Clone the repository and navigate to the agent's source directory:
   ```bash
   git clone https://github.com/mzai/agent-factory.git
   cd agent-factory/src/agent
   ```

2. Install the dependencies using `uv`:
   ```bash
   uv sync
   ```

3. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

### Running the Server

You can run the server either locally or using Docker.

#### Locally

To run the server locally, execute the following command from the `src/agent` directory:

```bash
uv run --active . --host 0.0.0.0 --port 8080
```

The server will be available at `http://localhost:8080`.

In addition to `host` and `port`, you can also pass the following arguments:

-   `framework`: The Agent framework to use (default: `openai`).
-   `model`: The model ID to use (default: `o3`).
-   `log_level`: The logging level (default: `info`).

> [!NOTE]
> Currently, any-agent supports the following frameworks:
> - `google`
> - `langchain`
> - `llama_index`
> - `openai`
> - `agno`
> - `smolagents`
> - `tinyagent`

#### Using Docker

1.  From the `src/agent` directory, build the Docker image:
    ```bash
    docker build -t agent-factory .
    ```

2.  Run the Docker container, setting the environment variables as needed:
    ```bash
    docker run -p 8080:8080 \
        -e FRAMEWORK=openai \
        -e MODEL=o3 \
        -e LOG_LEVEL=info \
        agent-factory
    ```

The server will be available at `http://localhost:8080`.

> [!NOTE]
> You can pass all the same arguments as when running locally, but they should be set as environment variables.

### Testing the Server

Once the server is running, you can use the `test_client.py` script to send a message to the agent.

```bash
uv run --active test_client.py "Summarize the contents of a web page given the URL."
```

The client will send the message to the server, print the response, and save the generated agent's files (`agent.py`,
`INSTRUCTIONS.md`, and `requirements.txt`) into a new directory inside the `generated_workflows` directory.
