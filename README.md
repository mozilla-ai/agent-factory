# Agent Factory

Agent Factory is an **Agent2Agent (A2A) protocol-compatible server** designed to simplify agent creation and management.
Describe your workflow in natural language, and the agent will generate the necessary code to implement that workflow
using available tools (Python functions or via MCP servers).

Under the hood, it leverages the [`any-agent`](https://github.com/mozilla-ai/any-agent) library, allowing you to easily
swap between Agent frameworks without any code changes.

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

6. If you plan to use the `search_tavily` tool, set up your Tavily API key (optional):
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
> Currently, any-agent supports the following frameworks:
> - `google`
> - `langchain`
> - `llama_index`
> - `openai`
> - `agno`
> - `smolagents`
> - `tinyagent`

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
agent-factory "Summarize text content from a given webpage URL"
```

The client will send the message to the server, print the response, and save the generated agent's files (`agent.py`,
`README.md`, and `requirements.txt`) into a new directory inside the `generated_workflows` directory.

### Run the Generated Workflow

To run the generated agent, navigate to the directory where the agent was saved and execute:

```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py"
```

This will start an A2A protocol-compatible server that can handle requests from other agents. By default, it will run on
`http://localhost:8000`. You can also specify the host and port using the `--host` and `--port` flags:

```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py --host 0.0.0.0 --port 8081
```

Invoke the agent using the following command:

```bash
curl -X POST http://localhost:8081 \
  -H "Content-Type: application/json" \
  -d '{
      "jsonrpc": "2.0",
      "method": "message/send",
      "id": "$(uuidgen)",
      "params": {
          "message": {
              "messageId": "$(uuidgen)",
              "role": "user",
              "parts": [
                  {
                      "kind": "text",
                      "text": "Summarize the content of https://www.mozilla.ai/"
                  }
              ]
          }
      }
  }' | jq -r '.result.status.message.parts[0].text | fromjson | .summary'
```
## License

See the [LICENSE](LICENSE) file for details.
