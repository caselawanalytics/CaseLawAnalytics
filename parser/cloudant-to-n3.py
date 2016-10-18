#!/usr/local/bin/python
from rdflib import Graph, plugin
from rdflib.serializer import Serializer

g = Graph()
g.parse("https://rechtspraak.cloudant.com/docs/ECLI:NL:GHSHE:2014:1641", format="json-ld")
g.serialize("ECLI_NL_GHSHE_2014_1641.n3", format="n3")

