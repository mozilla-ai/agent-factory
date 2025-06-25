## Setup & Run Instructions

1. Clone or download the project repository.
2. Ensure you have **Python 3.11** installed.
3. Create a `.env` file in the project root containing the following (replace the values with your own keys):

```env
OPENAI_API_KEY="your-openai-api-key"
ELEVENLABS_API_KEY="your-elevenlabs-api-key"
```

4. Install dependencies and run the agent using **uv**:

```bash
uv run --with-requirements generated_workflows/latest/requirements.txt --python 3.11 \
  python generated_workflows/latest/agent.py --url "https://example.com" --num_hosts 3
```

The agent will:
1. Fetch the article text from the given URL.
2. Generate a podcast script featuring the specified number of hosts.
3. Produce an MP3 file narrated with multiple voices using ElevenLabs.
4. Save an execution trace to `generated_workflows/latest/agent_eval_trace.json` and print the structured JSON result containing the audio file path.

**Note:** ffmpeg must be installed and accessible via your system `PATH` if you plan on extending the workflow to combine audio files, though the current implementation does not require it.
