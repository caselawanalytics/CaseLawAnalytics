# CaseLawAnalytics
This repository contains code to setup a blazegraph instance with "Hoge Raad" (high court) cases from [Rechtspraak.nl](https://www.rechtspraak.nl) and an app to query the data.

This code is still under development.

Prerequisites:
* Java 7
* Python 3

## Blazegraph
First, download the [Blazegraph executable jar](http://sourceforge.net/projects/bigdata/files/bigdata/2.1.4/blazegraph.jar/).

Then, run blazegraph with the properties file included in this repository:

`java -server -Xmx4g -Dbigdata.propertyFile=<path_to_repo>/blazegraph/RWStore.properties -jar blazegraph.jar `

(NB: it will create the .jnl file containing the data in the current working directory).

### Load data into Blazegraph
The code for parsing the data from rechtspraak.nl and loading it into blazegraph can be found in `parser/parser.py`. See for example the code in [this notebook](https://github.com/NLeSC/CaseLawAnalytics/blob/master/notebooks/SmallParser.ipynb).

To not overload the rechtspraak.nl server, it is best to first download the [complete collection of rechtspraak.nl](http://static.rechtspraak.nl/PI/OpenDataUitspraken.zip). 


## The query app
The query app runs in flask. Make sure the blazegraph server is running. Then:

`export FLASK_APP=blazegraph_querier/main.py`

and run the app:

`flask run`
