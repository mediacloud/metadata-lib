import os

import mcmetadata.webpages

test_dir = os.path.dirname(os.path.realpath(__file__))
fixtures_dir = os.path.join(test_dir, "fixtures")

# mcmetadata.webpages.DEFAULT_TIMEOUT_SECS = 500  # reset to a longer timeout for tests


def read_fixture(filename: str) -> str:
    with open(os.path.join(fixtures_dir, filename)) as f:
        html_text = f.read()
    return html_text
