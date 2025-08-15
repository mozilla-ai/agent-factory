import sys
import textwrap
from pathlib import Path

import pytest
import yaml
from any_agent import AgentTrace

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def use_cases():
    use_cases_path = project_root / "tests/generation/use_cases.yaml"
    with use_cases_path.open() as f:
        return yaml.safe_load(f)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-artifacts",
        action="store_true",
        default=False,
        help="Overwrite/Update the output artifacts stored in `tests/artifacts`.",
    )
    parser.addoption(
        "--artifacts-dir",
        action="store",
        default=str(Path(__file__).parent / "artifacts"),
        help="Directory containing the generated artifacts (default: tests/artifacts)",
    )
    parser.addoption("--prompt-id", action="store", default="test_prompt", help="ID of the prompt being tested")


@pytest.fixture(scope="session")
def artifacts_dir(request):
    path = Path(request.config.getoption("--artifacts-dir"))
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def prompt_id(request):
    return request.config.getoption("--prompt-id")


@pytest.fixture(scope="session")
def max_attempts(request, use_cases):
    """Fixture to provide max_attempts from the use case YAML based on --prompt-id."""
    prompt_id = request.config.getoption("--prompt-id")
    return use_cases[prompt_id]["max_attempts"]


@pytest.fixture(scope="session")
def min_successes(request, use_cases):
    """Fixture to provide min_successes from the use case YAML based on --prompt-id."""
    prompt_id = request.config.getoption("--prompt-id")
    return use_cases[prompt_id]["min_successes"]


@pytest.fixture(scope="session")
def agent_dir(artifacts_dir, prompt_id):
    """Fixture to get the agent directory path for the current prompt."""
    return artifacts_dir / prompt_id


@pytest.fixture(scope="session")
def agent_file(agent_dir):
    """Fixture to get the agent file path for the current prompt."""
    return agent_dir / "agent.py"


@pytest.fixture(scope="session")
def toml_file(agent_dir):
    """Fixture to get the agent file path for the current prompt."""
    return agent_dir / ".mcpd.toml"


@pytest.fixture(scope="session")
def generated_agent_code(agent_file):
    """Fixture to read the agent code."""
    return agent_file.read_text()


@pytest.fixture(scope="session")
def generated_agent_toml(toml_file):
    """Fixture to read the agent .mcpd.toml file."""
    return toml_file.read_text()


@pytest.fixture(scope="module")
def common_eval_testing_data_path():
    return Path("tests/generated_agent_evaluation/data/")


@pytest.fixture(scope="module")
def sample_evaluation_json_file(common_eval_testing_data_path):
    return (common_eval_testing_data_path / "sample_evaluation_case.json").read_text()


@pytest.fixture(scope="module")
def sample_agent_eval_trace_json(common_eval_testing_data_path):
    return (common_eval_testing_data_path / "sample_agent_eval_trace.json").read_text()
