import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
from rechtspraak_parser import parser
from lxml import etree
from rdflib.namespace import DCTERMS, RDFS

def test_parse_element():
    element = etree.ElementTree().parse("test/test_ecli.xml")
    graph = parser.parse_xml_element(element, "ECLI:NL:HR:1999:AA3837")
    references = list(graph.subject_objects(DCTERMS.references))
    assert len(references)==3
