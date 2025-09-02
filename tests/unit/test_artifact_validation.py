"""Tests for artifact validation utilities."""

import json
from unittest.mock import patch

import pytest

from agent_factory.schemas import CodeSnippet
from agent_factory.utils.artifact_validation import (
    prepare_python_code,
    validate_dependencies,
    validate_python_syntax,
)


class TestValidateDependencies:
    """Test the validate_dependencies function."""

    def test_adds_uv_when_uvx_in_tools(self, sample_generator_agent_response_json):
        """Test that uv is added when uvx is found in tools."""
        tools = sample_generator_agent_response_json["tools"] + "\n# uvx install some-mcp-server"
        dependencies = ["any-agent[all]==0.25.0", "python-dotenv", "beautifulsoup4", "requests", "fire"]

        result = validate_dependencies(tools, dependencies)

        expected = "\n".join(dependencies) + "\nuv"

        expected_sorted = sorted([line for line in expected.split("\n") if line])
        result_sorted = sorted([line for line in result.split("\n") if line])

        assert result_sorted == expected_sorted


class TestValidatePythonSyntax:
    """Test the validate_python_syntax function."""

    def create_llm_response(self, mock_llm_response_factory, code_str: str):
        """Helper to build a mocked LLM response payload for a given code string."""
        return mock_llm_response_factory(content=json.dumps({"code": code_str}))

    def test_validate_python_syntax_with_valid_code(self):
        """Test validate_python_syntax with already valid code."""
        valid_code = "def my_func():\n    print('hello')"
        with patch("agent_factory.utils.artifact_validation.fix_python_syntax_errors") as mock_fix:
            result = validate_python_syntax(valid_code)
            assert result.code == valid_code
            mock_fix.assert_not_called()

    def test_validate_python_syntax_fixes_invalid_code(self, mock_llm_response_factory):
        """Test that invalid code is fixed on the first attempt."""
        invalid_code = "def my_func()\n    print('hello')"
        valid_code = "def my_func():\n    print('hello')"
        custom_response = self.create_llm_response(mock_llm_response_factory, valid_code)

        with patch(
            "agent_factory.utils.artifact_validation.completion", return_value=custom_response
        ) as mock_completion:
            result = validate_python_syntax(invalid_code)
            assert result.code == valid_code
            mock_completion.assert_called_once()

    def test_validate_python_syntax_fails_after_retries(self, mock_llm_response_factory):
        """Test that a SyntaxError is raised after max_retries."""
        invalid_code = "def my_func()\n    print('hello')"
        llm_response_content = json.dumps({"code": invalid_code})  # LLM keeps returning invalid code

        custom_response = mock_llm_response_factory(content=llm_response_content)

        with patch(
            "agent_factory.utils.artifact_validation.completion", return_value=custom_response
        ) as mock_completion:
            with pytest.raises(SyntaxError):
                validate_python_syntax(invalid_code, max_retries=2)
            assert mock_completion.call_count == 2

    def test_validate_python_syntax_recursive_fix(self, mock_llm_response_factory):
        """Test that code is fixed after more than one attempt."""
        initial_invalid_code = "def my_func()\n    print('hello')"
        intermediate_invalid_code = "def my_func():\nprint('hello')"  # Wrong indentation
        valid_code = "def my_func():\n    print('hello')"

        llm_response_1 = self.create_llm_response(mock_llm_response_factory, intermediate_invalid_code)
        llm_response_2 = self.create_llm_response(mock_llm_response_factory, valid_code)

        with patch(
            "agent_factory.utils.artifact_validation.completion", side_effect=[llm_response_1, llm_response_2]
        ) as mock_completion:
            result = validate_python_syntax(initial_invalid_code, max_retries=3)
            assert result.code == valid_code
            assert mock_completion.call_count == 2


class TestPreparePythonCode:
    """Test the prepare_python_code function."""

    @patch("agent_factory.utils.artifact_validation.validate_python_syntax")
    @patch("agent_factory.utils.artifact_validation.clean_python_code_with_autoflake")
    def test_prepare_python_code_happy_path(self, mock_clean, mock_validate):
        """Test prepare_python_code with valid code."""
        code = "import os\ndef my_func():\n    print('hello')"
        cleaned_code = "def my_func():\n    print('hello')"
        validated_code_snippet = CodeSnippet(code=cleaned_code)

        mock_clean.return_value = cleaned_code
        mock_validate.return_value = validated_code_snippet

        result = prepare_python_code(code)

        mock_clean.assert_called_once_with(code)
        mock_validate.assert_called_once_with(cleaned_code, max_retries=3, attempt=1, model="gpt-4o-mini")
        assert result == validated_code_snippet

    @patch("agent_factory.utils.artifact_validation.validate_python_syntax", side_effect=SyntaxError("Test error"))
    @patch("agent_factory.utils.artifact_validation.clean_python_code_with_autoflake")
    def test_prepare_python_code_raises_syntax_error(self, mock_clean, mock_validate):
        """Test that prepare_python_code propagates SyntaxError."""
        code = "def my_func()\n    print('hello')"
        mock_clean.return_value = code

        with pytest.raises(SyntaxError):
            prepare_python_code(code)

        mock_clean.assert_called_once_with(code)
        mock_validate.assert_called_once_with(code, max_retries=3, attempt=1, model="gpt-4o-mini")
