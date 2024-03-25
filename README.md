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

Development
-----------

If you are interested in adding code to this module, first clone the GitHub repository.

### Installing

* `flit install`
* `pre-commit install`

### Testing

`pytest`

### Distributing a New Version

1. Run `pytest` to make sure all the test pass
2. Update the version number in `pyproject.toml`
3. Make a brief note in the `CHANGELOG.md` about what changes
4. Commit the changes
5. Tag the commit with a semantic version number - `v*.*.*`
6. Push to repo to GitHub
7. Run `flit build` to create an install package
8. Run `flit publish` to upload it to PyPI

#### Test Cache

Test are run against fixtures by default.  This can be changed with the use of '--use-cache=False' when running tests.
When adding new tests, re-run 'scripts/get-test-web-content.py'


Contributors
------------

Created as part of the Media Cloud Project. Contributes include:
* Rahul Bhargava (Media Cloud, Northeastern University)
* Paige Gulley (Media Cloud)
* Phil Budne (Media Cloud)
* Vangelis Banos (Internet Archive)
