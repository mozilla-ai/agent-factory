# Setup Instructions

1. Clone or download this project.
2. Create a `.env` file in the project root containing:

```
OPENAI_API_KEY=<your_openai_key>
SLACK_BOT_TOKEN=<your_slack_bot_token>
SLACK_TEAM_ID=<your_slack_team_id>
```

3. Install the ultra-fast Python package manager `uv`:
   * **macOS / Linux**:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   * **Windows (PowerShell)**:
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```

4. Run the agent (replace `<folder_name>` with the actual timestamped sub-folder and your company name):

```bash
uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.13 \
  python generated_workflows/<folder_name>/agent.py --company_name "ACME Corp"
```