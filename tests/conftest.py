import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-assets",
        action="store_true",
        default=False,
        help="Update asset files.",
    )
