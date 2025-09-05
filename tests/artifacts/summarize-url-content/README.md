# Webpage Summarizer Agent

A simple agent that fetches any public webpage and returns a concise 4-6 sentence summary of its main content.

# Prerequisites

- uv

## Install uv

- **macOS / Linux**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
- **Windows PowerShell**
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

# Configuration

Create a `.env` file with any required environment variables (e.g. `OPENAI_API_KEY` for the summarization tool).

# Run the Agent

```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py --url "https://example.com"
```
