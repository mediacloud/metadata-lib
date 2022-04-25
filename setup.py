#! /usr/bin/env python
from setuptools import setup
import re
import os

REQUIRED_PACKAGES = [
    # for date guessing
    "htmldate==1.2.1", "dateparser==1.1.1",
    # for domain name extraction
    "tldextract==3.2.1",
    # for languge detection
    "py3langid==0.2.1",
    # various content extractors we try to use
    "newspaper3k==0.2.8", "goose3==3.1.11", "BeautifulSoup4==4.11.1", "readability-lxml==0.8.1", "trafilatura==1.2.0",
    "boilerpy3==1.0.6",
    # support
    "requests", "cchardet==2.1.7"  # BeautifulSoup4 speedup
]

with open('mcmetadata/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE).group(1)

# add README.md to distribution
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md')) as f:
    long_description = f.read()

setup(name='mediacloud-metadata',
      maintainer='Rahul Bhargava',
      maintainer_email='rahul@mediacloud.org',
      version=version,
      description='Media Cloud news article metadata extraction',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='http://mediacloud.org',
      test_suite="mediacloud.test",
      packages=['mcmetadata'],
      package_data={'': ['LICENSE']},
      install_requires=REQUIRED_PACKAGES,
      project_urls={  # Optional
              'Bug Reports': 'https://github.com/mediacloud/meta-extractor/issues',
              'Source': 'https://github.com/mediacloud/meta-extractor',
          },
      )
