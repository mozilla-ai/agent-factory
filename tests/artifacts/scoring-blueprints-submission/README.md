# Blueprint Evaluation Agent

This repository contains **agent.py** which evaluates a GitHub repository against Mozilla AI Blueprint guidelines, publishes the results to Slack, and stores the evaluation in a local SQLite database.

## Environment Setup

1. **Clone this repository**
2. **Create a `.env` file** in the project root containing:

```
OPENAI_API_KEY=your_openai_key_here
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_TEAM_ID=T0123456789
```

3. **Install the package manager `uv`** (choose one):

- macOS / Linux:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- Windows (PowerShell):
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

4. **Install Python dependencies & run the agent**

```bash
uv run --with-requirements requirements.txt --python 3.13 \
  python agent.py --repo_url "https://github.com/your_org/your_repo"
```

## Required Files
* `blueprints.db` – an SQLite database already containing the table `github_repo_evaluations`.

## Notes
* The agent automatically discovers the Slack channel named `#blueprint-submission`.
* Only minimal tools are enabled from each MCP server for security.
* All evaluation traces are stored in `agent_eval_trace.json` for later inspection.
