# Setup Instructions

1. Clone / download the generated workflow folder.
2. Install the universal Python package manager **uv** (choose the command for your OS):
   * macOS / Linux:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   * Windows (PowerShell):
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
3. Create a `.env` file in the workflow root and add the required environment variables:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   # Optional: custom guest voice
   # ELEVENLABS_VOICE_ID=voice-abcdef1234567890
   ```
4. Ensure **ffmpeg** is installed and in your system `PATH` (needed to merge mp3 files).
5. Run the agent:
   ```bash
   uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.13 \
     python generated_workflows/<folder_name>/agent.py --url "https://example.com/article"
   ```
   Replace `<folder_name>` with the actual timestamped directory and the sample URL with any page you like.

The script will output the final structured JSON and save an execution trace to `agent_eval_trace.json`. The synthesized one-minute podcast mp3 will be stored in the `podcasts/` sub-directory.
