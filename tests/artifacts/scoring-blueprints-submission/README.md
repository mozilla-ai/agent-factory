# Setup Instructions

1. Clone this repository and navigate to the generated_workflows/timestamped_folder.
2. Create a `.env` file with the following environment variables:

```
OPENAI_API_KEY=<your_openai_key>
SLACK_BOT_TOKEN=<your_slack_bot_token>
SLACK_TEAM_ID=<your_slack_team_id>
```

3. Install the **uv** package manager (choose one):
   * **macOS / Linux**
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   * **Windows (PowerShell)**
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```

4. Ensure `blueprints.db` (containing table `github_repo_evaluations`) is located in the same folder as `agent.py`.

5. Run the agent:

```bash
uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.13 \
  python generated_workflows/<folder_name>/agent.py --repo_url "https://github.com/your/repo"
```

Replace `<folder_name>` with your timestamped directory and the repo URL you want to evaluate.