import json
import tempfile
from pathlib import Path

import pytest

from agent_factory.factory_tools import initialize_mcp_config, register_mcp_server
from agent_factory.instructions import AGENT_CODE_TEMPLATE
from agent_factory.schemas import AgentParameters
from agent_factory.utils.io_utils import (
    BINARY_NAME_MCPD,
    export_mcpd_config_artifacts,
    parse_cli_args_to_params_json,
    prepare_agent_artifacts,
    run_binary,
)


def test_prepare_agent_artifacts(sample_generator_agent_response_json):
    """Test that prepare_agent_artifacts correctly prepares the artifacts."""
    artifacts = prepare_agent_artifacts(sample_generator_agent_response_json)

    assert "agent.py" in artifacts
    assert "README.md" in artifacts
    assert "requirements.txt" in artifacts
    assert "tools/__init__.py" in artifacts
    assert "tools/summarize_text_with_llm.py" in artifacts
    assert "agent_parameters.json" in artifacts

    from agent_factory.utils import clean_python_code_with_autoflake

    agent_code_before_cleaning = AGENT_CODE_TEMPLATE.format(**sample_generator_agent_response_json)
    assert artifacts["agent.py"] == clean_python_code_with_autoflake(agent_code_before_cleaning)
    assert artifacts["README.md"] == sample_generator_agent_response_json["readme"]
    assert artifacts["requirements.txt"] == sample_generator_agent_response_json["dependencies"]

    # Verify tools taken from src directory
    tool_path = Path("src/agent_factory/tools/summarize_text_with_llm.py")
    assert artifacts["tools/summarize_text_with_llm.py"] == tool_path.read_text(encoding="utf-8")

    assert artifacts["agent_parameters.json"] == parse_cli_args_to_params_json(
        sample_generator_agent_response_json["cli_args"]
    )


@pytest.mark.parametrize(
    "cli_args_str, expected_params",
    [
        # Single argument
        ("url: str", {"params": {"--url": "string"}}),
        # Multiple arguments
        ("url: str, num_hosts: int", {"params": {"--url": "string", "--num_hosts": "integer"}}),
        # Empty string
        ("", {"params": {}}),
    ],
)
def test_parse_cli_args_to_params_json(cli_args_str, expected_params):
    """Test that parse_cli_args_to_params_json correctly parses various CLI argument strings."""
    params_json_str = parse_cli_args_to_params_json(cli_args_str)
    actual_params = json.loads(params_json_str)
    assert actual_params == expected_params

    # Validate against the Pydantic schema
    validated_params = AgentParameters(**actual_params)
    assert validated_params.model_dump() == expected_params


def test_missing_binary_fails_with_clear_message():
    """Test that missing binary produces a clear failure message."""
    try:
        run_binary("definitely_not_a_real_binary_12345", ["--version"], ignore_response=True)
        pytest.fail("Should have raised RuntimeError for missing binary")
    except RuntimeError as e:
        if "Binary not found" in str(e):
            assert "Binary not found: definitely_not_a_real_binary_12345" in str(e)
        else:
            raise  # Re-raise if it's a different RuntimeError.


def test_export_mcpd_config_artifacts_no_mcpd_key():
    """Test that export_mcpd_config_artifacts returns empty dict when no mcpd key present."""
    agent_outputs = {"some_other_key": "value"}
    result = export_mcpd_config_artifacts(agent_outputs)
    assert result == {}


def test_export_mcpd_config_artifacts_empty_mcpd_value():
    """Test that export_mcpd_config_artifacts returns empty dict when mcpd value is empty."""
    # Test with empty string.
    agent_outputs = {"mcpd": ""}
    result = export_mcpd_config_artifacts(agent_outputs)
    assert result == {}

    # Test with whitespace only.
    agent_outputs = {"mcpd": "   \n\t  "}
    result = export_mcpd_config_artifacts(agent_outputs)
    assert result == {}


def test_export_mcpd_config_artifacts_with_binary_with_output_dir(mcpd_binary):
    """Test export with real mcpd binary and filesystem server WITH output_dir specified."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config_path = temp_path / "test_config.toml"
        output_path = temp_path / "output"
        output_path.mkdir()

        # Change to temp directory for mcpd operations.
        import os

        original_cwd = Path.cwd()
        os.chdir(temp_dir)

        try:
            # Initialize a new mcpd project and add a server.
            initialize_mcp_config(config_path)
            assert config_path.exists(), "mcpd init should create the config file"

            # Add 'filesystem' server, so we have meaningful config file contents.
            register_mcp_server(config_path, "filesystem")

            # Read (store) the config content for comparison.
            mcpd_config_content = config_path.read_text(encoding="utf-8")

            # Create agent factory outputs with mcpd config.
            agent_outputs = {"mcpd": mcpd_config_content}

            # Test the export with output_dir to verify files are created.
            result = export_mcpd_config_artifacts(agent_outputs, output_dir=output_path)

            # Should always contain the original config.
            assert ".mcpd.toml" in result
            assert result[".mcpd.toml"] == mcpd_config_content

            # Check files were created in output directory.
            assert (output_path / ".mcpd.toml").exists(), "Config file should exist in output dir"
            assert (output_path / ".mcpd.toml").read_text(encoding="utf-8") == mcpd_config_content

            # Check for the expected files in the returned output, this is what matters most.
            expected_keys = {".mcpd.toml", ".env", "secrets.prod.toml"}
            actual_keys = set(result.keys())
            assert actual_keys == expected_keys, (
                f"Expected all export files, got: {actual_keys}, missing: {expected_keys - actual_keys}"
            )

            # Just for sanity, verify export files exist in the specified output directory (side effect).
            if ".env" in result:
                assert (output_path / ".env").exists(), "Contract file should exist in output dir"
            if "secrets.prod.toml" in result:
                assert (output_path / "secrets.prod.toml").exists(), "Context file should exist in output dir"

        finally:
            os.chdir(original_cwd)


def test_export_mcpd_config_artifacts_with_binary_minimal(mcpd_binary):
    """Test export with real mcpd minimal config (no servers) using default temp dir."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config_path = temp_path / "minimal_config.toml"

        # Change to temp directory for mcpd operations.
        import os

        original_cwd = Path.cwd()
        os.chdir(temp_dir)

        try:
            # Initialize empty mcpd config (no servers).
            initialize_mcp_config(config_path)
            assert config_path.exists(), "mcpd init should create the config file"

            # Read the initialized minimal config.
            minimal_config_content = config_path.read_text(encoding="utf-8")

            # Create agent factory outputs.
            agent_outputs = {"mcpd": minimal_config_content}

            # Test with NO output_dir (uses temporary directory by default).
            result = export_mcpd_config_artifacts(agent_outputs)

            # Should contain the original config.
            assert ".mcpd.toml" in result
            assert result[".mcpd.toml"] == minimal_config_content

            # With minimal empty config, mcpd should NOT generate export files.
            expected_keys = {".mcpd.toml"}
            actual_keys = set(result.keys())
            assert actual_keys == expected_keys, f"Expected only .mcpd.toml for empty config, got: {actual_keys}"

        finally:
            os.chdir(original_cwd)


def test_export_mcpd_config_artifacts_with_binary_with_temp_dir(mcpd_binary):
    """Test export with real mcpd and filesystem server using default temp dir."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config_path = temp_path / "test_config.toml"

        # Change to temp directory for mcpd operations.
        import os

        original_cwd = Path.cwd()
        os.chdir(temp_dir)

        try:
            # Initialize mcpd config and add filesystem server.
            initialize_mcp_config(config_path)
            assert config_path.exists(), "mcpd init should create the config file"

            # Add filesystem server for meaningful config.
            register_mcp_server(config_path, "filesystem")

            # Read the config with server.
            mcpd_config_content = config_path.read_text(encoding="utf-8")

            # Create agent factory outputs.
            agent_outputs = {"mcpd": mcpd_config_content}

            # Test with NO output_dir (uses temporary directory by default).
            result = export_mcpd_config_artifacts(agent_outputs)

            # Should contain the original config.
            assert ".mcpd.toml" in result
            assert result[".mcpd.toml"] == mcpd_config_content

            # With filesystem server, should generate all export files.
            expected_keys = {".mcpd.toml", ".env", "secrets.prod.toml"}
            actual_keys = set(result.keys())
            assert actual_keys == expected_keys, (
                f"Expected all export files, got: {actual_keys}, missing: {expected_keys - actual_keys}"
            )

            # Verify export files have content.
            assert len(result[".env"]) > 0, "Contract file should have content"
            assert len(result["secrets.prod.toml"]) > 0, "Context file should have content"

        finally:
            os.chdir(original_cwd)


def test_export_mcpd_config_artifacts_with_temp_directory():
    """Test that temporary directory is used and cleaned up when output_dir is None."""
    # Create a simple config.
    config_content = """[[servers]]
name = "test-foo-mcp"
package = "npx::test-foo-mcp@2025.01.01"
"""
    agent_outputs = {"mcpd": config_content}

    # Test with default behavior (temporary directory).
    result = export_mcpd_config_artifacts(agent_outputs)

    # Should return the config content.
    assert ".mcpd.toml" in result
    assert result[".mcpd.toml"] == config_content

    # Note: We can't verify temp dir cleanup directly since it happens automatically,
    # so the test passing without errors indicates proper cleanup.


def test_export_mcpd_config_artifacts_with_output_dir():
    """Test that files persist when output_dir is provided."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test_output"
        output_path.mkdir()

        # Create a config.
        config_content = """[[servers]]
name = "test-server"
package = "uvx::test-server-mcp@1.2.3"
"""
        agent_outputs = {"mcpd": config_content}

        # Test with specified output directory.
        result = export_mcpd_config_artifacts(agent_outputs, output_dir=output_path)

        # Should return the config content.
        assert ".mcpd.toml" in result
        assert result[".mcpd.toml"] == config_content

        # Files should persist in output directory.
        assert (output_path / ".mcpd.toml").exists(), "Config file should persist in output dir"
        assert (output_path / ".mcpd.toml").read_text(encoding="utf-8") == config_content

        # After function returns, files should still exist (not cleaned up).
        assert output_path.exists(), "Output directory should still exist"
        assert (output_path / ".mcpd.toml").exists(), "Files should persist after function returns"


def test_export_mcpd_config_artifacts_mcpd_failure():
    """Test that function handles mcpd export failure gracefully."""
    from unittest.mock import MagicMock, patch

    config_content = """[[servers]]
name = "test-server"
package = "uvx::test-server-mcp@1.2.3"
"""
    agent_outputs = {"mcpd": config_content}

    # Mock run_binary to simulate mcpd failure
    with patch("agent_factory.utils.io_utils.run_binary") as mock_run_binary:
        mock_run_binary.side_effect = RuntimeError("mcpd export failed")

        # Function should handle the error and still return the original config
        result = export_mcpd_config_artifacts(agent_outputs)

        # Should at least return the original config even if export fails
        assert ".mcpd.toml" in result
        assert result[".mcpd.toml"] == config_content

        # Export files won't be present due to failure
        assert ".env" not in result
        assert "secrets.prod.toml" not in result
