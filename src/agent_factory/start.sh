#!/bin/sh

# Set default values for environment variables if not set
: "${FRAMEWORK:=openai}"
: "${MODEL:=o3}"
: "${HOST:=0.0.0.0}"
: "${PORT:=8080}"
: "${LOG_LEVEL:=info}"
: "${CHAT:=1}"

# Check if CHAT is set to 1 or 0 and set the chat flag accordingly
chat_flag="--nochat"
[ "$CHAT" -eq 1 ] && chat_flag="--chat"

uv run -m agent_factory --framework "${FRAMEWORK}" $chat_flag --model "${MODEL}" --host "${HOST}" --port "${PORT}" --log-level "${LOG_LEVEL}"
