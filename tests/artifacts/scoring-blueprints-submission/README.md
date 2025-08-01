# Setup Instructions

1. Clone this repository and switch into its directory.
2. Create a `.env` file in the project root containing **all** of the following variables:
   ```env
   # OpenAI (or compatible) key for the agent’s LLM calls
   OPENAI_API_KEY=<your_openai_key>

   # Slack MCP credentials
   SLACK_BOT_TOKEN=<your_slack_bot_token>
   SLACK_TEAM_ID=<your_slack_team_id>

   # Path on the host machine to the SQLite database (blueprints.db)
   DB_PATH=/absolute/path/to/blueprints.db
   ```
3. Install the **uv** package manager (choose one):
   * macOS / Linux:
     `curl -LsSf https://astral.sh/uv/install.sh | sh`
   * Windows (PowerShell):
     `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
4. Install Python dependencies and run the agent:
   ```bash
   uv run --with-requirements requirements.txt --python 3.13 \
       python agent.py --repo_url "https://github.com/owner/repo"
   ```
