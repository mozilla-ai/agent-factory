## Setup Instructions

1. **Clone the repository** (or download `agent.py`).
2. **Create a Python virtual environment** (optional but recommended).
3. **Install the `uv` package manager**
   • macOS & Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   • Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
4. **Create a `.env` file** in the project root and add your OpenAI API key (required by any-agent):

   ```env
   OPENAI_API_KEY=your_openai_key_here
   ```

   No other environment variables are necessary for this agent.
5. **Install dependencies & run the agent**:

   ```bash
   uv run --with-requirements requirements.txt --python 3.13 python agent.py --url "https://example.com"
   ```

The agent will output the JSON summary and write the full execution trace to `agent_eval_trace.json`.
