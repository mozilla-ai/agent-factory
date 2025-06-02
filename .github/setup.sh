#/bin/bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
uv sync
uv pip install -e .
