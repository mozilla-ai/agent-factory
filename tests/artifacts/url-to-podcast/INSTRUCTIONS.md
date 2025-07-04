Setup & Run Instructions

1. Clone or download this repository.
2. Install the universal Python package manager “uv”.
   • macOS / Linux:
     `curl -LsSf https://astral.sh/uv/install.sh | sh`
   • Windows (PowerShell):
     `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
3. Install ffmpeg (required by the combine_mp3_files_for_podcast tool) and ensure it is in your PATH.
4. Create a `.env` file in the project root containing:
   OPENAI_API_KEY=<your_openai_key>
   ELEVENLABS_API_KEY=<your_elevenlabs_key>
5. Run the agent (replace <folder_name> and URL):
   `uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.11 python generated_workflows/<folder_name>/agent.py --url "https://example.com"`