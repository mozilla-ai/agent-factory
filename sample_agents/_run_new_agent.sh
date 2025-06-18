#!/bin/sh
set -x

if [ -n "$VIRTUAL_ENV" ]; then
  deactivate || true
fi

uv venv --seed "$HOME/.venvs/child"
. "$HOME/.venvs/child/bin/activate"
pip install -r generated_workflows/latest/requirements.txt
python generated_workflows/latest/agent.py "$ARGS"