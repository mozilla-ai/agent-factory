### Environment Setup Instructions

1. Clone or download this repository and navigate to the generated_workflows/<folder_name> directory.

2. Create a `.env` file in that directory containing **all** of the following environment variables:

```
OPENAI_API_KEY=<your-openai-api-key>
SLACK_BOT_TOKEN=<your-slack-bot-token>
SLACK_TEAM_ID=<your-slack-team-id>
BLUEPRINTS_DB_PATH=<absolute-path-to-your-blueprints.db>
```

3. Install the **uv** package manager (choose one command based on your OS):

- **macOS / Linux**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Windows (PowerShell)**
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

4. Install Python dependencies and run the agent via CLI (replace `<folder_name>` with your timestamped folder name and `<repo_url>` with the GitHub URL you want to evaluate):

```bash
uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.11 \
  python generated_workflows/<folder_name>/agent.py --repo_url "<repo_url>"
```

The agent will output a JSON object and save the full execution trace to `agent_eval_trace.json` in the same directory.