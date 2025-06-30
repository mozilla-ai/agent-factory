### Environment setup instructions\n\n1. **Create a `.env` file** in the project root and add your OpenAI key:\n   ```bash
   OPENAI_API_KEY="your_openai_api_key_here"
   ```\n\n2. **Install the universal Python package manager `uv`**\n   *MacOS / Linux*:\n   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```\n   *Windows* (PowerShell):\n   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```\n\n3. **Run the agent** (replace `<folder_name>` and the URL):\n   ```bash
   uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.11 \
      python generated_workflows/<folder_name>/agent.py --url "https://example.com"
   ```