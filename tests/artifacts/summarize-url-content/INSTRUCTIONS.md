## Setup Instructions

1. **Clone or download the repository** that contains `generated_workflows/latest/agent.py` and the `tools/` directory.

2. **Create a `.env` file** in the project root with the following environment variables:

```
# .env
OPENAI_API_KEY="your_openai_api_key"
```

`OPENAI_API_KEY` is required by both the agent (OpenAI provider) and the Litellm-based summarisation tool.

3. **Install dependencies and run the agent**.  Using **uv** you can create a temporary virtual environment and run the script in one command:

```bash
uv run \
  --with-requirements generated_workflows/latest/requirements.txt \
  --python 3.11 \
  python generated_workflows/latest/agent.py --url "https://example.com" --summary_length "three bullet points"
```

Replace the URL and `summary_length` arguments as desired.

*The first time you run the command `uv` will automatically create a virtual environment and install all dependencies listed in `requirements.txt`.*