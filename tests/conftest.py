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


@pytest.fixture
def agent_file(artifacts_dir, prompt_id):
    """Fixture to get the agent file path for the current prompt."""
    return artifacts_dir / prompt_id / "agent.py"


@pytest.fixture
def generated_agent_code(agent_file):
    """Fixture to read the agent code."""
    return agent_file.read_text()


@pytest.fixture
def agent_factory_trace_file(artifacts_dir: Path, prompt_id: str) -> Path:
    """Fixture to get the trace file path for the current prompt."""
    return artifacts_dir / prompt_id / "agent_factory_trace.json"


@pytest.fixture
def agent_factory_trace(agent_factory_trace_file: Path) -> AgentTrace:
    """Fixture to load and validate the trace for the current prompt."""
    return AgentTrace.model_validate_json(agent_factory_trace_file.read_text())


@pytest.fixture(scope="session")
def prompt_id(request):
    return request.config.getoption("--prompt-id")


@pytest.fixture(scope="module")
def common_eval_testing_data_path():
    return Path("tests/generated_agent_evaluation/data/")


@pytest.fixture(scope="module")
def sample_evaluation_json_file(common_eval_testing_data_path):
    return (common_eval_testing_data_path / "sample_evaluation_case.json").read_text()


@pytest.fixture(scope="module")
def sample_agent_eval_trace_json(common_eval_testing_data_path):
    return (common_eval_testing_data_path / "sample_agent_eval_trace.json").read_text()


@pytest.fixture(scope="session")
def cost_tracker():
    """A session-scoped fixture to track and summarize the total cost of API calls
    during the test session.
    """
    run_costs = []
    yield run_costs

    # The code below runs AFTER all tests in the session are complete
    if not run_costs:
        return

    total_cost = sum(run_costs)
    avg_cost = total_cost / len(run_costs) if run_costs else 0

    summary_output = textwrap.dedent(f"""
        {"=" * 60}
        COST SUMMARY
        {"-" * 60}
        Number of runs: {len(run_costs)}
        Total cost: ${total_cost:.3f}
        Average cost per run: ${avg_cost:.3f}
        {"=" * 60}
    """)
    print(summary_output)
