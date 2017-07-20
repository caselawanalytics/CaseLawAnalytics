[![Build Status](https://travis-ci.org/NLeSC/CaseLawAnalytics.svg?branch=master)](https://travis-ci.org/NLeSC/CaseLawAnalytics)

# CaseLawAnalytics
This repository contains code for the case law query app: an application to query Dutch law cases and extract a network to use in the [case law visualization app](https://github.com/NLeSC/case-law-app).

This code is still under development.

Prerequisites:
* Python 3

## The python package
The python package `caselawnet` provides the following main functionalities:
* Search the [rechtspraak.nl](https://www.rechtspraak.nl/) api to retrieve 
  relevant law cases.
* Retrieve metadata from [rechtspraak.nl](https://www.rechtspraak.nl/) for a 
  list of cases (given their ECLI identifier)
* (Future: retrieve references between cases from [LiDO](http://linkeddata.overheid.nl/front/portal/lido))
* Calculate network statistics and create json file that can be used in the
  [case law visualization app](https://github.com/NLeSC/case-law-app).


To install `caselawnet`, clone the repository and run in the root of the repository:

`pip install .`

To run tests:

`pytest tests/`



## The web app
The web application provides a graphical user interface to the caselawnet package.

Copy the settings file:

`cp settings.cfg_dist settings.cfg`

If necessary, configure attributes in the config file, such as database.

To run the web app:

`export FLASK_APP=caselawnet_webapp.py`

and run the app:

`flask run`

The app runs much quicker if it connects to a database with the parsed cases. __To Do__ : Document how to create this database



## Setting up a database
The application works with [SQLAlchemy](). You can use any database as a backend for this. 
If using MySQL, the python package [mysql=connector-python](https://dev.mysql.com/doc/connector-python/en/connector-python-installation-source.html) needs to be installed.