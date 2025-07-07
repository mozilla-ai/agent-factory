# Setup Instructions

1. **Clone repository / unpack project**

2. **Create a `.env` file** in the project root and add your OpenAI key:

```
OPENAI_API_KEY="sk-..."
```

3. **Install the `uv` package manager** (choose one command based on your OS):

*macOS / Linux*
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

*Windows (PowerShell)*
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

4. **Run the agent**

Replace `<folder_name>` with the generated workflow directory name and provide a URL to summarise:
```bash
uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.11 \
  python generated_workflows/<folder_name>/agent.py --url "https://example.com"
```