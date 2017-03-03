import os
import sys

from SPARQLWrapper import SPARQLWrapper, JSON

sys.path.insert(0, os.path.abspath('..'))
import rechtspraak_query_app.parser.matcher as matcher
from . import network_analysis
import json
import itertools

DEFAULT_SPARQL_ENDPOINT = "http://localhost:9999/blazegraph/namespace/hogeraad/sparql"

def retrieve_from_sparql(searchstring, sparql):
    # escape quotes in searchstring
    searchstring = searchstring.replace('"', '\\"')

    query_nodesandrefs = '''prefix dcterm: <http://purl.org/dc/terms/>
    prefix bds: <http://www.bigdata.com/rdf/search#>
    select ?type ?id ?to ?title ?creator ?date ?subject ?abstract ?hasVersion ?article
    with {
     	select ?id
    	where {
          ?o bds:search "''' + searchstring + '''" .
          ?o bds:matchAllTerms "true" .
          ?id ?p ?o .
          ?id dcterm:type	<http://psi.rechtspraak.nl/uitspraak>.
         }
    } as %matcheddocs
    where {
      {
        BIND("link" AS ?type).
        ?id dcterm:references ?to.
        ?to dcterm:type	<http://psi.rechtspraak.nl/uitspraak>.
        include %matcheddocs
      }
       union
        {
        include %matcheddocs
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
        BIND("vindplaats" AS ?type).
        ?id dcterm:hasVersion ?hasVersion
        include %matcheddocs
        }
      union
      {
        include %matcheddocs
        BIND("article" AS ?type).
        ?id dcterm:reference ?articleid .
        ?articleid rdfs:label "Wetsverwijzing".
        ?articleid dcterm:title ?article
      }
    }
    '''
    sparql.setQuery(query_nodesandrefs)
    sparql.setReturnFormat(JSON)
    ret = sparql.query()
    nodes_and_links = ret.convert()
    return nodes_and_links

def retrieve_predicate_object(pred, obj, sparql):
    # escape quotes in searchstring
    pred = pred.replace('"', '\\"')
    obj = obj.replace('"', '\\"')

    query_nodesandrefs = '''prefix dcterm: <http://purl.org/dc/terms/>
    prefix bds: <http://www.bigdata.com/rdf/search#>
    select ?type ?id ?to ?title ?creator ?date ?subject ?abstract ?hasVersion ?article
    with {
     	select ?id
    	where {
          ?id  ''' + pred + ' ' + obj + ''' .
          ?id dcterm:type	<http://psi.rechtspraak.nl/uitspraak>.
         }
    } as %matcheddocs
    where {
      {
        BIND("link" AS ?type).
        ?id dcterm:references ?to.
        ?to dcterm:type	<http://psi.rechtspraak.nl/uitspraak>.
        include %matcheddocs
      }
       union
        {
        include %matcheddocs
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
        BIND("vindplaats" AS ?type).
        ?id dcterm:hasVersion ?hasVersion
        include %matcheddocs
        }
    union
      {
        include %matcheddocs
        BIND("article" AS ?type).
        ?id dcterm:reference ?articleid .
        ?articleid rdfs:label "Wetsverwijzing".
        ?articleid dcterm:title ?article
      }
    }
    '''
    sparql.setQuery(query_nodesandrefs)
    sparql.setReturnFormat(JSON)
    ret = sparql.query()
    nodes_and_links = ret.convert()
    return nodes_and_links


def parse_nodes(nodes_in, variables):
    nodes_json = []
    unique_ids = []
    for d in nodes_in:
        if d['id'] not in unique_ids:
            dout = {}
            for var in variables:
                dout[var] = d.get(var, '')
            nodes_json.append(dout)
            unique_ids.append(d['id'])
    return nodes_json, unique_ids


def url_to_ecli(url):
    ecli = url.split('=')[-1]
    return ecli

def ecli_to_year(ecli):
    return int(ecli.split(':')[3])


def enrich_nodes(nodes, vindplaatsen, articles):
    """
    Add some attributes to the nodes.

    :param nodes:
    :param vindplaatsen:
    :return:
    """
    for node in nodes:
        matched_articles = matcher.get_articles(node['abstract'])
        node['articles'] = [art + ' ' + book for (art, book), cnt in
                            matched_articles.items()]
        node['ecli'] = url_to_ecli(node['id'])
        node['year'] = ecli_to_year(node['ecli'])

    # get the keys (case id) and value (article name)
    articles_kv = [(item['id'], item['article']) for item in articles]
    articles_grouped = itertools.groupby(articles_kv, lambda x: x[0])
    articles_dict = {k: list(set([val[1] for val in g])) for k,g in articles_grouped}

    count_version = {}
    count_annotation = {}
    for item in vindplaatsen:
        id0 = item['id']
        val = item['hasVersion']
        count_version[id0] = count_version.get(id0, 0) + 1
        if val.lower().find('met annotatie') >= 0:
            count_annotation[id0] = count_annotation.get(id0, 0) + 1

    for node in nodes:
        node['count_version'] = count_version.get(node['id'], 0)
        node['count_annotation'] = count_annotation.get(node['id'], 0)
        node['articles'] = node['articles'] + articles_dict.get(node['id'], [])

    return nodes


def parse_links(links_in, node_ids):
    unique_link_ids = []
    links_json = []
    for d in links_in:
        target = d['to']
        if target in node_ids:
            dout = {'source': d['id'],
                    'target': target }
            dout['id'] = dout['source'] + '_' + dout['target']
            if dout['id'] not in unique_link_ids:
                links_json.append(dout)
                unique_link_ids.append(dout['id'])
    return links_json

def transform_result_item(item):
    return {k: item[k]['value'] for k in item}

def query(searchstring, only_linked=True, sparql=None, pred=None, obj=None):
    if sparql is None:
        sparql = SPARQLWrapper(DEFAULT_SPARQL_ENDPOINT)

    if searchstring is None:
        nodes_and_links = retrieve_predicate_object(pred, obj,
                                                                  sparql)
    else:
        nodes_and_links = retrieve_from_sparql(searchstring, sparql)

    # Parse the nodes
    variables = [x for x in nodes_and_links['head']['vars'] if
                 x not in ['type', 'from', 'to', 'hasVersion', 'article']]

    data = [transform_result_item(item) for item in nodes_and_links['results']['bindings']]
    nodes = [res for res in data  if res['type'] == 'node']
    vindplaatsen = [res for res in data  if res['type'] == 'vindplaats']
    articles = [res for res in data  if res['type'] == 'article']
    nodes_json, node_ids = parse_nodes(nodes, variables)

    nodes_json = enrich_nodes(nodes_json, vindplaatsen, articles)

    # Parse the links
    links = [res for res in data  if res['type'] == 'link']
    links_json = parse_links(links, node_ids)

    # Add network analysis
    nodes_json = network_analysis.add_network_statistics(nodes_json, links_json)

    # Possibly: remove nodes without link
    if only_linked:
        ids_with_link = set(
            [d['source'] for d in links_json] + [d['target'] for d in
                                                 links_json])
        nodes_json = [node for node in nodes_json if
                      node['id'] in ids_with_link]

    return nodes_json, links_json


def to_d3_json(nodes, links, filename):
    with open(filename, 'w') as outfile:
        json.dump({'nodes': nodes, 'links': links}, fp=outfile)


def to_sigma_json(nodes, links, title, filename=None):
    if filename is None:
        return json.dumps({'title': title, 'nodes': nodes, 'edges': links})
    with open(filename, 'w') as outfile:
        json.dump({'title': title, 'nodes': nodes, 'edges': links}, fp=outfile)

def to_csv(nodes, filename=None, variables=None):
    import pandas as pd
    if len(nodes) == 0:
        df = pd.DataFrame()
    else:
        if variables is None:
            variables  = nodes[0].keys()
        df = pd.DataFrame(nodes).set_index('id')
    if filename is None:
        return df.to_csv()
    else:
        df.to_csv(filename)