import os

from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    @computed_field
    @property
    def A2A_AGENT_URL(self) -> str:  # noqa: N802
        return os.environ.get("A2A_AGENT_URL", "http://agent:8080")

    @computed_field
    @property
    def REDIS_URL(self) -> str:  # noqa: N802
        return os.environ.get("REDIS_URL", "redis://redis:6379/0")

    @computed_field
    @property
    def PUBLIC_AGENT_CARD_PATH(self) -> str:  # noqa: N802
        return os.environ.get("PUBLIC_AGENT_CARD_PATH", "'/.well-known/agent.json'")

    @computed_field
    @property
    def EXTENDED_AGENT_CARD_PATH(self) -> str:  # noqa: N802
        return os.environ.get("EXTENDED_AGENT_CARD_PATH", "/agent/authenticatedExtendedCard")

    @computed_field
    @property
    def STORAGE_TYPE(self) -> str:  # noqa: N802
        return os.environ.get("STORAGE_TYPE", "minio")

    @computed_field
    @property
    def S3_ENDPOINT_URL(self) -> str | None:  # noqa: N802
        return os.environ.get("S3_ENDPOINT_URL", "http://minio:9000")

    @computed_field
    @property
    def S3_ACCESS_KEY(self) -> str:  # noqa: N802
        return os.environ.get("S3_ACCESS_KEY", "minioadmin")

    @computed_field
    @property
    def S3_SECRET_KEY(self) -> str:  # noqa: N802
        return os.environ.get("S3_SECRET_KEY", "minioadmin")

    @computed_field
    @property
    def S3_BUCKET_NAME(self) -> str:  # noqa: N802
        return os.environ.get("S3_BUCKET_NAME", "agents")


settings = Settings()
