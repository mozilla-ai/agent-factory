### Setup instructions

1. Clone or download this repository.
2. Ensure `ffmpeg` is installed and available on your system path.
3. Create a `.env` file in the project root with the following variables:

```
OPENAI_API_KEY=<your_openai_key>
ELEVENLABS_API_KEY=<your_elevenlabs_api_key>
# Optional – supply a different voice for the guest speaker
ELEVENLABS_GUEST_VOICE_ID=<guest_voice_id>
```

4. Install the Python package manager **uv** (choose the command for your OS):
   * macOS/Linux:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   * Windows (PowerShell):
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```

5. Install dependencies and run the agent (replace `<folder_name>` with the actual timestamped folder name and provide a real URL):

```bash
uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.11 \
  python generated_workflows/<folder_name>/agent.py --url "https://example.com"
```

The agent will produce `agent_eval_trace.json` (for inspection) and `one_minute_podcast.mp3` in the working directory.