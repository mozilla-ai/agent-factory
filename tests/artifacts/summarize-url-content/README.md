# Webpage Summariser Agent

A single-step CLI agent that takes a webpage URL, extracts its textual content, and returns a concise summary in JSON form.

## Prerequisites

- **uv** – fast Python package manager
- **mcpd** – optional; the agent attempts to connect but does not rely on MCP tools

### Install **uv**
- macOS / Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
- Windows PowerShell
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install **mcpd**
Follow the official guide: <https://mozilla-ai.github.io/mcpd/installation/>

## Configuration

Create a `.env` file in the project root and add your OpenAI credentials:
```
OPENAI_API_KEY=sk-...
```
No other environment variables are required unless you wish to run `mcpd`.

## Run the Agent

1. (Optional) start the `mcpd` daemon if you use MCP servers for other purposes:
```bash
mcpd daemon --log-level=DEBUG --log-path=$(pwd)/mcpd.log --dev
```

2. Execute the agent:
```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py --url "https://example.com"
```
