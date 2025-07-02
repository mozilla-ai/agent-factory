Setup Instructions
------------------
1. Create a `.env` file in the project root containing:
   OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
   ELEVENLABS_API_KEY="YOUR_ELEVENLABS_API_KEY"

2. Install the ultra-fast Python package manager **uv** (choose one):
   • macOS / Linux:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   • Windows (PowerShell):
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```

3. Run the agent (replace <folder_name> with the generated folder and supply a real URL):
   ```bash
   uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.11 \
      python generated_workflows/<folder_name>/agent.py --url "https://example.com/article"
   ```