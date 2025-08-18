import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agent_factory.utils.mcpd_utils import (
    export_mcpd_config_artifacts,
    initialize_mcp_config,
    register_mcp_server,
    run_binary,
)


class TestInitializeMcpConfig:
    """Tests for initialize_mcp_config function."""

    def test_initialize_mcp_config_custom_path(self):
        """Test initialization with custom config path."""
        with patch("agent_factory.utils.mcpd_utils.run_binary") as mock_run_binary:
            mock_run_binary.return_value = {"return_code": 0}

            custom_path = Path("/custom/path/.mcpd.toml")
            result = initialize_mcp_config(config_path=custom_path)

            assert result == 0
            mock_run_binary.assert_called_once_with(
                "mcpd", ["init", f"--config-file={custom_path}"], ignore_response=True
            )

    def test_initialize_mcp_config_runtime_error(self):
        """Test that RuntimeError from run_binary is propagated."""
        with patch("agent_factory.utils.mcpd_utils.run_binary") as mock_run_binary:
            mock_run_binary.side_effect = RuntimeError("mcpd init failed")

            config_path = Path("/tmp/.mcpd.toml")
            with pytest.raises(RuntimeError, match="mcpd init failed"):
                initialize_mcp_config(config_path)


class TestRegisterMcpServer:
    """Tests for register_mcp_server function."""

    @pytest.mark.parametrize(
        "name,version,tools,expected_args",
        [
            ("github", None, None, ["add", "github"]),
            ("github", "v1.2.3", None, ["add", "github", "--version", "v1.2.3"]),
            ("github", None, ["tool1", "tool2"], ["add", "github", "--tool", "tool1", "--tool", "tool2"]),
            ("slack", "v2.0.0", ["tool1"], ["add", "slack", "--version", "v2.0.0", "--tool", "tool1"]),
        ],
    )
    def test_register_mcp_server(self, name, version, tools, expected_args):
        """Test registering server with various parameters."""
        with patch("agent_factory.utils.mcpd_utils.run_binary") as mock_run_binary:
            mock_run_binary.return_value = {"return_code": 0}

            config_path = Path("/test/config.toml")
            result = register_mcp_server(name=name, config_path=config_path, version=version, tools=tools)

            assert result == 0

            mock_run_binary.assert_called_once_with(
                "mcpd",
                [expected_args[0], expected_args[1]] + [f"--config-file={config_path}"] + expected_args[2:],
                ignore_response=True,
            )

    def test_register_mcp_server_runtime_error(self):
        """Test that RuntimeError from run_binary is propagated."""
        with patch("agent_factory.utils.mcpd_utils.run_binary") as mock_run_binary:
            mock_run_binary.side_effect = RuntimeError("mcpd add failed")

            config_path = Path("/test/config.toml")
            with pytest.raises(RuntimeError, match="mcpd add failed"):
                register_mcp_server(name="github", config_path=config_path)


class TestExportMcpdConfigArtifacts:
    """Tests for export_mcpd_config_artifacts function."""

    mock_mcpd_toml = MagicMock(spec=Path)
    mock_mcpd_toml.exists.return_value = True
    mock_mcpd_toml.read_text.return_value = "mcpd toml content"
    mock_mcpd_toml.__str__.return_value = "/tmp/testdir/.mcpd.toml"

    mock_env_contract = MagicMock(spec=Path)
    mock_env_contract.exists.return_value = True
    mock_env_contract.read_text.return_value = "env content"
    mock_env_contract.__str__.return_value = "/tmp/testdir/.env"

    mock_secrets_context = MagicMock(spec=Path)
    mock_secrets_context.exists.return_value = True
    mock_secrets_context.read_text.return_value = "secrets content"
    mock_secrets_context.__str__.return_value = "/tmp/testdir/secrets.prod.toml"

    def _truediv_side_effect(self, file_name):
        """Side effect for Path.__truediv__."""
        if file_name == ".mcpd.toml":
            return self.mock_mcpd_toml
        if file_name == ".env":
            return self.mock_env_contract
        if file_name == "secrets.prod.toml":
            return self.mock_secrets_context
        return MagicMock()

    @pytest.mark.parametrize(
        "agent_factory_outputs",
        [{"mcp_servers": None}, {"mcp_servers": []}],
    )
    @patch("agent_factory.utils.mcpd_utils.logger")
    def test_export_no_mcp_servers(self, mock_logger, agent_factory_outputs):
        """Test that no artifacts are exported if mcp_servers is missing or empty."""
        result = export_mcpd_config_artifacts(agent_factory_outputs)
        assert result == {}
        mock_logger.warning.assert_called_once_with(
            "Agent Factory output does not contain MCP servers, no related artifacts will be exported."
        )

    @patch("agent_factory.utils.mcpd_utils.Path")
    @patch("agent_factory.utils.mcpd_utils.run_binary")
    @patch("agent_factory.utils.mcpd_utils.register_mcp_server")
    @patch("agent_factory.utils.mcpd_utils.initialize_mcp_config")
    @patch("tempfile.TemporaryDirectory")
    def test_export_artifacts_success(
        self, mock_tmpdir, mock_init_config, mock_register_server, mock_run_binary, mock_path
    ):
        """Test successful export of all artifacts when mcp_servers are present."""
        mock_tmpdir.return_value.__enter__.return_value = "/tmp/testdir"
        mock_run_binary.return_value = {"return_code": 0}

        mock_work_dir = MagicMock(spec=Path)
        mock_path.return_value = mock_work_dir
        mock_work_dir.__truediv__.side_effect = self._truediv_side_effect

        agent_factory_outputs = {
            "mcp_servers": [
                {"name": "github", "tools": ["list_repos"]},
                {"name": "jira"},
            ]
        }

        result = export_mcpd_config_artifacts(agent_factory_outputs)

        assert result == {
            ".mcpd.toml": "mcpd toml content",
            ".env": "env content",
            "secrets.prod.toml": "secrets content",
        }

        mock_path.assert_called_once_with("/tmp/testdir")
        mock_init_config.assert_called_once_with(self.mock_mcpd_toml)

        assert mock_register_server.call_count == 2
        mock_register_server.assert_any_call("github", config_path=self.mock_mcpd_toml, tools=["list_repos"])
        mock_register_server.assert_any_call("jira", config_path=self.mock_mcpd_toml, tools=None)

        mock_run_binary.assert_called_once_with(
            "mcpd",
            [
                "config",
                "export",
                "--config-file",
                "/tmp/testdir/.mcpd.toml",
                "--contract-output",
                "/tmp/testdir/.env",
                "--context-output",
                "/tmp/testdir/secrets.prod.toml",
            ],
            ignore_response=True,
        )

    @patch("agent_factory.utils.mcpd_utils.Path")
    @patch("agent_factory.utils.mcpd_utils.run_binary")
    @patch("agent_factory.utils.mcpd_utils.register_mcp_server")
    @patch("agent_factory.utils.mcpd_utils.initialize_mcp_config")
    @patch("tempfile.TemporaryDirectory")
    def test_export_fails(self, mock_tmpdir, mock_init_config, mock_register_server, mock_run_binary, mock_path):
        """Test that RuntimeError is raised when mcpd export fails."""
        mock_tmpdir.return_value.__enter__.return_value = "/tmp/testdir"
        mock_run_binary.return_value = {"return_code": 1}

        mock_work_dir = MagicMock(spec=Path)
        mock_path.return_value = mock_work_dir
        mock_work_dir.__truediv__.side_effect = self._truediv_side_effect

        agent_factory_outputs = {"mcp_servers": [{"name": "github"}]}

        with pytest.raises(RuntimeError, match="Failed to export MCP config"):
            export_mcpd_config_artifacts(agent_factory_outputs)

    @patch("agent_factory.utils.mcpd_utils.Path")
    @patch("agent_factory.utils.mcpd_utils.run_binary")
    @patch("agent_factory.utils.mcpd_utils.register_mcp_server")
    @patch("agent_factory.utils.mcpd_utils.initialize_mcp_config")
    @patch("tempfile.TemporaryDirectory")
    def test_export_with_output_dir(
        self, mock_tmpdir, mock_init_config, mock_register_server, mock_run_binary, mock_path
    ):
        """Test artifact export when an output_dir is provided."""
        output_dir = Path("/persistent/dir")
        mock_run_binary.return_value = {"return_code": 0}

        mock_work_dir = MagicMock(spec=Path)

        def path_side_effect(p):
            if p == output_dir:
                return mock_work_dir
            return MagicMock()

        mock_path.side_effect = path_side_effect
        mock_work_dir.__truediv__.side_effect = self._truediv_side_effect

        agent_factory_outputs = {"mcp_servers": [{"name": "github"}]}

        result = export_mcpd_config_artifacts(agent_factory_outputs, output_dir=output_dir)

        assert result is not None
        assert ".mcpd.toml" in result

        mock_tmpdir.assert_not_called()
        mock_path.assert_called_once_with(output_dir)
        mock_init_config.assert_called_once_with(self.mock_mcpd_toml)
        mock_register_server.assert_called_once_with("github", config_path=self.mock_mcpd_toml, tools=None)


class TestRunBinary:
    """Tests for run_binary function."""

    @patch("subprocess.run")
    def test_run_binary_success(self, mock_subprocess_run):
        """Test successful binary execution with JSON output."""
        mock_result = MagicMock()
        mock_result.stdout = '{"key": "value"}'
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result

        result = run_binary("path/to/binary", ["arg1"])

        assert result == {"key": "value"}
        mock_subprocess_run.assert_called_once_with(
            ["path/to/binary", "arg1"], capture_output=True, text=True, check=True
        )

    @patch("subprocess.run")
    def test_run_binary_ignore_response(self, mock_subprocess_run):
        """Test successful binary execution when response is ignored."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result

        result = run_binary("path/to/binary", ["arg1"], ignore_response=True)

        assert result == {"return_code": 0}
        mock_subprocess_run.assert_called_once_with(
            ["path/to/binary", "arg1"], capture_output=True, text=True, check=True
        )

    @patch("subprocess.run")
    def test_run_binary_called_process_error(self, mock_subprocess_run):
        """Test that RuntimeError is raised on subprocess.CalledProcessError."""
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="error")

        with pytest.raises(RuntimeError, match="Subprocess failed"):
            run_binary("path/to/binary", ["arg1"])

    @patch("subprocess.run")
    def test_run_binary_json_decode_error(self, mock_subprocess_run):
        """Test that ValueError is raised on invalid JSON output."""
        mock_result = MagicMock()
        mock_result.stdout = "not json"
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result

        with pytest.raises(ValueError, match="Invalid JSON output"):
            run_binary("path/to/binary", ["arg1"])

    @patch("subprocess.run")
    def test_run_binary_file_not_found_error(self, mock_subprocess_run):
        """Test that RuntimeError is raised on FileNotFoundError."""
        mock_subprocess_run.side_effect = FileNotFoundError

        with pytest.raises(RuntimeError, match="Binary not found: path/to/binary"):
            run_binary("path/to/binary", ["arg1"])

    @patch("subprocess.run")
    def test_run_binary_unexpected_error(self, mock_subprocess_run):
        """Test that RuntimeError is raised on unexpected exceptions."""
        mock_subprocess_run.side_effect = Exception("Unexpected error")

        with pytest.raises(RuntimeError, match="An unexpected error occurred during binary execution"):
            run_binary("path/to/binary", ["arg1"])
