import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-artifacts",
        action="store_true",
        default=False,
        help="Overwrite/Update the output artifacts stored in `tests/artifacts`.",
    )


@pytest.fixture(scope="module")
def common_eval_testing_data_path():
    return Path("tests/generated_agent_evaluation/data/")


@pytest.fixture(scope="module")
def sample_evaluation_json_file(common_eval_testing_data_path):
    return (common_eval_testing_data_path / "sample_evaluation_case.json").read_text()


@pytest.fixture(scope="module")
def sample_agent_eval_trace_json(common_eval_testing_data_path):
    return (common_eval_testing_data_path / "sample_agent_eval_trace.json").read_text()
