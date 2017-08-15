"""
A simple parser that retrieves rechtspraak.nl XML files,
parses them as RDF triples.

TODO: handle exceptions better
"""


import re
from rdflib import Graph
import rdflib
import urllib.parse
from rdflib.namespace import DCTERMS, RDFS


##################################
# Functions for actual parsing
##################################
def get_children(el, ns, tag):
    nsmap = el.nsmap
    searchtag = '{{{}}}{}'.format(nsmap[ns], tag)
    return list(el.iterchildren(searchtag))

def get_from_descriptions(descriptions, ns, tag):
    result = []
    for des in descriptions:
        result.extend(get_children(des, ns, tag))
    return result

def get_identifier(descriptions, ecli):
    ecli_node = None
    if len(descriptions)==2:
        identifier_list = get_children(descriptions[1], 'dcterms', 'identifier')
        if len(identifier_list)>0:
            identifier = identifier_list[0].text
            ecli_node = rdflib.URIRef(identifier)
    if ecli_node is None:
        ecli_node = rdflib.URIRef("http://deeplink.rechtspraak.nl/uitspraak?id="+ecli)
    return ecli_node

def add_title(descriptions, g, ecli_node):
    title_list = get_from_descriptions(descriptions, 'dcterms', 'title')
    for title in title_list:
        g.add((ecli_node, DCTERMS.title, rdflib.Literal(title.text)))
    return g

def add_date(descriptions, g, ecli_node):
    title_list =get_from_descriptions(descriptions, 'dcterms', 'date')
    for date in title_list:
        g.add((ecli_node, DCTERMS.date,
               rdflib.Literal(date.text, datatype=rdflib.XSD.date)))
    return g


def add_type(descriptions, g, ecli_node):
    type_list  = get_from_descriptions(descriptions, 'dcterms', 'type')
    for dtype in type_list:
        g.add((ecli_node, DCTERMS.type, rdflib.URIRef(dtype.attrib[
        'resourceIdentifier'])))
    return g

def add_version(descriptions, g, ecli_node):
    version_list = get_from_descriptions(descriptions, 'dcterms', 'hasVersion')
    for version in version_list:
        value = version.attrib.get('resourceIdentifier', None)
        if value == 'http://psi.rechtspraak.nl/vindplaats':
            for lis in get_children(version, 'rdf', 'list'):
                for item in get_children(lis, 'rdf', 'li'):
                    g.add(
                        (ecli_node, DCTERMS.hasVersion, rdflib.Literal(item.text)))

    return g

def add_subject(descriptions, g, ecli_node):
    subject_list  = get_from_descriptions(descriptions, 'dcterms', 'subject')
    for s in subject_list:
        value = s.attrib.get('resourceIdentifier', None)
        if value is not None:
            g.add((ecli_node, DCTERMS.subject, rdflib.URIRef(value)))
    return g

def add_type(descriptions, g, ecli_node):
    type_list  = get_from_descriptions(descriptions, 'dcterms', 'type')
    for dtype in type_list:
        value = dtype.attrib.get('resourceIdentifier', None)
        if value is not None:
            g.add((ecli_node, DCTERMS.type, rdflib.URIRef(value)))
    return g

def add_creator(descriptions, g, ecli_node):
    creator_list  = get_from_descriptions(descriptions, 'dcterms', 'creator')
    for creator in creator_list:
        value = creator.attrib.get('resourceIdentifier', None)
        if value is not None:
            g.add((ecli_node, DCTERMS.creator, rdflib.URIRef(value)))
    return g

def add_abstract(element, g, ecli_node):
    abstract_xml_list = list(element.iterchildren('{*}inhoudsindicatie'))
    if len(abstract_xml_list)>0:
        abstract_text = ' '.join(
            [e.text for e in abstract_xml_list[0].iterdescendants() if
             e.text is not None])
        g.add((ecli_node, DCTERMS.abstract, rdflib.Literal(abstract_text)))
    return g

def add_uitspraak(element, g, ecli_node):
    uitspraak_xml_list = list(element.iterchildren('{*}uitspraak'))
    if len(uitspraak_xml_list)>0:
        uitspraak_text = ' '.join(
            [e.text for e in uitspraak_xml_list[0].iterdescendants() if
             e.text is not None])
        g.add((ecli_node, DCTERMS.description, rdflib.Literal(uitspraak_text)))
    return g


#TODO
def add_one_reference(reference, g, ecli_node):
    ref_ns = ""
    resourceIdentifier = ""
    label = ""

    for k, v in reference.attrib.items():
        regex = r'\{(.*)\}(.*)'
        ns, att = re.findall(regex, k)[0]
        if att == 'resourceIdentifier':
            ref_ns = ns
            resourceIdentifier = v
        if att == 'label':
            label = v
    ref_uri_str = urllib.parse.quote(ref_ns + resourceIdentifier, safe=';/?:@&=+$,')
    reference_uri = rdflib.URIRef(ref_uri_str)
    g.add((ecli_node, DCTERMS.references, reference_uri))
    g.add((reference_uri, RDFS.label, rdflib.Literal(label)))
    g.add((reference_uri, DCTERMS.title, rdflib.Literal(reference.text)))
    return g

def add_reference(descriptions, g, ecli_node):
    reference_list = get_from_descriptions(descriptions, 'dcterms', 'references')
    for reference in reference_list:
        add_one_reference(reference, g, ecli_node)
    return g


def parse_xml_element(element, ecli):
    g = Graph()
    rdf = list(element.iterdescendants('{*}RDF'))[0]
    nsmap = rdf.nsmap
    for k, v in nsmap.items():
        g.bind(k, v)
    descriptions = list(rdf.iterchildren('{*}Description'))

    ecli_node = get_identifier(descriptions, ecli)
    g = add_title(descriptions, g, ecli_node)
    g = add_date(descriptions, g, ecli_node)
    g = add_type(descriptions, g, ecli_node)
    g = add_subject(descriptions, g, ecli_node)
    g = add_creator(descriptions, g, ecli_node)
    g = add_abstract(element, g, ecli_node)
    g = add_version(descriptions, g, ecli_node)
    g = add_reference(descriptions, g, ecli_node)
    g = add_uitspraak(element, g, ecli_node)
    return g


