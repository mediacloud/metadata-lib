Meta Extractor
==============

🚧 _under construction_ 🚧

This is a package to extract a domain, title, publication date, text, and language content from the URL or text of an
online news story. The methods for each are extracted from the larger [Media Cloud project](https://mediacloud.org), 
but also build on numerous 3rd party  libraries. The metadata extracted includes:
* the original URL of publication
* a normalized URL useful for de-duplication
* the canonical domain published on
* the date of publication
* the primary language used in the article text
* the title of the article
* a normalized title useful for de-duplication 
* the text content of the news article
* the name of the library used to extract the article content


Installation
------------

`pip install mediacloud-metadata`

Usage
-----

If you pass in a URL, it will follow redirects and fetch the HTML for you.

```python
from mcmetadata import extract
metadata = extract(url="https://my.awesome.news/story-path")
```

You can also pass in HTML you already have on hand. Note that in this case it is also useful to pass in the URL
because that is used for some for some of the metadata extraction.

```python
from mcmetadata import extract
metadata = extract(url="https://my.awesome.news/story-path",
                   html_text="<html><head><title>my webpage ... </html>")
```


Distribution
------------

This is setup to automatically publish new releases to PyPi via GitHub Actions:

1. Run `pytest` to make sure all the test pass
2. Update the version number in `mcextractor/__init__.py`
3. Make a brief note in the version history section below about the changes
4. Commit the changes
5. Tag the commit with a semantic version number - 'v*.*.*'
6. Push to repo to GitHub

### Manual Release

If you need to push a release manually then you can do this:

1. Run `python setup.py sdist` to create an installation package
2. Run `twine upload --repository-url https://test.pypi.org/legacy/ dist/*` to upload it to PyPI's test platform
3. Run `twine upload dist/*` to upload it to PyPI


Version History
---------------

* __v0.5.3__: bug fixes in title normalization
* __v0.5.2__: more efficient parsing of dates from HTML, remove failing over-specified canonical domain case
* __v0.5.1__: fix small bug related to use of BeautifulSoup
* __v0.5.0__: add normalized URL and normalized title
* __v0.4.3__: *more* work on title regex bug
* __v0.4.2__: work on title regex bug
* __v0.4.1__: work on deployment
* __v0.4.0__: performance improvements, dependency updates
* __v0.3.1__: update dependencies
* __v0.3.0__: more fault tolerant, faster regex's, track extraction rates, update requirements
* __v0.2.0__: first packaging release for use in other places
* __v0.1.1__: first version for testing with collaborators


Contributors
------------

Created as part of the Media Cloud Project:
* Rahul Bhargava (Media Cloud, Northeastern University)
* Vangelis Banos (Internet Archive)
