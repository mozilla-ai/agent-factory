# Setup Instructions

1. **Clone repository / obtain code**
2. **Environment Variables** – create a `.env` file in the project root containing:
   ```env
   OPENAI_API_KEY=your_openai_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_key_here
   # Optional – only if you want specific voices
   # ELEVENLABS_VOICE_ID=voice-id
   ```
3. **Install `uv` package manager**
   *MacOS/Linux*
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   *Windows (PowerShell)*
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
4. **System Requirements**
   • `ffmpeg` must be installed and available in your PATH for MP3 concatenation.
   • `docker` must be installed and running (used for the ElevenLabs MCP server).

5. **Run the Agent**
   Replace `<folder_name>` with your generated timestamped directory and supply the target URL:
   ```bash
   uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.13 \
     python generated_workflows/<folder_name>/agent.py --url "https://example.com/article"
   ```
   The final podcast mp3 will be saved to `generated_workflows/<folder_name>/podcasts/final_podcast.mp3` and the full execution trace to `agent_eval_trace.json`.