# Blueprint Repository Evaluator

Evaluates a GitHub repository against Mozilla AI Blueprint development guidelines, assigns a score, posts the evaluation to Slack, and logs it in a local SQLite database.

## Prerequisites

- uv
- mcpd

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

Follow the installation instructions in the official documentation: https://mozilla-ai.github.io/mcpd/installation/

## Configuration

Create a `.env` file in the project root and add the necessary environment variables, for example:

```env
# OpenAI / Anthropic / Azure keys for LLM usage
OPENAI_API_KEY=sk-...

# Slack MCP server authentication
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_TEAM_ID=T01234567

# SQLite MCP server configuration (path to database)
MCPD_ARGS_sqlite__db_path=./blueprints.db
```

## Run the Agent

1. Export your .env variables so they can be sourced by mcpd and run the mcpd daemon:
   ```bash
   export $(cat .env | xargs) \
     && mcpd daemon --log-level=DEBUG --log-path=$(pwd)/mcpd.log --dev --runtime-file secrets.prod.toml
   ```

2. Execute the agent:
   ```bash
   uv run --with-requirements requirements.txt --python 3.13 python agent.py --repo_url "https://github.com/owner/repo"
   ```

The agent will output a structured JSON result, post it to Slack, and insert a record into `blueprints.db`.
