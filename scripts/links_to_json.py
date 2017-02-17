import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
from rechtspraak_parser import parser, populate_blazegraph
from rdflib import Graph
from rdflib.namespace import DCTERMS
import rdflib
from blazegraph_querier import query_to_json, network_analysis

def read_csv(path, sep=','):
    links_df = pd.read_csv(path, sep=sep)
    links_df.columns = ['id', 'reference']
    links_df = links_df.drop_duplicates()
    eclis = list(pd.concat([links_df['id'], links_df['reference']]).unique())
    return links_df, eclis


def make_graph(links, eclis):
    graph = Graph()
    for ecli in eclis:
        try:
            element = populate_blazegraph.retrieve_from_web(ecli)
        except:
            print("Could not parse: " + ecli)
        graph += parser.parse_xml_element(element, ecli)

    # Add links to the graph
    for i, r in links.iterrows():
        create_link(r['id'], r['reference'], graph)
    return graph

def ecli_to_url(ecli):
    return "http://deeplink.rechtspraak.nl/uitspraak?id={}".format(ecli)

def create_link(ecli_from, ecli_to, g):
    url_from = rdflib.URIRef(ecli_to_url(ecli_from))
    url_to = rdflib.URIRef(ecli_to_url(ecli_to))
    g.add((url_from, DCTERMS.references, url_to))


def get_query():
    query = '''prefix dcterm: <http://purl.org/dc/terms/>
    prefix bds: <http://www.bigdata.com/rdf/search#>
    select ?type ?id ?to ?title ?creator ?date ?subject ?abstract ?hasVersion ?article
    where {
      {
        BIND("link" AS ?type).
        ?id dcterm:references ?to.
        ?to dcterm:type	<http://psi.rechtspraak.nl/uitspraak>.
      }
       union
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


def graph_to_network(graph):
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
    links = [x for x in res_list if x['type'] == 'link']

    variables = ['id', 'title', 'creator', 'date', 'subject', 'abstract']
    nodes_json, node_ids = query_to_json.parse_nodes(nodes, variables)
    nodes_json = query_to_json.enrich_nodes(nodes_json, vindplaatsen, articles)
    links_json = query_to_json.parse_links(links, node_ids)
    # Add network analysis
    nodes_json = network_analysis.add_network_statistics(nodes_json,
                                                         links_json)
    return nodes_json, links_json

if __name__ == "__main__":
    import sys
    print(sys.argv)
    file_in = sys.argv[1]
    file_out = sys.argv[2]
    title = sys.argv[3]
    links_df, eclis = read_csv(file_in, sep=',')
    graph = make_graph(links_df, eclis)
    nodes, links = graph_to_network(graph)
    query_to_json.to_sigma_json(nodes, links, title, filename=file_out)



