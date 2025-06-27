### Setup / Run Instructions

1. Clone or download this repository.
2. Create a `.env` file in the project root containing:

```
OPENAI_API_KEY=your_openai_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

3. Install the modern Python package manager **uv** (choose one):

*Mac / Linux*
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```
*Windows (PowerShell)*
```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

4. Run the agent (replace `<folder_name>` with the actual timestamped folder name and supply your arguments):
```
uv run --with-requirements generated_workflows/<folder_name>/requirements.txt --python 3.11 \
  python generated_workflows/<folder_name>/agent.py --url "https://example.com/article" --num_hosts 3
```