# Blueprint Evaluation Agent

Evaluates a GitHub repository against the Mozilla AI Blueprint guidelines, posts the score to Slack, and logs it to SQLite.

# Prerequisites

- uv
- mcpd

## Install uv

- **macOS / Linux**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
- **Windows PowerShell**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Install mcpd

Follow the mcpd installation instructions in the official documentation: https://mozilla-ai.github.io/mcpd/installation/

# Configuration

Set the environment variables in the `.env` file that has been created for you. Add other environment variables as needed, for example, environment variables for your LLM provider.

# Run the Agent

1. Run the mcpd daemon:
```bash
mcpd daemon --log-level=DEBUG --log-path=$(pwd)/mcpd.log --dev --runtime-file secrets.prod.toml
```

2. Run the agent:
```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py --repo_url "https://github.com/user/repo"
```
