Meta Extractor
==============

🚧 _under constrction_ 🚧

This is a package to extract a domain, title, publication date, text, and language content from a URL. The methods for each
is extracted from the larger [Media Cloud project](https://mediacloud.org). 

Usage
-----

```python
from mcextractor import extract
metadata = extract(url="https://my.awesome.news/story-path")
```

or 

```python
from mcextractor import extract
metadata = extract(html_text="<html><head><title>my webpage ... </html>")
```

