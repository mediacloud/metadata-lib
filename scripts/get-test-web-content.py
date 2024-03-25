import os
import re
import time

from surt import surt

from mcmetadata import webpages

"""
The purpose of this script is to grab all of the urls present in the tests directory and cache the content in the
fixtures folder. The filenames will be equal to the alphanumeric content of the surt-ified url- this way, we can run
the tests against known cached content instead of having to query the IA everytime we want to test.
"""

test_directory = "../mcmetadata/test"

url_regex = r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"

test_files = [p for p in os.listdir(test_directory) if p.split(".")[-1] == "py"]


all_urls = []
for f in test_files:
    with open(os.path.join(test_directory, f), "r") as file:
        text = file.read()
        urls = re.findall(url_regex, text)
        for url in urls:
            if ".jpeg" not in url:
                all_urls.append(url[:-1])

final_urls = list(set(all_urls))


print(f" Found {len(final_urls)} in tests")

output_directory = "../mcmetadata/test/fixtures/"

for url in final_urls:

    url = re.sub('"', "", url)
    s = surt(url)
    filesafe_surt = "cached-" + re.sub(r"\W+", "", url)

    print(f"Fetching content for {url}")
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
        print(f"OK, saving: {filesafe_surt}")
        out = open(output_directory + filesafe_surt, "w")
        out.write(content)
        out.close()
    else:
        print(f"Failed: {filesafe_surt}")
