# Setup Instructions

### 1. Environment variables
Create a `.env` file at the project root with:
```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_TEAM_ID=T0123456789
```

### 2. Install the **uv** package manager (choose one command based on your OS)
- **macOS / Linux**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Windows (PowerShell)**
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

### 3. Install dependencies & run the agent
```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py --repo_url "https://github.com/your/repository"
```

The agent will evaluate the repository, post a message in the `#blueprint-submission` Slack channel, insert a row into `blueprints.db`, and return a structured JSON response.
