import shutil
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agent_factory.factory_tools import (
    BASE_TEMP_CONFIG_DIR,
    cleanup_temp_config_dir,
    create_temp_config_dir,
    initialize_mcp_config,
    read_temp_config_file,
    register_mcp_server,
)


class TestInitializeMcpConfig:
    """Tests for initialize_mcp_config function."""

    def test_initialize_mcp_config_custom_path(self):
        """Test initialization with custom config path."""
        with patch("agent_factory.factory_tools.run_binary") as mock_run_binary:
            mock_run_binary.return_value = {}

            custom_path = Path("/custom/path/.mcpd.toml")
            result = initialize_mcp_config(config_path=custom_path)

            assert result is True
            mock_run_binary.assert_called_once_with(
                "mcpd", ["init", f"--config-file={custom_path}"], ignore_response=True
            )

    def test_initialize_mcp_config_runtime_error(self):
        """Test that RuntimeError from run_binary is propagated."""
        with patch("agent_factory.factory_tools.run_binary") as mock_run_binary:
            mock_run_binary.side_effect = RuntimeError("mcpd init failed")

            config_path = Path("/tmp/.mcpd.toml")
            with pytest.raises(RuntimeError, match="mcpd init failed"):
                initialize_mcp_config(config_path)


class TestRegisterMcpServer:
    """Tests for register_mcp_server function."""

    def test_register_mcp_server_name_only(self):
        """Test registering server with name only."""
        with patch("agent_factory.factory_tools.run_binary") as mock_run_binary:
            mock_run_binary.return_value = {}

            config_path = Path("/test/config.toml")
            result = register_mcp_server(config_path, "github")

            assert result is True

            mock_run_binary.assert_called_once_with(
                "mcpd", ["add", "github", f"--config-file={config_path}"], ignore_response=True
            )

    def test_register_mcp_server_with_version(self):
        """Test registering server with version specified."""
        with patch("agent_factory.factory_tools.run_binary") as mock_run_binary:
            mock_run_binary.return_value = {}

            config_path = Path("/test/config.toml")
            result = register_mcp_server(config_path, "github", version="v1.2.3")

            assert result is True

            mock_run_binary.assert_called_once_with(
                "mcpd", ["add", "github", f"--config-file={config_path}", "--version", "v1.2.3"], ignore_response=True
            )

    def test_register_mcp_server_with_tools(self):
        """Test registering server with tools subset specified."""
        with patch("agent_factory.factory_tools.run_binary") as mock_run_binary:
            mock_run_binary.return_value = {}

            config_path = Path("/test/config.toml")
            tools = ["create_issue", "list_repos"]
            result = register_mcp_server(config_path, "github", tools=tools)

            assert result is True

            expected_args = [
                "add",
                "github",
                f"--config-file={config_path}",
                "--tool",
                "create_issue",
                "--tool",
                "list_repos",
            ]
            mock_run_binary.assert_called_once_with("mcpd", expected_args, ignore_response=True)

    def test_register_mcp_server_all_parameters(self):
        """Test registering server with all parameters."""
        with patch("agent_factory.factory_tools.run_binary") as mock_run_binary:
            mock_run_binary.return_value = {}

            config_path = Path("/test/config.toml")
            tools = ["tool1", "tool2"]
            result = register_mcp_server(config_path, "slack", version="v2.0.0", tools=tools)

            assert result is True

            expected_args = [
                "add",
                "slack",
                f"--config-file={config_path}",
                "--version",
                "v2.0.0",
                "--tool",
                "tool1",
                "--tool",
                "tool2",
            ]
            mock_run_binary.assert_called_once_with("mcpd", expected_args, ignore_response=True)

    def test_register_mcp_server_runtime_error(self):
        """Test that RuntimeError from run_binary is propagated."""
        with patch("agent_factory.factory_tools.run_binary") as mock_run_binary:
            mock_run_binary.side_effect = RuntimeError("mcpd add failed")

            config_path = Path("/test/config.toml")
            with pytest.raises(RuntimeError, match="mcpd add failed"):
                register_mcp_server(config_path, "github")


class TestTempConfigDir:
    """Tests for temporary config directory functions."""

    def test_create_temp_config_dir_success(self):
        """Test successful creation of temp config directory."""
        with tempfile.TemporaryDirectory() as test_base:
            test_base_path = Path(test_base)

            with patch("agent_factory.factory_tools.BASE_TEMP_CONFIG_DIR", test_base_path):
                config_path, dir_uuid, deletion_key = create_temp_config_dir()

                # Check return types.
                assert isinstance(config_path, Path)
                assert isinstance(dir_uuid, uuid.UUID)
                assert isinstance(deletion_key, str)

                # Check config path structure.
                assert config_path.name == ".mcpd.toml"
                assert config_path.parent.name == str(dir_uuid)

                # Check directory was created.
                dir_path = test_base_path / str(dir_uuid)
                assert dir_path.exists()
                assert dir_path.is_dir()

                # Check key file was created.
                key_file = dir_path / "_key.txt"
                assert key_file.exists()
                assert key_file.read_text() == deletion_key

    def test_create_temp_config_dir_base_dir_created(self):
        """Test that base directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as test_base:
            test_base_path = Path(test_base) / "nonexistent" / "path"

            with patch("agent_factory.factory_tools.BASE_TEMP_CONFIG_DIR", test_base_path):
                config_path, dir_uuid, deletion_key = create_temp_config_dir()

                # Check base directory was created.
                assert test_base_path.exists()

                # Check temp directory was created.
                dir_path = test_base_path / str(dir_uuid)
                assert dir_path.exists()

    def test_create_temp_config_dir_os_error(self):
        """Test error handling for OS errors."""
        with patch("agent_factory.factory_tools.BASE_TEMP_CONFIG_DIR") as mock_base:
            mock_base.mkdir.side_effect = OSError("Permission denied")

            with pytest.raises(RuntimeError, match="Cannot create temp config dir"):
                create_temp_config_dir()

    def test_read_temp_config_file_success(self):
        """Test successful reading of temp config file."""
        with tempfile.TemporaryDirectory() as test_base:
            test_base_path = Path(test_base)

            # Create test structure.
            test_uuid = uuid.uuid4()
            dir_path = test_base_path / str(test_uuid)
            dir_path.mkdir()

            config_file = dir_path / ".mcpd.toml"
            test_content = "test config content"
            config_file.write_text(test_content)

            with patch("agent_factory.factory_tools.BASE_TEMP_CONFIG_DIR", test_base_path):
                result = read_temp_config_file(test_uuid)
                assert result == test_content

    def test_read_temp_config_file_dir_not_exists(self):
        """Test error when directory doesn't exist."""
        with tempfile.TemporaryDirectory() as test_base:
            test_base_path = Path(test_base)

            non_existent_uuid = uuid.uuid4()

            with patch("agent_factory.factory_tools.BASE_TEMP_CONFIG_DIR", test_base_path):
                with pytest.raises(RuntimeError, match=f"Temp config directory doesn't exist: {non_existent_uuid}"):
                    read_temp_config_file(non_existent_uuid)

    def test_read_temp_config_file_file_not_exists(self):
        """Test error when config file doesn't exist."""
        with tempfile.TemporaryDirectory() as test_base:
            test_base_path = Path(test_base)

            # Create directory but no config file.
            test_uuid = uuid.uuid4()
            dir_path = test_base_path / str(test_uuid)
            dir_path.mkdir()

            with patch("agent_factory.factory_tools.BASE_TEMP_CONFIG_DIR", test_base_path):
                with pytest.raises(RuntimeError, match="Temp config file doesn't exist"):
                    read_temp_config_file(test_uuid)

    def test_read_temp_config_file_path_traversal_protection(self):
        """Test that path traversal attempts are blocked."""
        with tempfile.TemporaryDirectory() as test_base:
            test_base_path = Path(test_base)

            # Create a malicious symlink.
            test_uuid = uuid.uuid4()
            dir_path = test_base_path / str(test_uuid)
            dir_path.mkdir()

            # Create file outside base dir.
            outside_file = test_base_path.parent / "outside.toml"
            outside_file.write_text("malicious content")

            # Create symlink to outside file.
            config_link = dir_path / ".mcpd.toml"
            config_link.symlink_to(outside_file)

            with patch("agent_factory.factory_tools.BASE_TEMP_CONFIG_DIR", test_base_path):
                with pytest.raises(RuntimeError, match="Attempted to read file outside of allowed directory"):
                    read_temp_config_file(test_uuid)

            outside_file.unlink()

    def test_cleanup_temp_config_dir_success(self):
        """Test successful cleanup of temp config directory."""
        with tempfile.TemporaryDirectory() as test_base:
            test_base_path = Path(test_base)

            with patch("agent_factory.factory_tools.BASE_TEMP_CONFIG_DIR", test_base_path):
                # Create temp dir using the actual function.
                config_path, dir_uuid, deletion_key = create_temp_config_dir()

                # Verify directory exists.
                dir_path = test_base_path / str(dir_uuid)
                assert dir_path.exists()

                # Clean up.
                result = cleanup_temp_config_dir(dir_uuid, deletion_key)

                # Verify success and directory is deleted.
                assert result is True
                assert not dir_path.exists()

    def test_cleanup_temp_config_dir_wrong_key(self):
        """Test that cleanup silently fails with wrong deletion key."""
        with tempfile.TemporaryDirectory() as test_base:
            test_base_path = Path(test_base)

            with patch("agent_factory.factory_tools.BASE_TEMP_CONFIG_DIR", test_base_path):
                # Create temp dir.
                config_path, dir_uuid, deletion_key = create_temp_config_dir()

                # Try to delete with wrong key - should return False.
                wrong_key = str(uuid.uuid4())
                result = cleanup_temp_config_dir(dir_uuid, wrong_key)

                # Verify failed deletion.
                assert result is False
                dir_path = test_base_path / str(dir_uuid)
                assert dir_path.exists(), "Directory should still exist with wrong key"

                # Cleanup with correct key.
                result = cleanup_temp_config_dir(dir_uuid, deletion_key)
                assert result is True

                # Now it should be deleted.
                assert not dir_path.exists(), "Directory should be deleted with correct key"

    def test_cleanup_temp_config_dir_not_exists(self):
        """Test error when trying to cleanup non-existent directory."""
        with tempfile.TemporaryDirectory() as test_base:
            test_base_path = Path(test_base)

            non_existent_uuid = uuid.uuid4()
            deletion_key = str(uuid.uuid4())

            with patch("agent_factory.factory_tools.BASE_TEMP_CONFIG_DIR", test_base_path):
                with pytest.raises(RuntimeError, match=f"Directory with UUID '{non_existent_uuid}' not found"):
                    cleanup_temp_config_dir(non_existent_uuid, deletion_key)

    def test_cleanup_temp_config_dir_path_traversal_protection(self):
        """Test that path traversal in cleanup is blocked."""
        with tempfile.TemporaryDirectory() as test_base:
            test_base_path = Path(test_base)

            # Create a directory outside base.
            outside_dir = test_base_path.parent / "outside_dir"
            outside_dir.mkdir(exist_ok=True)

            # Create fake key file.
            key_file = outside_dir / "_key.txt"
            deletion_key = str(uuid.uuid4())
            key_file.write_text(deletion_key)

            # Try to use a path that would traverse outside.
            fake_uuid = f"../{outside_dir.name}"

            with patch("agent_factory.factory_tools.BASE_TEMP_CONFIG_DIR", test_base_path):
                with pytest.raises(RuntimeError, match="Attempted to delete directory outside of allowed directory"):
                    cleanup_temp_config_dir(fake_uuid, deletion_key)

            # Verify outside directory still exists.
            assert outside_dir.exists()

            shutil.rmtree(outside_dir)
