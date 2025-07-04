from pathlib import Path
from uuid import UUID

from backend.settings import settings
from backend.storage import storage_client


def prepare_output_dir(agent_id: UUID) -> Path:
    """Prepare the output directory for the agent's generated workflows.

    Args:
        agent_id (UUID): The unique identifier of the agent.

    Returns:
        Path: The path to the output directory where workflows will be saved.
    """
    output_dir = Path.cwd()
    output_dir = output_dir / "generated_workflows" / str(agent_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def download_agent_files(agent_id: UUID) -> Path:
    """Download the agent files from S3.

    Args:
        agent_id (UUID): The unique identifier of the agent.

    Returns:
        Path: The path to the directory where the files were downloaded.
    """
    output_dir = prepare_output_dir(agent_id)
    bucket_name = settings.S3_BUCKET_NAME

    files_to_download = ["agent.py", "INSTRUCTIONS.md", "requirements.txt", "Containerfile"]

    for file in files_to_download:
        storage_client.download_file(
            bucket_name,
            f"{agent_id}/{file}",
            str(output_dir / file),
        )

    # Download tools directory
    tools_prefix = f"{agent_id}/tools/"
    tools_dir = output_dir / "tools"
    tools_dir.mkdir(exist_ok=True)

    response = storage_client.list_objects_v2(Bucket=bucket_name, Prefix=tools_prefix)
    if "Contents" in response:
        for obj in response["Contents"]:
            tool_key = obj["Key"]
            tool_file_name = Path(tool_key).name
            if tool_file_name:
                storage_client.download_file(
                    bucket_name,
                    tool_key,
                    str(tools_dir / tool_file_name),
                )

    return output_dir
