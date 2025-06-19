import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-artifacts",
        action="store_true",
        default=False,
        help="Overwrite/Update the output artifacts stored in `tests/artifacts`.",
    )
