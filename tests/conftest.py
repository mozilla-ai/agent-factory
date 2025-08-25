import sys
from pathlib import Path

import pytest
import yaml
from any_agent.tracing.agent_trace import AgentTrace
from rich.console import Console
from rich.table import Table

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


@pytest.fixture(scope="session")
def metrics_tracker():
    """Session-scoped tracker that records per-run metrics as dictionaries.

    Each run should append a dict with keys:
    - cost (float): incurred for LLM API calls
    - duration (timedelta): duration to complete the task
    - n_turns (int): number of turns taken by the agent
    - n_tokens (int): total tokens used by the agent
    - n_input_tokens (int): input tokens
    - n_output_tokens (int): output tokens
    At the end of the session, a consolidated summary of totals and averages is printed.
    """
    run_metrics: list[dict] = []
    yield run_metrics

    # AFTER all tests in the session are complete
    if not run_metrics:
        return

    n_runs = len(run_metrics)
    total_cost = sum(m.get("cost", 0.0) for m in run_metrics)
    total_duration_seconds = sum(m.get("duration", 0.0) for m in run_metrics)
    total_turns = sum(m.get("n_turns", 0) for m in run_metrics)
    total_tokens = sum(m.get("n_tokens", 0) for m in run_metrics)
    total_input_tokens = sum(m.get("n_input_tokens", 0) for m in run_metrics)
    total_output_tokens = sum(m.get("n_output_tokens", 0) for m in run_metrics)

    avg_cost = total_cost / n_runs if n_runs else 0.0
    avg_duration_seconds = total_duration_seconds / n_runs if n_runs else 0.0
    avg_turns = total_turns / n_runs if n_runs else 0.0
    avg_tokens = total_tokens / n_runs if n_runs else 0.0
    avg_input_tokens = total_input_tokens / n_runs if n_runs else 0.0
    avg_output_tokens = total_output_tokens / n_runs if n_runs else 0.0

    console = Console()

    table = Table(title="RUN METRICS SUMMARY")
    table.add_column("Metric", style="bold")
    table.add_column("Total", justify="right")
    table.add_column("Average (per run)", justify="right")

    table.add_row("Cost ($)", f"{total_cost:.3f}", f"{avg_cost:.3f}")
    table.add_row("Duration (s)", f"{total_duration_seconds:.1f}", f"{avg_duration_seconds:.1f}")
    table.add_row("Turns", f"{total_turns}", f"{int(avg_turns)}")
    table.add_row("Tokens (total)", f"{total_tokens}", f"{int(avg_tokens)}")
    table.add_row("Tokens (input)", f"{total_input_tokens}", f"{int(avg_input_tokens)}")
    table.add_row("Tokens (output)", f"{total_output_tokens}", f"{int(avg_output_tokens)}")

    console.print(table)
