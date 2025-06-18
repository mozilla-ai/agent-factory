#!/bin/sh
set -e

uv run python -m src.main "Given a URL (argument \`--url\`) to a code snippet, extract the code and review it for errors, bugs, and improvements."
ARGS="--url=https://raw.githubusercontent.com/mozilla-ai/agent-factory/refs/heads/main/eval/main.py" sh sample_agents/_run_new_agent.sh