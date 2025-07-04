# How to run this agent

1. Clone or download the generated_workflows folder.
2. Create a `.env` file in the project root and add the following variables:
   ```
   OPENAI_API_KEY=<your-openai-key>
   SLACK_BOT_TOKEN=<your-slack-bot-token>
   SLACK_TEAM_ID=<your-team-id>
   ```
3. Ensure a file named `blueprints.db` exists in the working directory and contains the table
   `github_repo_evaluations` with at least these columns:
   ```sql
   CREATE TABLE IF NOT EXISTS github_repo_evaluations (
       repo_url TEXT,
       score INTEGER,
       evaluation_details TEXT,
       evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```
4. Install the uv package manager:
   • macOS/Linux:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   • Windows PowerShell:
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
5. Install dependencies and run the agent (replace `<folder_name>` and `<repo>`):
   ```bash
   uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.11 \
     python generated_workflows/<folder_name>/agent.py --repo_url "<repo>"
   ```