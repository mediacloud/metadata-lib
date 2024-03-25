"""
Run URLs from our production system through the pipeline and save a CSV that lets us compare results to see if
this code produces similar metadata to the system the heuristics were extracted from. Useful for validating that
we are getting results we expect from the code as we evaluate different libraries and solutions.
"""

import csv
import logging
import multiprocessing as mp
from typing import Dict, Optional

import dateparser

import mcmetadata

logger = logging.getLogger(__file__)


def _comparison_worker(s: Dict) -> Optional[Dict]:
    try:
        results = {
            'url': s['url'],
            'language': s['language'],
            'pub_date': dateparser.parse(s['publish_date']).date(),
            'title': s['title'],
        }
        # guesses
        info = mcmetadata.extract(results['url'])
        results['language_guess'] = info['language']
        results['pub_date_guess'] = info['publication_date'].date()
        results['title_guess'] = info['article_title']
        # results
        results['language_match'] = results['language_guess'] == results['language']
        results['pub_date_match'] = results['pub_date_guess'] == results['pub_date']
        results['pub_date_diff'] = (results['pub_date'] - results['pub_date_guess']).days
        results['title_match'] = results['title_guess'] == results['title']
        return results
    except Exception:
        return None


def generate_comparison_csv(input_file: str, parallel: bool):
    with open(input_file) as infile:
        reader = csv.DictReader(infile)
        # run in parallel for performance improvement
        if parallel:
            pool = mp.Pool(processes=16)
            results = [r for r in pool.map(_comparison_worker, [s for s in reader][:200]) if r is not None]
        else:
            results = [_comparison_worker(r) for r in reader if r is not None]
    # write out csv for manual review
    with open(input_file.split('.')[0] + "-comparison.csv", 'w') as outfile:
        cols = ['url', 'pub_date', 'pub_date_guess', 'pub_date_match', 'pub_date_diff',
                'language', 'language_guess', 'language_match',
                'title', 'title_guess', 'title_match']
        writer = csv.DictWriter(outfile, fieldnames=cols)
        writer.writeheader()
        for s in results:
            writer.writerow(s)


if __name__ == "__main__":
    generate_comparison_csv('random-stories.csv', True)
