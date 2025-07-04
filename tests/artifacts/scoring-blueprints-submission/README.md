# Setup Instructions

1. **Clone this repository** (or place the generated_workflows folder in your project).

2. **Create a `.env` file** in the project root with the following variables:

```
OPENAI_API_KEY="<your-openai-key>"
SLACK_BOT_TOKEN="xoxb-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx"
SLACK_TEAM_ID="T01234567"
```

3. **Install the `uv` Python package manager**

MacOS / Linux:
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Windows (PowerShell):
```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

4. **Prepare the SQLite database**
   Ensure a Docker volume named `blueprints_db` exists and already contains the file `blueprints.db` with table `github_repo_evaluations`.  For a fresh setup you can create it by:

```bash
docker volume create blueprints_db
docker run --rm -i -v blueprints_db:/data alpine sh -c "apk add --no-cache sqlite && sqlite3 /data/blueprints.db 'CREATE TABLE IF NOT EXISTS github_repo_evaluations (id INTEGER PRIMARY KEY AUTOINCREMENT, repo_url TEXT, score INTEGER, summary TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);'"
```

5. **Run the agent**
Replace `<folder_name>` with the time-stamped folder created inside `generated_workflows` and `<repo_url>` with the repository you want to evaluate.

```bash
uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.11 \
    python generated_workflows/<folder_name>/agent.py --repo_url "<repo_url>"
```

The agent will output a JSON object, post the evaluation message to Slack and log the result into the SQLite database.