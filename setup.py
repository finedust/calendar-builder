#!/usr/bin/env python3

import io
import re
from setuptools import setup, find_packages
import sys

with io.open('./calendariounibo/__init__.py', encoding='utf8') as version_file:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")


with io.open('LEGGIMI.txt', encoding='utf8') as readme:
    long_description = readme.read()


setup(
    name='calendariounibo',
    version=version,
    description='Sincronizza il calendario del telefono con le lezioni dal sito di UniBo',
    long_description=long_description,
    author='Francesco Tosello',
    author_email='francesco.tosello@studio.unibo.it',
    license='MIT license',
    packages=find_packages(
        exclude=[
            'docs', 'tests',
            'windows', 'macOS', 'linux',
            'iOS', 'android',
            'django'
        ]
    ),
    classifiers=[
        'Development Status :: Production',
        'License :: OSI Approved :: MIT license',
    ],
    install_requires=[
    ],
    options={
        'app': {
            'formal_name': 'Calendario UniBo',
            'bundle': 'it.francescotosello'
        },

        # Desktop/laptop deployments
        'macos': {
            'app_requires': [
            ]
        },
        'linux': {
            'app_requires': [
            ]
        },
        'windows': {
            'app_requires': [
            ]
        },

        # Mobile deployments
        'ios': {
            'app_requires': [
            ]
        },
        'android': {
            'app_requires': [
            ]
        },

        # Web deployments
        'django': {
            'app_requires': [
            ]
        },
    }
)
