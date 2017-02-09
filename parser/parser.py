"""
A simple parser that retrieves rechtspraak.nl XML files,
can parse them and upload them to the blazegraph SPARQL point.

TODO: handle exceptions better
"""

import os
from lxml import etree
import re
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph
import rdflib
import urllib.parse
from rdflib.namespace import DCTERMS, RDFS

##################################
# Functions for retrieving metadata
##################################
def get_entries_from_link(fr=0, \
                          maximum=1000, \
                          baselink=None):
    """
    Retrieves the 'entry' elements of an xml file on the web.
    TODO: now standard selects Hoge Raad and return=Doc

    :param fr:
    :param maximum:
    :param baselink:
    :return:
    """
    if baselink is None:
        baselink = 'http://data.rechtspraak.nl/uitspraken/zoeken?return=DOC&creator=http://standaarden.overheid.nl/owms/terms/Hoge_Raad_der_Nederlanden'
    link = baselink + '&max=' + str(maximum) + '&from=' + str(fr)
    xml_element = etree.ElementTree().parse(link)
    entries = list(xml_element.iter('{*}entry'))
    return entries

def get_first_content(el, tag):
    return list(el.iter('{*}'+tag))[0].text


##################################
# Functions for retrieving complete xml documents
##################################
def retrieve_from_web(ecli):
    link = 'http://data.rechtspraak.nl/uitspraken/content?id=' + ecli
    return etree.ElementTree().parse(link)


def retrieve_from_filesystem(ecli, rootpath):
    year = ecli[11:15]
    fn = str(year) + '/' + re.sub(':', '_', ecli) + '.xml'
    path = os.path.join(rootpath, fn)
    try:
        return etree.ElementTree().parse(path)
    except Exception as e:
        return None

def retrieve_from_any(ecli, rootpath):
    """
    Checks if it can find the xml document in the filesystem,
    otherwise retrieves it from the web.

    :param ecli:
    :param rootpath:
    :return:
    """
    el = retrieve_from_filesystem(ecli, rootpath)
    if el is None:
        try:
            el = retrieve_from_web(ecli)
        except Exception as e:
            el = None
    return el


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


def parse_xml_element(g, element, ecli):
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


def parse_and_save(ecli, filepath_input, filepath_output, form='n3'):
    """
    Retrieves the XML document for a specific ECLI identifier,
    parses it and stores it in the specified format.

    :param ecli:
    :param filepath_input:
    :param filepath_output:
    :param form:
    :return:
    """
    g = Graph()
    element = retrieve_from_any(ecli, filepath_input)
    if element is None:
        return None
    g = parse_xml_element(g, element, ecli)
    ext = '.ttl' if form=='turtle' else '.'+form
    fname = os.path.join(filepath_output, re.sub(':', '_', ecli)+ext)
    g.serialize(destination=fname, format=form)
    return fname



##################################
# Functions for processing many eclis
##################################
def upload_to_sparql(fname, namespace='hogeraad'):
    sparql = SPARQLWrapper("http://localhost:9999/blazegraph/namespace/{}/sparql".format(namespace))
    sparql.method = 'POST'
    sparql.setQuery('LOAD <file://{}>'.format(fname))
    res = sparql.query()

def parse_data_in_batches(filepath_input, filepath_output,
                          nrdocs=30000, batchsize=1000):
    for start in range(0, nrdocs, batchsize):
        entries = get_entries_from_link(start, batchsize)
        print(start, len(entries))
        for entry in entries:
            ecli = get_first_content(entry, 'id')
            fname = parse_and_save(ecli, filepath_input, filepath_output,
                                   form='n3')
            if fname is not None:
                upload_to_sparql(fname)
            else:
                print("Could not parse", ecli)

if __name__ == "__main__":
    import sys
    filepath_input = sys.argv[0]
    filepath_output = sys.argv[1]
    parse_data_in_batches(filepath_input, filepath_output,
                                 nrdocs=30000, batchsize=1000)