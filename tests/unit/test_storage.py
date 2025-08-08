import os
from pathlib import Path
from unittest.mock import patch

import pytest

from agent_factory.utils.io_utils import prepare_agent_artifacts
from agent_factory.utils.storage import (
    LocalStorage,
    S3Storage,
    get_storage_backend,
)


def test_get_storage_backend_local_default():
    """Verify that get_storage_backend returns a LocalStorage instance by default."""
    backend = get_storage_backend()
    assert isinstance(backend, LocalStorage)


@pytest.mark.parametrize("backend_env, expected_class", [("s3", S3Storage), ("minio", S3Storage)])
def test_get_storage_backend_s3_minio(backend_env, expected_class, mock_s3_environ):
    """Verify that get_storage_backend returns an S3Storage instance when specified."""
    with patch.dict(os.environ, {"STORAGE_BACKEND": backend_env}):
        with patch("boto3.client"):  # Mock boto3 client to avoid actual AWS calls
            backend = get_storage_backend()
            assert isinstance(backend, expected_class)


def test_local_storage_save(tmp_path, sample_generator_agent_response_json):
    """Test the LocalStorage.save() method."""
    storage = LocalStorage()
    artifacts = prepare_agent_artifacts(sample_generator_agent_response_json)
    output_dir = tmp_path / "output"

    storage.save(artifacts, output_dir)

    assert (output_dir / "agent.py").exists()
    assert (output_dir / "README.md").exists()
    assert (output_dir / "requirements.txt").exists()
    assert (output_dir / "tools/__init__.py").exists()
    assert (output_dir / "tools/summarize_text_with_llm.py").exists()


def test_local_storage_setup_output_directory_with_existing_dir(tmp_path):
    """Ensures that passing an existing directory as output_dir returns the same directory."""
    storage = LocalStorage()
    result = storage._setup_output_directory(tmp_path)
    assert result == tmp_path
    assert result.exists()


def test_local_storage_setup_output_directory_creates_nonexistent_parents(tmp_path):
    """Verifies that the function creates parent directories if they don't exist."""
    storage = LocalStorage()
    target_dir = tmp_path / "nonexistent" / "subdir"
    result = storage._setup_output_directory(target_dir)
    assert result == target_dir
    assert result.exists()


@patch("boto3.client")
def test_s3_storage_save(mock_boto3_client, sample_generator_agent_response_json, mock_s3_environ):
    """Test the S3Storage.save() method with a mocked S3 client."""
    storage = S3Storage()
    artifacts = prepare_agent_artifacts(sample_generator_agent_response_json)
    output_dir = Path("output_dir_name")

    storage.save(artifacts, output_dir)

    mock_boto3_client.return_value.upload_file.assert_called_once()


@patch("boto3.client")
def test_s3_storage_bucket_creation(mock_boto3_client, mock_s3_environ):
    """Test that the S3Storage class creates a bucket if it doesn't exist."""
    from botocore.exceptions import ClientError

    mock_s3_client = mock_boto3_client.return_value
    mock_s3_client.exceptions.ClientError = ClientError
    mock_s3_client.head_bucket.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadBucket"
    )

    S3Storage()
    mock_s3_client.create_bucket.assert_called_once_with(Bucket="test-bucket")
