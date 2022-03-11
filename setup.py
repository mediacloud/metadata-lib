#! /usr/bin/env python
from setuptools import setup
import re
from os import path

with open('mcmetadata/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE).group(1)

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md')) as f:
    long_description = f.read()

setup(name='mediacloud-metadata',
      version=version,
      description='Media Cloud news article metadata extraction',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='http://mediacloud.org',
      test_suite="mediacloud.test",
      packages=['mcmetadata'],
      package_data={'': ['LICENSE']},
      install_requires=['requests', 'htmldate', 'dateparser', 'tldextract', 'py3langid', 'newspaper3k', 'goose3',
                'BeautifulSoup4', 'readability-lxml', 'trafilatura', 'boilerpy3'],
      project_urls={  # Optional
              'Bug Reports': 'https://github.com/mediacloud/meta-extractor/issues',
              'Source': 'https://github.com/mediacloud/meta-extractor',
          },
      )
