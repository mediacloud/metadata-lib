import csv
import dateparser

from mcmetadata import extract


def generate_comparison_csv(input_file: str):
    with open(input_file) as infile:
        reader = csv.DictReader(infile)
        all_results = []
        for s in reader:
            try:
                results = {
                    'url': s['url'],
                    'language': s['language'],
                    'pub_date': dateparser.parse(s['publish_date']).date(),
                    'title': s['title'],
                }
                # guesses
                info = extract(results['url'])
                results['language_guess'] = info['language']
                results['pub_date_guess'] = info['publication_date'].date()
                results['title_guess'] = info['article_title']
                # results
                results['language_match'] = results['language_guess'] == results['language']
                results['pub_date_match'] = results['pub_date_guess'] == results['pub_date']
                results['title_match'] = results['title_guess'] == results['title']
                all_results.append(results)
            except Exception as e:
                continue
    with open(input_file.split('.')[0]+"-comparison.csv", 'w') as outfile:
        cols = ['url', 'pub_date', 'pub_date_guess', 'pub_date_match',
                'language', 'language_guess', 'language_match',
                'title', 'title_guess', 'title_match']
        writer = csv.DictWriter(outfile, fieldnames=cols)
        writer.writeheader()
        for s in all_results:
            writer.writerow(s)


if __name__ == "__main__":
    generate_comparison_csv('random-stories.csv')
