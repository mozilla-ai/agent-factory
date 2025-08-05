# Webpage Summarizer Agent

This agent downloads the textual content of any public webpage and returns a concise English summary.

## Environment Variables
Create a `.env` file in the project root with the following variable:

```
OPENAI_API_KEY=<your_openai_api_key>
```

## Install the *uv* package manager

MacOS / Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Install dependencies and run the agent
```bash
uv run --with-requirements requirements.txt --python 3.13 python agent.py --url "https://example.com"
```
