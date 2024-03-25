"""
Run 100 URLs and print out how long each piece of metadata took to extract. Useful for determining if changes
increase of decrease performance.
"""

import csv
import logging

import mcmetadata

logger = logging.getLogger(__file__)


if __name__ == "__main__":
    with open('random-stories-small.csv') as infile:
        reader = csv.DictReader(infile)
        for r in reader:
            try:
                mcmetadata.extract(r['url'])
            except Exception:
                pass  # just skip on any failure - we just want the overall stats
    print("Stats (in elapsed seconds):")
    for s in mcmetadata.STAT_NAMES:
        print("  {}: {} ({:.3%})".format(
            s,
            mcmetadata.stats.get(s),
            mcmetadata.stats.get(s) / mcmetadata.stats.get('total')
        ))
