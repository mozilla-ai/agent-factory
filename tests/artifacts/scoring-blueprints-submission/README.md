# GitHub Blueprint Evaluator Agent

This agent assesses a public GitHub repository against Mozilla AI Blueprint guidelines, scores it out of 100, posts the results to the `#blueprint-submission` Slack channel, and logs the entry into a local SQLite database.

## Prerequisites

- **uv** – Python package manager/runner
- **mcpd** – Model-Context Protocol daemon (for Slack & SQLite MCP servers)

### Install uv

- **macOS / Linux**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Windows PowerShell**
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

### Install mcpd

Follow the installation guide in the official documentation:
https://mozilla-ai.github.io/mcpd/installation/

## Configuration

Create a `.env` file with your environment variables, for example:

```
OPENAI_API_KEY=sk-...
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_TEAM_ID=T01234567
MCPD_ADDR=http://localhost:8090
# SQLite MCP server argument (path to DB)
MCPD_RUNTIME_ARGS="--db-path=$(pwd)/blueprints.db"
```

## Run the Agent

1. Export the variables and start the MCP daemon with the required servers (Slack and SQLite):

```bash
export $(cat .env | xargs)
# Start MCP daemon with Slack & SQLite servers (in another terminal or with &)
mcpd daemon --log-level=DEBUG --log-path=$(pwd)/mcpd.log --dev --runtime-file secrets.prod.toml
```

2. Evaluate a repository:

```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py --repo_url "https://github.com/your/repo"
```

The agent will output a structured JSON object, post the evaluation to Slack, and insert a row into the `github_repo_evaluations` table in `blueprints.db`.
Logs and full agent trace (including token costs) are saved to `agent_eval_trace.json`.
