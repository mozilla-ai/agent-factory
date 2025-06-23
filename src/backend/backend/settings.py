import os

from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    @computed_field
    @property
    def A2A_AGENT_URL(self) -> str:  # noqa: N802
        return os.environ.get("A2A_AGENT_URL", "http://localhost:5001")

    @computed_field
    @property
    def PUBLIC_AGENT_CARD_PATH(self) -> str:  # noqa: N802
        return os.environ.get("PUBLIC_AGENT_CARD_PATH", "'/.well-known/agent.json'")

    @computed_field
    @property
    def EXTENDED_AGENT_CARD_PATH(self) -> str:  # noqa: N802
        return os.environ.get("EXTENDED_AGENT_CARD_PATH", "/agent/authenticatedExtendedCard")


settings = Settings()
