### Setup & Run Instructions

1. Clone or download this project.
2. Ensure **ffmpeg** is installed and accessible in your PATH (required for MP3 combination).
3. Create a `.env` file in the project root containing:
```
OPENAI_API_KEY="your_openai_api_key"
ELEVENLABS_API_KEY="your_elevenlabs_api_key"
```
4. Install Python package manager **uv** (choose one):
   * macOS / Linux:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   * Windows (PowerShell):
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
5. Run the agent (replace `<folder_name>` with the generated directory name and your URL):
```bash
uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.11 \
  python generated_workflows/<folder_name>/agent.py --url "https://example.com"
```