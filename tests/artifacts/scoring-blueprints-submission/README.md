# Blueprint Repository Evaluator Agent

An agent that automatically scores GitHub repositories against Mozilla AI Blueprint guidelines, reports the results to Slack, and logs them into a local SQLite database.

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

Create a `.env` file in the project root and add the following environment variables:

```
OPENAI_API_KEY=your_openai_key_here
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_TEAM_ID=T01234567
MCPD_ADDR=http://localhost:8090  # optional, defaults as shown
```

Additionally configure the SQLite MCP server to point at the local database:
```bash
mcpd config args set sqlite --runtime-file secrets.dev.toml -- --db-path=$(pwd)/blueprints.db
```

# Run the Agent

1. Start the mcpd daemon:
```bash
mcpd daemon --log-level=DEBUG --log-path=$(pwd)/mcpd.log --dev --runtime-file secrets.dev.toml
```

2. Execute the agent:
```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py --repo_url "https://github.com/owner/repo"
```
