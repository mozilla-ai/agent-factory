# Blueprint Evaluator Agent – Setup Instructions

This agent evaluates a GitHub repository against Mozilla AI’s Blueprint guidelines, posts the result to Slack and records it in a local SQLite database.

## 1. Clone or download the generated workflow folder

```bash
cd generated_workflows/<folder_name>
```

## 2. Environment variables
Create a `.env` file in the same directory containing:
```
OPENAI_API_KEY=<your OpenAI key>
SLACK_BOT_TOKEN=<your Slack bot token>
SLACK_TEAM_ID=<your Slack workspace team id>
SQLITE_DB_PATH=<absolute path to blueprints.db on your host>
```
The `blueprints.db` file must already exist and contain the table `github_repo_evaluations` with columns `(id INTEGER PRIMARY KEY, repo_url TEXT, score INTEGER, evaluation_text TEXT, created_at DATETIME)`.

## 3. Install the `uv` package manager
• macOS / Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
• Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 4. Install dependencies & run the agent
Replace `<folder_name>` with the actual timestamped folder and supply a GitHub repo link:
```bash
uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.13 \
    python generated_workflows/<folder_name>/agent.py --repo_url "https://github.com/owner/repo"
```
The agent will output a JSON object and write an `agent_eval_trace.json` file to the folder for inspection.