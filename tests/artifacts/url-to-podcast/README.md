# Setup Instructions

1. **Clone repository & enter the generated_workflows folder** (skip if already there).
2. **Create a `.env` file** in the project root with:
   ```bash
   OPENAI_API_KEY="your-openai-key"
   ELEVENLABS_API_KEY="your-elevenlabs-key"
   ```
3. **Install Python package manager uv**
   *macOS / Linux*
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   *Windows*
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
4. **Run the agent** (replace `<folder_name>` and `<URL>`):
   ```bash
   uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.13 \
      python generated_workflows/<folder_name>/agent.py --url "<URL>"
   ```
5. Generated files (individual turns and `podcast_final.mp3`) will be saved to `/tmp`.
