# Installation

This guide covers how to install and set up Agent Factory.

## Prerequisites

Before installing Agent Factory, ensure you have the following prerequisites:

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
