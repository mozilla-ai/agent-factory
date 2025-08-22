import sys
from pathlib import Path

import pytest
import yaml
from any_agent.tracing.agent_trace import AgentTrace

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
def artifacts_dir(request: pytest.FixtureRequest) -> Path:
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
def requires_mcpd(request, use_cases):
    """Fixture to provide requires_mcpd from the use case YAML based on --prompt-id."""
    prompt_id = request.config.getoption("--prompt-id")
    return use_cases[prompt_id]["requires_mcpd"]


@pytest.fixture(scope="session")
def agent_dir(artifacts_dir: Path, prompt_id: str) -> Path:
    """Fixture to get the agent directory path for the current prompt."""
    return artifacts_dir / prompt_id


@pytest.fixture(scope="session")
def agent_file(agent_dir: Path) -> Path:
    """Fixture to get the agent file path for the current prompt."""
    return agent_dir / "agent.py"


@pytest.fixture(scope="session")
def toml_file(agent_dir: Path) -> Path:
    """Fixture to get the agent file path for the current prompt."""
    return agent_dir / ".mcpd.toml"


@pytest.fixture(scope="session")
def generated_agent_code(agent_file: Path) -> str:
    """Fixture to read the agent code."""
    if agent_file.exists():
        return agent_file.read_text()
    else:
        return ""


@pytest.fixture(scope="session")
def generated_agent_toml(toml_file: Path) -> str:
    """Fixture to read the agent .mcpd.toml file."""
    if toml_file.exists():
        return toml_file.read_text()
    else:
        return ""


@pytest.fixture
def agent_factory_trace_file(artifacts_dir: Path, prompt_id: str) -> Path:
    """Fixture to get the trace file path for the current prompt."""
    return artifacts_dir / prompt_id / "agent_factory_trace.json"


@pytest.fixture
def agent_factory_trace(agent_factory_trace_file: Path) -> AgentTrace:
    """Fixture to load and validate the trace for the current prompt."""
    return AgentTrace.model_validate_json(agent_factory_trace_file.read_text())


@pytest.fixture(scope="module")
def common_eval_testing_data_path() -> Path:
    return Path("tests/generated_agent_evaluation/data/")


@pytest.fixture(scope="module")
def sample_evaluation_json_file(common_eval_testing_data_path: Path) -> str:
    return (common_eval_testing_data_path / "sample_evaluation_case.json").read_text()


@pytest.fixture(scope="module")
def sample_agent_eval_trace_json(common_eval_testing_data_path: Path) -> str:
    return (common_eval_testing_data_path / "sample_agent_eval_trace.json").read_text()
