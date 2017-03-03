import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name = "rechtspraak_query_app",
    version = "0.1.0",
    description = ("Flask application for querying networks of Dutch case law"),
    license = "Apache 2.0",
    keywords = "Python",
    url = "https://github.com/NLeSC/CaseLawAnalytics",
    packages=['rechtspraak_query_app', 'rechtspraak_query_app.parser'],
    install_requires=required,
    long_description=read('README.md'),
    classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
    ],
)
