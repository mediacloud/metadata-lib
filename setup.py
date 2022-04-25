#! /usr/bin/env python
from setuptools import setup
import re
import os
from pip._internal.network.session import PipSession
from pip._internal.req import parse_requirements

with open('mcmetadata/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE).group(1)

# add README.md to distribution
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md')) as f:
    long_description = f.read()

# load in centralized requirements (https://stackoverflow.com/a/57191701)
requirements = parse_requirements(os.path.join(os.path.dirname(__file__), 'requirements.txt'), session=PipSession())

setup(name='mediacloud-metadata',
      version=version,
      description='Media Cloud news article metadata extraction',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='http://mediacloud.org',
      test_suite="mediacloud.test",
      packages=['mcmetadata'],
      package_data={'': ['LICENSE']},
      install_requires=[str(requirement.requirement) for requirement in requirements],
      project_urls={  # Optional
              'Bug Reports': 'https://github.com/mediacloud/meta-extractor/issues',
              'Source': 'https://github.com/mediacloud/meta-extractor',
          },
      )
