import os
import re
import time

from mcmetadata import webpages
from mcmetadata.test import cached_url_file_name

"""
The purpose of this script is to grab all of the urls present in the tests directory and cache the content in the
fixtures folder. The filenames will be equal to the alphanumeric content of the surt-ified url- this way, we can run
the tests against known cached content instead of having to query the IA everytime we want to test.
Run from root directory as python scrips/get-test-web-content.py
"""

TEST_DIR = "mcmetadata/test"
FIXTURE_DIR = TEST_DIR + "/fixtures/"

url_regex = r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"

test_files = [p for p in os.listdir(TEST_DIR) if p.split(".")[-1] == "py"]


all_urls = []
for f in test_files:
    with open(os.path.join(TEST_DIR, f), "r") as file:
        text = file.read()
        urls = re.findall(url_regex, text)
        for url in urls:
            if ".jpeg" not in url:
                all_urls.append(url[:-1])

final_urls = list(set(all_urls))


print(f"Found {len(final_urls)} in tests")

for url in final_urls:
    url = re.sub('"', "", url)
    cache_file_name = cached_url_file_name(url)
    print(f"Fetching content for {url}")
    if os.path.exists(FIXTURE_DIR + cache_file_name):
        print(f"  Skipping, already exists at {cache_file_name}")
    else:
        keep_trying = True
        tries = 0
        content = None
        while keep_trying:
            try:
                content, _ = webpages.fetch(url)
            except Exception:
                time.sleep(1)
                tries += 1
                if tries > 10:
                    keep_trying = False
            else:
                keep_trying = False

        if content:
            print(f"  OK, saving: to {cache_file_name}")
            out = open(FIXTURE_DIR + cache_file_name, "w")
            out.write(content)
            out.close()
        else:
            print(f"  Failed: {cache_file_name}")
