from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agent_factory.instructions import AGENT_CODE_TEMPLATE
from agent_factory.utils.io_utils import save_agent_outputs, setup_output_directory


def test_setup_output_directory_default(tmp_path):
    """Tests the creation of a timestamped directory when no output_dir is provided."""
    mock_cwd = tmp_path
    mock_now_datetime = MagicMock()
    mock_now_datetime.strftime.return_value = "2025-07-28_10:00:00"
    mock_uuid = "12345678"
    expected_output_path = mock_cwd / "generated_workflows" / f"2025-07-28_10:00:00_{mock_uuid}"

    with (
        patch("agent_factory.utils.io_utils.Path.cwd", return_value=mock_cwd),
        patch("agent_factory.utils.io_utils.datetime") as mock_datetime,
        patch("agent_factory.utils.io_utils.uuid.uuid4", return_value=mock_uuid),
        patch("agent_factory.utils.io_utils.Path.mkdir") as mock_mkdir,
    ):
        mock_datetime.now.return_value = mock_now_datetime
        result = setup_output_directory(output_dir=None)

        assert result == expected_output_path
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


@pytest.mark.parametrize(
    "custom_input, expected_path",
    [
        (Path("/custom/path/dir"), Path("/custom/path/dir")),
        ("/custom/string/dir", Path("/custom/string/dir")),
    ],
    ids=["path_input", "str_input"],
)
def test_setup_output_directory_specified(custom_input, expected_path):
    """Tests the setup_output_directory function when a Path or string is provided."""
    with patch("agent_factory.utils.io_utils.Path.mkdir") as mock_mkdir:
        result = setup_output_directory(output_dir=custom_input)
        assert result == expected_path
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


def test_save_agent_outputs_success(tmp_path, sample_generator_agent_response_json):
    agent_code = AGENT_CODE_TEMPLATE.format(**sample_generator_agent_response_json)
    output_dir = tmp_path
    agent_path = output_dir / "agent.py"
    readme_path = output_dir / "README.md"
    req_path = output_dir / "requirements.txt"

    with patch("agent_factory.utils.io_utils.clean_python_code_with_autoflake", side_effect=lambda x: x) as mock_clean:
        save_agent_outputs(sample_generator_agent_response_json, output_dir)

        mock_clean.assert_called_once_with(agent_code)
        assert agent_path.exists()
        assert readme_path.exists()
        assert req_path.exists()
