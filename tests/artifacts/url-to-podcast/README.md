# Setup Instructions

1. Clone this repository and navigate into the generated workflow folder (e.g. `generated_workflows/20240410_123456`).
2. Create a `.env` file in that folder and set the required environment variables:

```
OPENAI_API_KEY=your-openai-key
ELEVENLABS_API_KEY=your-elevenlabs-key
```

3. Install the **uv** package manager (choose the command for your OS):

*MacOS / Linux*
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

*Windows (PowerShell)*
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

4. Ensure FFmpeg is installed and reachable in your system `PATH` (required for MP3 concatenation).

5. Install Python dependencies and run the agent (replace `<folder_name>` and `<URL>`):

```bash
uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.13 python generated_workflows/<folder_name>/agent.py --url "<URL>"
```

The agent will output `agent_eval_trace.json` (detailed trace) and the final `podcast_final.mp3` file in the workflow directory.