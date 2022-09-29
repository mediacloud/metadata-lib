import pytest

def pytest_addoption(parser):
    parser.addoption(
        '--use-cache', default=True, help='Use cached versions of content instead of fetching at every step'
    )