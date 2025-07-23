import sys
import textwrap
from pathlib import Path

import pytest
import yaml
from any_agent import AgentTrace


@pytest.fixture(scope="module")
def common_eval_testing_data_path():
    return Path("tests/generated_agent_evaluation/data/")


@pytest.fixture(scope="module")
def sample_evaluation_json_file(common_eval_testing_data_path):
    return (common_eval_testing_data_path / "sample_evaluation_case.json").read_text()


@pytest.fixture(scope="module")
def sample_agent_eval_trace_json(common_eval_testing_data_path):
    return (common_eval_testing_data_path / "sample_agent_eval_trace.json").read_text()
