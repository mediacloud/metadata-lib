#! /usr/bin/env python
from setuptools import setup
import re
import os

REQUIRED_PACKAGES = [
    # for date guessing
    "htmldate==1.6.*", "dateparser==1.2.*",
    # for domain name and URL extraction
    "tldextract==5.1.*",
    "url-normalize==1.4.*",
    "furl==2.1.*",
    # for language detection
    "py3langid==0.2.*",
    # various content extractors we try to use
    "newspaper3k==0.2.*", "goose3==3.1.*", "BeautifulSoup4>=4.11,<4.13", "readability-lxml==0.8.*", "trafilatura>=1.4,<1.7",
    "boilerpy3==1.0.*",
    # support
    "requests",         # leave un-versioned so dependencies can sort of which version is best
    "faust-cchardet==2.1.*",  # BeautifulSoup4 speedup
    "surt==0.3.1"
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
      package_data={'': ['LICENSE'], 'mcmetadata': ['data/*.*']},
      python_requires='>=3.10',
      install_requires=REQUIRED_PACKAGES,
      tests_require=['parameterized'],
      project_urls={
              'Bug Reports': 'https://github.com/mediacloud/meta-extractor/issues',
              'Source': 'https://github.com/mediacloud/meta-extractor',
          },
      )
