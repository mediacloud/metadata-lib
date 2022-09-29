import pytest

def pytest_addoption(parser):
    parser.addoption(
        '--use-cache', default=True, help='Whether to use cached versions of content'
    )