"""Configuration settings for the Agent Factory."""

import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(".default.env", usecwd=True))
load_dotenv(find_dotenv(".env", usecwd=True), override=True)

PROJECT_ROOT = Path(__file__).parent.parent.parent
TRACES_DIR = Path(os.getenv("TRACES_DIR", "traces"))
if not TRACES_DIR.is_absolute():
    TRACES_DIR = PROJECT_ROOT / TRACES_DIR

DEFAULT_EXPORT_PATH = PROJECT_ROOT / "generated_workflows"

# A2A Protocol Constants
PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"
EXTENDED_AGENT_CARD_PATH = "/agent/authenticatedExtendedCard"
DEFAULT_TIMEOUT = 600  # 10 minutes
