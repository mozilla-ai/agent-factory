# Setup & Run Instructions

1. Clone or download this repository and ensure you have Python 3.11 installed.
2. Create a `.env` file in the project root containing at minimum:

```
OPENAI_API_KEY=<your-openai-key>
ELEVENLABS_API_KEY=<your-elevenlabs-key>
```
3. Install dependencies and run the agent in one command:

```bash
uv run --with-requirements generated_workflows/latest/requirements.txt --python 3.11 \
  python generated_workflows/latest/agent.py --url "https://example.com/article" --num_speakers 3
```

The agent will save its trace to `generated_workflows/latest/agent_eval_trace.json` and print the structured JSON result containing the path to the generated podcast mp3.