# Setup Instructions

1. **Clone the repository** (or copy the generated_workflows folder).
2. **Create and activate a Python virtual environment** (optional but recommended).
3. **Install the universal Python package manager `uv`:**
   - macOS / Linux:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - Windows (PowerShell):
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
4. **Add required environment variables**
   - Create a file named `.env` in the project root with:
     ```env
     OPENAI_API_KEY=<your_openai_api_key>
     ```
5. **Run the agent** (replace `<folder_name>` with the actual timestamped directory and provide a URL):
   ```bash
   uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.13 \
     python generated_workflows/<folder_name>/agent.py --url "https://example.com"
   ```