#!/bin/sh
set -e

deactivate
uv venv --seed "$HOME/.venvs/child"
. "$HOME/.venvs/child/bin/activate"
pip install -r generated_workflows/latest/requirements.txt
python generated_workflows/latest/agent.py "$ARGS"