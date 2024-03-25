Media Cloud Metadata Extractor
==============================

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

### Prep Release
1. Run `pytest` to make sure all the test pass
2. Update the version number in `mcmetadata/__init__.py`
3. Make a brief note in the version history section below about the changes
4. Commit the changes
5. Tag the commit with a semantic version number - 'v*.*.*'
6. Push to repo to GitHub

### Manual Release

1. Run `python setup.py sdist` to create an installation package
2. Run `twine upload --repository-url https://test.pypi.org/legacy/ dist/*` to upload it to PyPI's test platform
3. Run `twine upload dist/*` to upload it to PyPI

### Test Cache

Test are run against fixtures by default.  This can be changed with the use of '--use-cache=False' when running tests. 
When adding new tests, re-run 'scripts/get-test-web-content.py'


Contributors
------------

Created as part of the Media Cloud Project. Contributes include:
* Rahul Bhargava (Media Cloud, Northeastern University)
* Paige Gulley (Media Cloud)
* Phil Budne (Media Cloud)
* Vangelis Banos (Internet Archive)
