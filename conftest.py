from distutils.util import strtobool

import pytest


def pytest_addoption(parser):
    parser.addoption(
        '--use-cache', default=True, nargs="?", const=True,
        help='Use cached versions of content instead of fetching at every step',
        type=lambda x: bool(strtobool(x))
    )
