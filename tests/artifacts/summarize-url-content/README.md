# Webpage Summarizer Agent

Generates a concise summary for any provided webpage URL using Mozilla's any-agent framework.

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

Set the environment variables in the `.env` file that has been created for you. Add other environment variables as needed, for example, environment variables for your LLM provider.

# Run the Agent

```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py --url "https://example.com"
```
