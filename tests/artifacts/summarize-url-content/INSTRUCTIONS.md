### Setup & Run Instructions

1. **Clone the repository or copy the generated code** into a local folder, e.g. `generated_workflows/20240611_123456/`.
2. **Create a `.env` file** inside that folder and add your OpenAI key (required by `litellm`):
   ```bash
   echo "OPENAI_API_KEY=your_openai_key_here" > .env
   ```
3. **Install the `uv` Python package manager** (choose the command for your OS):
   * **macOS / Linux**:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   * **Windows (PowerShell)**:
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
4. **Run the agent** (replace the folder name and URL):
   ```bash
   uv run --with-requirements generated_workflows/20240611_123456/requirements.txt --python 3.11 \
     python generated_workflows/20240611_123456/agent.py --url "https://example.com"
   ```
   The agent creates `agent_eval_trace.json` in the same folder and prints the structured summary.