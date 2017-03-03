"""
This module can retrieve rechtspraak.nl XML files,
parses them and upload them to the blazegraph SPARQL point.

TODO: handle exceptions better
"""
import os
import re

from SPARQLWrapper import SPARQLWrapper
from lxml import etree

from . import parser

namespace = "kb"#"hogeraad"
sparql_endpoint = "http://localhost:9999/blazegraph/namespace/{}/sparql".format(namespace)


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
    link = 'http://data.rechtspraak.nl/uitspraken/content?id={}'.format(ecli)
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
    element = retrieve_from_any(ecli, filepath_input)
    if element is None:
        return None
    g = parser.parse_xml_element(element, ecli)
    ext = '.ttl' if form=='turtle' else '.'+form
    fname = os.path.join(filepath_output, re.sub(':', '_', ecli)+ext)
    g.serialize(destination=fname, format=form)
    return fname



##################################
# Functions for processing many eclis
##################################
def upload_to_sparql(fname):
    sparql = SPARQLWrapper(sparql_endpoint)
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

