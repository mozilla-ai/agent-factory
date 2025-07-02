### Setup / Run Instructions

1. Clone or download this generated workflow folder.
2. Create a `.env` file in the same folder and set **all** required environment variables:

```
OPENAI_API_KEY="sk-..."          # For the OpenAI model (o3)
SLACK_BOT_TOKEN="xoxb-..."       # Bot token with chat:write & channels:read scopes
SLACK_TEAM_ID="T01234567"        # Your Slack workspace ID
```

3. Install the ultra-fast Python package manager `uv` (choose one):
   • macOS/Linux:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   • Windows PowerShell:
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

4. Run the agent (replace `<folder_name>` with the actual generated folder name):

```bash
uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.11 \
  python generated_workflows/<folder_name>/agent.py --repo_url "https://github.com/owner/repo"
```

The script prints nothing but writes `agent_eval_trace.json` containing the full trace and returns the structured evaluation JSON.