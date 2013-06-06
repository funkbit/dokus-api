#!/usr/bin/env python
import os
import sys

from dokus import __version__
from setuptools import setup

# Publish to Pypi
if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

setup(
    name='pydokus',
    version=__version__,
    description='pydokus is Python module for interacting with the Dokus REST API.',
    long_description=open('README.md').read(),
    author='Funkbit',
    author_email='post@funkbit.no',
    url='https://github.com/funkbit/dokus-api',
    packages=['dokus', ],
    license='BSD',
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    )
)
