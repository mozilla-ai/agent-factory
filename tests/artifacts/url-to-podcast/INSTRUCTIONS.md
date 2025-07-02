### Setup & Run Instructions

1. Clone or download the generated workflow directory created by the agent-factory.
2. Ensure you have Python 3.11 installed.
3. Install the ultra-fast Python package manager **uv** (choose the command for your OS):
   • macOS/Linux:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   • Windows (PowerShell):
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
4. Create a `.env` file at the root of the project with the following variables:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ```
   (No quotes – replace with your real keys.)
5. Make sure **ffmpeg** is installed and accessible in your system `PATH` (required for combining MP3 files).
6. Install Python dependencies and run the agent (replace `<folder_name>` with the actual timestamped folder and provide a real URL):
   ```bash
   uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.11 \
     python generated_workflows/<folder_name>/agent.py --url "https://example.com/article"
   ```
7. After completion, inspect the printed JSON output for the path to `podcast.mp3` and locate the file in the `podcasts/` directory.
