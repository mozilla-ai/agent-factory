import os
import tempfile
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path

import boto3
from any_agent.tracing.agent_trace import AgentTrace

from agent_factory.utils.logging import logger


class StorageBackend(ABC):
    @abstractmethod
    def __str__(self) -> str:
        """Return a string representation of the storage backend."""
        pass

    @abstractmethod
    def save(self, artifacts_to_save: dict[str, str], output_dir: Path) -> None:
        pass

    @abstractmethod
    def upload_trace_file(self, agent_trace: AgentTrace, output_dir: Path) -> None:
        """Upload agent trace to the storage backend."""
        pass


class LocalStorage(StorageBackend):
    def __str__(self) -> str:
        """Human-readable string identifying the local storage."""
        return "Local Storage"

    def save(self, artifacts_to_save: dict[str, str], output_dir: Path) -> None:
        output_dir = Path("generated_workflows") / output_dir
        output_path = self._setup_output_directory(output_dir)
        try:
            for file_path_str, content in artifacts_to_save.items():
                full_path = output_path / file_path_str
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with full_path.open("w", encoding="utf-8") as f:
                    f.write(content)
            logger.info(f"Agent files saved to folder {output_path}")
        except Exception as e:
            logger.warning(f"Warning: Failed to save agent outputs: {str(e)}")

    def _setup_output_directory(self, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def upload_trace_file(self, agent_trace: AgentTrace, output_dir: Path) -> None:
        """Save agent trace to the local storage directory."""
        output_dir = Path("generated_workflows") / output_dir
        output_path = self._setup_output_directory(output_dir)

        try:
            trace_dest = output_path / "agent_factory_trace.json"
            trace_dest.write_text(agent_trace.model_dump_json(), encoding="utf-8")
            logger.info(f"Agent trace saved to {trace_dest}")
        except Exception as e:
            logger.warning(f"Warning: Failed to save agent trace: {str(e)}")


class S3Storage(StorageBackend):
    def __init__(self):
        # Get credentials (optional for IRSA)
        self.aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.environ.get("AWS_REGION", "us-east-1")
        self.bucket_name = os.environ["S3_BUCKET_NAME"]
        self.endpoint_url = os.environ.get("AWS_ENDPOINT_URL") or None
        self.storage_str = "S3" if self.endpoint_url is None else "MinIO"

        # Build config dict for IRSA compatibility
        s3_config = {}

        # Always include region
        if self.aws_region:
            s3_config["region_name"] = self.aws_region

        # Only add credentials if both are provided (for local/dev)
        # If not provided, boto3 will use IRSA in K8s
        if self.aws_access_key_id and self.aws_secret_access_key:
            s3_config["aws_access_key_id"] = self.aws_access_key_id
            s3_config["aws_secret_access_key"] = self.aws_secret_access_key

        # Add endpoint URL for MinIO/LocalStack
        if self.endpoint_url:
            s3_config["endpoint_url"] = self.endpoint_url

        self.s3_client = boto3.client("s3", **s3_config)
        self._create_bucket_if_not_exists()

    def __str__(self) -> str:
        """Human-readable string identifying the S3/MinIO storage with bucket name."""
        return f"{self.storage_str} in bucket {self.bucket_name}"

    def _create_bucket_if_not_exists(self):
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except self.s3_client.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.info(f"Bucket {self.bucket_name} not found. Creating it.")
                if self.endpoint_url is None and self.aws_region != "us-east-1":
                    self.s3_client.create_bucket(
                        Bucket=self.bucket_name, CreateBucketConfiguration={"LocationConstraint": self.aws_region}
                    )
                else:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                raise

    def save(self, artifacts_to_save: dict[str, str], output_dir: Path) -> None:
        self._save_as_zip(artifacts_to_save, output_dir.name)

    def _save_as_zip(self, artifacts_to_save: dict[str, str], output_dir: str):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "agent_artifacts.zip"
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for filename, content in artifacts_to_save.items():
                    file_path = temp_path / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    with Path(file_path).open("w", encoding="utf-8") as f:
                        f.write(content)
                    zipf.write(file_path, arcname=filename)

            try:
                self.s3_client.upload_file(str(zip_path), self.bucket_name, f"{output_dir}/agent_artifacts.zip")
                logger.info(
                    f"Successfully uploaded agent artifacts to {self.storage_str} bucket "
                    f"{self.bucket_name} in folder {output_dir}"
                )
            except Exception as e:
                logger.error(f"Failed to upload to {self.storage_str} bucket {self.bucket_name}. Error: {e}")

    def upload_trace_file(self, agent_trace: AgentTrace, output_dir: Path) -> None:
        """Upload agent trace to S3/MinIO storage."""
        s3_key = f"{output_dir.name}/agent_factory_trace.json"
        try:
            agent_trace_json = agent_trace.model_dump_json()

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=agent_trace_json.encode("utf-8"),
                ContentType="application/json",
            )
            logger.info(
                f"Successfully uploaded agent trace to {self.storage_str} bucket {self.bucket_name} at {s3_key}"
            )
        except Exception as e:
            logger.error(f"Failed to upload agent trace to {self.storage_str} bucket {self.bucket_name}. Error: {e}")


def get_storage_backend() -> StorageBackend:
    backend = os.environ.get("STORAGE_BACKEND", "local")
    if backend in ["s3", "minio"]:
        return S3Storage()
    else:
        return LocalStorage()
