#!/bin/sh
set -e

uv run python -m src.main "Please read the markdown file in a path that I'll give you, translate the descriptions to a language I'll also give you, and save it as a file detailing the target language in the filename."
sh sample_agents/_run_new_agent.sh ARGS="--file_path 'ools/available_tools.md' --target_language 'Spanish'"
