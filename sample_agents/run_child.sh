uv venv --seed /home/codespace/.venvs/child
. /home/codespace/.venvs/child/bin/activate
pip install -r generated_workflows/latest/requirements.txt
python generated_workflows/latest/agent.py
