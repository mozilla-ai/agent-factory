#!/bin/sh
set -e

uv run python -m src.main "Find a webpage that talks about the topic the user tells you (take argument \`--topic\`), read it and summarize the who, what and when for the user."
ARGS="--topic='the news today'" sh sample_agents/_run_new_agent.sh
