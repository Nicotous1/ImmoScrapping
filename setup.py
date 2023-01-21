#!/usr/bin/env python

"""The setup script."""

from typing import List
from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements: List[str] = [
    "pandas",
    "beautifulsoup4",
    "requests",
    "pyarrow",
    "boto3",
    "bs4",
]

test_requirements = [
    "pytest>=3",
]

setup(
    author="Nicolas Toussaint",
    author_email="ntoussai29@gmail.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Python Boilerplate contains all the boilerplate you need to create a Python package.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="immo_scrap",
    name="immo_scrap",
    packages=find_packages(include=["immo_scrap", "immo_scrap.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/nicotous1/immo_scrap",
    version="0.1.0",
    zip_safe=False,
)
