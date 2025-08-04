import os
import tempfile
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path

import boto3

from agent_factory.utils.logging import logger


class StorageBackend(ABC):
    @abstractmethod
    def save(self, artifacts_to_save: dict[str, str], output_dir: Path) -> None:
        pass


class LocalStorage(StorageBackend):
    def save(self, artifacts_to_save: dict[str, str], output_dir: Path) -> None:
        output_path = self._setup_output_directory(output_dir)
        try:
            for file_path_str, content in artifacts_to_save.items():
                full_path = output_path / file_path_str
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with full_path.open("w", encoding="utf-8") as f:
                    f.write(content)
            logger.info(f"Agent files saved to {output_path}")
        except Exception as e:
            logger.warning(f"Warning: Failed to save agent outputs: {str(e)}")

    def _setup_output_directory(self, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir


class S3Storage(StorageBackend):
    def __init__(self):
        self.aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
        self.aws_secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
        self.aws_region = os.environ["AWS_DEFAULT_REGION"]
        self.bucket_name = os.environ["S3_BUCKET"]
        self.endpoint_url = os.environ.get("AWS_ENDPOINT_URL") or None

        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region,
            endpoint_url=self.endpoint_url,
        )
        self._create_bucket_if_not_exists()

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
                    f"Successfully uploaded agent artifacts to S3 bucket {self.bucket_name} to folder {output_dir}"
                )
            except Exception as e:
                logger.error(f"Failed to upload to S3 bucket {self.bucket_name}. Error: {e}")


def get_storage_backend() -> StorageBackend:
    backend = os.environ.get("STORAGE_BACKEND", "local")
    if backend in ["s3", "minio"]:
        return S3Storage()
    else:
        return LocalStorage()
