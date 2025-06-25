### Setup Instructions

1. Install Python 3.11 and the **uv** package manager.
2. In the project root, create a file named `.env` and add the following environment variables:

```
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
```
3. Run the agent (replace `<URL>` with the webpage you want to convert):

```
uv run --with-requirements generated_workflows/latest/requirements.txt --python 3.11 python generated_workflows/latest/agent.py --url "<URL>"
```