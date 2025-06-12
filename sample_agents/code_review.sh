#!/bin/sh
set -e

uv run python -m src.main "Given a URL to a code snippet, which you need to ask for, extract the code and review it for errors, bugs, and improvements."
sh sample_agents/_run_new_agent.sh ARGS="https://raw.githubusercontent.com/mozilla-ai/agent-factory/refs/heads/main/eval/main.py"