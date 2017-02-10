# CaseLawAnalytics
This repository contains code to setup a blazegraph instance with "Hoge Raad" (high court) cases from [Rechtspraak.nl](https://www.rechtspraak.nl) and an app to query the data.

This code is still under development.

Prerequisites:
* Java 7
* Python 3

Install the python requirents with `pip install -r requirements.txt`.

## Blazegraph
First, download the [Blazegraph executable jar](http://sourceforge.net/projects/bigdata/files/bigdata/2.1.4/blazegraph.jar/).

Modify the property `com.bigdata.journal.AbstractJournal.file` in the file `[CaseLawAnalytics repository]/blazegraph/RWStore.properties` to indicate where Blazegraph should store the .jnl file containing the data.
Then, run blazegraph with the properties file included in this repository:

`java -server -Xmx4g -Dbigdata.propertyFile=<path_to_repo>/blazegraph/RWStore.properties -jar blazegraph.jar `


### Load data into Blazegraph
The code for parsing the data from rechtspraak.nl and loading it into blazegraph can be found in `rechtspraak_parser`. Run the script `scripts/populate_blazegraph` to store all 'Hoge Raad' cases in Blazegraph.

To not overload the rechtspraak.nl server, it is best to first download the [complete collection of rechtspraak.nl](http://static.rechtspraak.nl/PI/OpenDataUitspraken.zip). 


## The query app
The query app runs in flask. Make sure the blazegraph server is running. Then:

`export FLASK_APP=blazegraph_querier/main.py`

and run the app:

`flask run`
