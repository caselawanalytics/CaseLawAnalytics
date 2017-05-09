import itertools
from lxml import etree
import os
import re
from . import matcher, utils, parser, dbutils
import caselawnet
import pandas as pd
from rdflib import Graph
import warnings


node_variables = ['id', 'title', 'creator', 'date', 'subject', 'abstract']
node_extra_variables = ['year', 'count_version', 'count_annotation']

def get_meta_data(eclis, rootpath=None, dbpath=None):
    existing_eclis = []
    nodes = []

    # Try setting up the database
    db = None
    if dbpath is None:
        dbpath = caselawnet.rechtspraak_dbpath()
    if dbpath is not None:
        db = dbutils.connect_db(dbpath)

    graph = Graph()

    for ecli in eclis:
        #TODO check if its a valid ecli, otherwise throw error
        try:
            # First try database
            node = retrieve_from_db(ecli, db)
            if node is None:
                element = retrieve_from_any(ecli, rootpath=rootpath)
                graph += parser.parse_xml_element(element, ecli)
            else :
                print('Retrieved {} from database'.format(ecli))
                nodes.append(node)
            existing_eclis += [ecli]
        except Exception as e:
            # Add empty node
            print("Could not retrieve: " + ecli, e)
            node = {k: '' for k in node_variables + node_extra_variables}
            node['ecli'] = ecli
            node['id'] = utils.ecli_to_url(ecli)
            nodes.append(node)
    

    # TODO: what are the vindplaatsen and articles?
    if len(graph)>0:
        nodes.extend(graph_to_nodes(graph))

    if db is not None:
        db.close()
    return nodes

def enrich_links(links):
    links_out = [{} for _ in range(len(links))]
    for i in range(len(links)):
        lout = links_out[i]
        for k in links[i].keys():
            lout[k] = links[i][k]
        lout['source'] = utils.ecli_to_url(links[i]['source'])
        lout['target'] = utils.ecli_to_url(links[i]['target'])
        if 'id' not in links[i]:
            lout['id'] = links[i]['source'] + '_' + links[i]['target']
    return links_out


##################################
# Functions for retrieving complete xml documents
##################################
def retrieve_xml_from_web(ecli):
    link = 'http://data.rechtspraak.nl/uitspraken/content?id={}'.format(ecli)
    return etree.ElementTree().parse(link)


def retrieve_xml_from_filesystem(ecli, rootpath):
    year = ecli[11:15]
    fn = str(year) + '/' + re.sub(':', '_', ecli) + '.xml'
    path = os.path.join(rootpath, fn)
    try:
        return etree.ElementTree().parse(path)
    except Exception as e:
        return None

def retrieve_from_db(ecli, db):
    if db is not None:
        node = dbutils.retrieve_ecli(ecli, db)
        if node is not None:
            node = enrich_nodes([node], [], [])[0]
        return node
    return None

def retrieve_from_any(ecli, rootpath=None, db=None):
    """
    Checks if it can find the xml document in the db or filesystem,
    otherwise retrieves it from the web.

    :param ecli:
    :param rootpath:
    :return: xml element
    """
    el = None
    if rootpath is None:
        rootpath = caselawnet.rechtspraak_datapath()

    if rootpath is not None:
        el = retrieve_xml_from_filesystem(ecli, rootpath)
    if el is None:
        try:
            el = retrieve_xml_from_web(ecli)
            print('Retrieved {} from web'.format(ecli))
        except Exception as e:
            el = None
    else:
        print('Retrieved {} from file system'.format(ecli))
    return el




##################################
# Functions for making nodes from graph
##################################
def get_query():
    query = '''prefix dcterm: <http://purl.org/dc/terms/>
    prefix bds: <http://www.bigdata.com/rdf/search#>
    select ?type ?id ?to ?title ?creator ?date ?subject ?abstract ?hasVersion ?article
    where {
        {
        BIND("node" AS ?type).
       ?id dcterm:type	<http://psi.rechtspraak.nl/uitspraak>.
           optional { ?id dcterm:creator ?creator}.
       optional { ?id dcterm:abstract ?abstract}.
       optional { ?id dcterm:subject ?subject}.
       optional { ?id dcterm:date ?date}.
       optional { ?id dcterm:title ?title}
      }
      union
        {
        BIND("node" AS ?type).
       ?id dcterm:type	<http://psi.rechtspraak.nl/conclusie>.
           optional { ?id dcterm:creator ?creator}.
       optional { ?id dcterm:abstract ?abstract}.
       optional { ?id dcterm:subject ?subject}.
       optional { ?id dcterm:date ?date}.
       optional { ?id dcterm:title ?title}
      }
      union
      {
        BIND("vindplaats" AS ?type).
        ?id dcterm:hasVersion ?hasVersion
        }
    union
      {
        BIND("article" AS ?type).
        ?id dcterm:references ?articleid .
        ?articleid rdfs:label "Wetsverwijzing".
        ?articleid dcterm:title ?article
      }
    }
    '''
    varnames = ['type', 'id', 'to', 'title', 'creator', 'date', 'subject',
                'abstract', 'hasVersion', 'article']
    return query, varnames


def graph_to_nodes(graph):
    query, varnames = get_query()
    res = graph.query(query)
    res_df = pd.DataFrame(list(res))
    res_df.columns = varnames
    res_df = res_df.applymap(lambda x: x if x is None else str(x.toPython()))

    res_list = [dict(x[1]) for x in res_df.iterrows()]
    res_list = [{key: d[key] for key in d if d[key]} for d in res_list]

    nodes = [x for x in res_list if x['type'] == 'node']
    vindplaatsen = [x for x in res_list if x['type'] == 'vindplaats']
    articles = [x for x in res_list if x['type'] == 'article']

    variables = node_variables
    nodes_json, node_ids = parse_nodes(nodes, variables)
    nodes_json = enrich_nodes(nodes_json, vindplaatsen, articles)

    return nodes_json


def parse_nodes(nodes_in, variables):
    nodes_json = []
    unique_ids = []
    for d in nodes_in:
        if d['id'] not in unique_ids:
            dout = {}
            for var in variables:
                dout[var] = d.get(var, '')
            dout['ecli'] = utils.url_to_ecli(d['id'])
            nodes_json.append(dout)
            unique_ids.append(d['id'])
    return nodes_json, unique_ids

def enrich_nodes(nodes, vindplaatsen, articles):
    """
    Add some attributes to the nodes.

    :param nodes:
    :param vindplaatsen:
    :return:
    """
    nodes = add_year(nodes)
    nodes = add_articles(nodes, articles)
    nodes = add_versions(nodes, vindplaatsen)
    return nodes



def add_year(nodes):

    for node in nodes:
        if node['ecli'] is None:
            warnings.warn('ECLI field not available!', Warning)
            node['year'] = 0
        else:
            node['year'] = utils.ecli_to_year(node['ecli'])
    return nodes


def add_versions(nodes, versions):
    """
    In Dutch rechtspraak.nl data, an version can have an annotation.

    :param nodes: list of node objects
    :param versions: list of versions
    :return: list of nodes
    """
    count_version = {}
    count_annotation = {}
    for item in versions:
        id0 = item['id']
        val = item['hasVersion']
        count_version[id0] = count_version.get(id0, 0) + 1
        if val.lower().find('met annotatie') >= 0:
            count_annotation[id0] = count_annotation.get(id0, 0) + 1

    for node in nodes:
        node['count_version'] = count_version.get(node['id'], 0)
        node['count_annotation'] = count_annotation.get(node['id'], 0)
    return nodes

def add_articles(nodes, articles):
    # get the keys (case id) and value (article name)
    articles_kv = [(item['id'], item['article']) for item in articles]
    articles_grouped = itertools.groupby(articles_kv, lambda x: x[0])
    articles_dict = {k: list(set([val[1] for val in g]))
                     for k, g in articles_grouped}
    for node in nodes:
        matched_articles = matcher.get_articles(node['abstract'])
        node['articles'] = [art + ' ' + book for (art, book), cnt in
                            matched_articles.items()]  \
                           + articles_dict.get(node['id'], [])
    return nodes
