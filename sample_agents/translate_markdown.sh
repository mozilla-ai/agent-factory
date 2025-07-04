#!/bin/sh
set -e

uv run python -m src.main "Please read the markdown file in a path (argument \`--file_path\`) that I'll give you, translate the descriptions to a language (argument \`--target_language\`), and save it as a file detailing the target language in the filename."
ARGS="--file_path 'tools/README.md' --target_language 'Spanish'" sh sample_agents/_run_new_agent.sh
