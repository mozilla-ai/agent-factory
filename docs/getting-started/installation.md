## Prerequisites

- [Python 3.13+](https://www.python.org/downloads/) (will be automatically installed by `uv`)
- [uv](https://github.com/astral-sh/uv) (easily manage Python environments and agents' dependencies)
- [mcpd](https://github.com/mozilla-ai/mcpd) (interface to manage and run MCP servers)
- **(Optional)** [Docker](https://www.docker.com/products/docker-desktop/) (for containerized server deployment)

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

4. Create a `.env` file in the project root directory and add your OpenAI API key and Tavily API key (required). You can get a free Tavily API key by signing up [here](https://www.tavily.com/).
   ```bash
   OPENAI_API_KEY=sk-...
   TAVILY_API_KEY=tvly_...
   ```

5. (Only required if you are developing the library) Install pre-commit hooks:
   ```bash
   pre-commit install
   ```
