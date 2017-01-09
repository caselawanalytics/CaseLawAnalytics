from SPARQLWrapper import SPARQLWrapper, JSON
import os
import sys
sys.path.insert(0, os.path.abspath('..'))
import parser.matcher as matcher
import json

DEFAULT_SPARQL_ENDPOINT = "http://localhost:9999/blazegraph/namespace/hogeraad/sparql"

def retrieve_from_sparql(searchstring, sparql):
    # escape quotes in searchstring
    searchstring = searchstring.replace('"', '\\"')

    query_nodesandrefs = '''prefix dcterm: <http://purl.org/dc/terms/>
    prefix bds: <http://www.bigdata.com/rdf/search#>
    select ?type ?id ?to ?title ?creator ?date ?subject ?abstract
    with {
     	select ?id
    	where {
          ?o bds:search "''' + searchstring + '''" .
          ?id ?p ?o .
          ?id dcterm:type	<http://psi.rechtspraak.nl/uitspraak>.
         }
    } as %matcheddocs
    where {
      {
        BIND("link" AS ?type).
        ?id dcterm:references ?to.
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
        if d['id']['value'] not in unique_ids:
            dout = {}
            for var in variables:
                dout[var] = d.get(var,{'value':''})['value']
            nodes_json.append(dout)
            unique_ids.append(d['id']['value'] )
    return nodes_json, unique_ids


def enrich_nodes(nodes):
    for node in nodes:
        articles = matcher.get_articles(node['abstract'])
        node['articles'] = {art + ' ' + book: cnt for (art, book), cnt in
                            articles.items()}
    return nodes


def parse_links(links_in, node_ids):
    unique_link_ids = []
    links_json = []
    for d in links_in:
        target = d['to']['value']
        if target in node_ids:
            dout = {'source': d['id']['value'],
                    'target': target }
            dout['id'] = dout['source'] + '_' + dout['target']
            if dout['id'] not in unique_link_ids:
                links_json.append(dout)
                unique_link_ids.append(dout['id'])
    return links_json


def query(searchstring, only_linked=True, sparql=None):
    if sparql is None:
        sparql = SPARQLWrapper(DEFAULT_SPARQL_ENDPOINT)

    nodes_and_links = retrieve_from_sparql(searchstring, sparql)

    # Parse the nodes
    variables = [x for x in nodes_and_links['head']['vars'] if
                 x not in ['type', 'from', 'to']]
    nodes = [res for res in nodes_and_links['results']['bindings'] if
             res['type']['value'] == 'node']
    nodes_json, node_ids = parse_nodes(nodes, variables)
    nodes_json = enrich_nodes(nodes_json)

    # Parse the links
    links = [res for res in nodes_and_links['results']['bindings'] if
             res['type']['value'] == 'link']
    links_json = parse_links(links, node_ids)

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


def to_sigma_json(nodes, links, filename):
    with open(filename, 'w') as outfile:
        json.dump({'nodes': nodes_json, 'edges': references}, fp=outfile)
