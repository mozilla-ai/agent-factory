### Setup Instructions

1. Clone or download the project repository.
2. Create a `.env` file in the project root and add the mandatory ElevenLabs API key:

```
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```
3. (Optional) Add default voice IDs if you don’t plan to pass them on the command line:

```
HOST_VOICE_ID=voice_id_for_host
GUEST_VOICE_ID=voice_id_for_guest
```
4. Install the ultra-fast *uv* package manager:
   • macOS / Linux:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   • Windows (PowerShell):
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
5. Execute the agent (replace `<folder_name>` with the generated folder name and supply the required arguments):

```bash
uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.11 \
    python generated_workflows/<folder_name>/agent.py --url "https://example.com" \
    --host_voice_id "YOUR_HOST_VOICE_ID" --guest_voice_id "YOUR_GUEST_VOICE_ID"
```

The script will save the trace to `agent_eval_trace.json` and output the location of your finished `one_min_podcast.mp3`.