import itertools
from lxml import etree
import os
import re
from caselawnet import matcher, utils, parser
import caselawnet
import pandas as pd
from rdflib import Graph
import warnings


def get_meta_data(eclis, rootpath=None):
    existing_eclis = []
    graph = Graph()
    for ecli in eclis:
        try:
            element = retrieve_from_any(ecli, rootpath=rootpath)
            graph += parser.parse_xml_element(element, ecli)
            existing_eclis += [ecli]
        except:
            print("Could not parse: " + ecli)

    nodes = graph_to_nodes(graph)

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

def retrieve_from_any(ecli, rootpath=None):
    """
    Checks if it can find the xml document in the filesystem,
    otherwise retrieves it from the web.

    :param ecli:
    :param rootpath:
    :return:
    """
    el = None
    if rootpath is None:
        rootpath = caselawnet.rechtspraak_datapath()

    if rootpath is not None:
        el = retrieve_from_filesystem(ecli, rootpath)
    if el is None:
        try:
            el = retrieve_from_web(ecli)
        except Exception as e:
            el = None
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

    variables = ['id', 'title', 'creator', 'date', 'subject', 'abstract']
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