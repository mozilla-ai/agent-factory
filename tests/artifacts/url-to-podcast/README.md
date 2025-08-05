# One-Minute Podcast Generator

This project contains `agent.py`, an **any-agent** powered script that transforms any webpage into a concise 1-minute podcast, voiced by a host and a guest.

## Setup Instructions

1. **Clone this repository** and move into it.
2. **Create a `.env` file** in the project root containing:

```
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
```

3. **Install the universal Python package manager `uv`** (choose the command for your OS):

*Mac / Linux*
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

*Windows (PowerShell)*
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

4. **Install dependencies and run the agent**

```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py --url "https://example.com/article"
```

This will output the structured JSON response and save `agent_eval_trace.json` (including execution costs) plus the podcast MP3 in the `podcasts/` folder.

### External Requirements
* `ffmpeg` must be installed and available in your system `PATH` for audio-file concatenation.
