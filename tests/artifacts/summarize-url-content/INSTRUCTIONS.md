### Setup instructions
1. Create a `.env` file in the project root containing your OpenAI key:
   ```bash
   OPENAI_API_KEY="sk-..."
   ```
2. Install the ultra-fast Python package manager **uv** (choose one command):
   • macOS / Linux:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   • Windows (PowerShell):
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
3. Run the agent (replace `<folder_name>` with the generated_workflows sub-folder and provide a URL):
   ```bash
   uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.11 \
       python generated_workflows/<folder_name>/agent.py --url "https://example.com"
   ```
The agent will create `agent_eval_trace.json` in the same folder, containing the full execution trace.