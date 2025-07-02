### Setup & Run Instructions

1. Create and activate a Python 3.11 environment (if not already).

2. Install the **uv** package manager (choose the command that matches your OS):
   • macOS/Linux:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   • Windows PowerShell:
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. Place your OpenAI API key in a `.env` file at the project root:
   ```env
   OPENAI_API_KEY="your_openai_key_here"
   ```

4. Run the agent (replace `<folder_name>` with the generated folder and `<url>` with the target page):
   ```bash
   uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.11 \
     python generated_workflows/<folder_name>/agent.py --url "<url>"
   ```