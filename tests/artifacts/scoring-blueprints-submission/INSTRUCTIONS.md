### Environment setup
1. Create a `.env` file in the project root with the following keys:

```
OPENAI_API_KEY=<your-openai-api-key>
SLACK_BOT_TOKEN=<your-slack-bot-token>
SLACK_TEAM_ID=<your-slack-workspace-id>
```

2. Install the **uv** package manager (choose the command for your OS):
   • macOS / Linux
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   • Windows (PowerShell)
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. Run the agent (replace `<folder_name>` with the generated timestamped folder and supply a GitHub URL):
```bash
uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.11 \
    python generated_workflows/<folder_name>/agent.py --repo_url "https://github.com/owner/repo"
```