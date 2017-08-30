import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'caselawnet/_version.py')) as versionpy:
    exec(versionpy.read())

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name = "caselawnet",
    version = "0.3.3",
    description = ("Flask application for querying networks of Dutch case law"),
    license = "Apache 2.0",
    keywords = "Python",
    url = "https://github.com/NLeSC/CaseLawAnalytics",
    packages=['caselawnet'],
    install_requires=required,
    long_description=read('README.md'),
    classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
    ],
)
