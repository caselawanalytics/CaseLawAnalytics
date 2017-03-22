import rdflib
import requests
from io import StringIO
import json
import pandas as pd
import os
from lxml import etree
from rechtspraak_query_app import query_to_json, network_analysis


def get_authentication():
    # Are there environment variables?
    if 'LIDO_USERNAME' in os.environ and 'LIDO_PASSWORD' in os.environ:
        auth = {'username': os.environ['LIDO_USERNAME'],
                'password': os.environ['LIDO_PASSWORD']}
    else:
        try:
            with open('rechtspraak_query_app/authentication.json') as f:
                auth = json.load(f)
        except Exception:
            'No valid authentication file!'
            raise
    return auth

def lido_url_to_ecli(url):
    return url.split('/')[-1]


def retrieve_graph(ecli, graph=None, auth=None):
    if graph is None:
        graph = rdflib.graph.Graph()

    if auth is None:
        auth = get_authentication()

    lido_id = "http://linkeddata.overheid.nl/terms/jurisprudentie/id/" + ecli
    url = "http://linkeddata.overheid.nl/service/get-links?id={}".format(
        lido_id)
    response = requests.get(url,
                            auth=requests.auth.HTTPBasicAuth(
                                auth['username'], auth['password']))
    xml_rdf = response.text


    with StringIO(xml_rdf) as buff:
        graph.parse(buff)
    return graph


def get_links_one(ecli, auth=None):
    g = retrieve_graph(ecli, auth=None)
    query = '''
        prefix overheidrl: <http://linkeddata.overheid.nl/terms/>
        select ?s ?o
        where {
          ?s overheidrl:linkt ?o
        }
        '''
    links = g.query(query)
    links_ecli = [(lido_url_to_ecli(source), lido_url_to_ecli(target))
                  for source, target in links]
    return pd.DataFrame(links_ecli, columns=['id', 'reference'])



# TODO: link type should be case to case
query = '''
select ?type ?id ?ecli ?to ?title ?creator ?date ?subject ?abstract ?hasVersion ?article
where {
  {
    BIND("link" AS ?type).
    ?link a overheidrl:LinkAct.
    ?link overheidrl:linktNaar ?to.
    ?link overheidrl:linktVan ?id.
    ?link overheidrl:heeftLinktype <http://linkeddata.overheid.nl/terms/linktype/id/rvr-conclusie-eerdereaanleg>.
    ?id a overheidrl:Jurisprudentie.
    ?to a overheidrl:Jurisprudentie.
  }
   union
    {
    BIND("node" AS ?type).
   ?id a overheidrl:Jurisprudentie.
   ?id dct:identifier ?ecli.
   optional { ?id dct:creator ?creator}.
   optional { ?id dct:abstract ?abstract}.
   optional { ?id overheidrl:heeftRechtsgebied ?subject}.
   optional { ?id overheidrl:heeftUitspraakdatum ?date}.
   optional { ?id rdfs:label ?title}
  }
  union
  {
    BIND("vindplaats" AS ?type).
    ?id dct:hasVersion ?hasVersion.
    ?id a overheidrl:Jurisprudentie
    }
union
  {
    BIND("article" AS ?type).
    ?id a overheidrl:Jurisprudentie.
    ?id overheidrl:linkt ?articleid .
    ?articleid a overheidrl:Artikel.
    ?articleid dct:title ?article
  }
}
'''


def get_network_from_graph(graph, only_linked=False):
    # TODO: only nodes that are in a predefined set?
    res = graph.query(query)
    res_df = pd.DataFrame(list(res))
    varnames = ['type', 'id', 'ecli',
            'to', 'title', 'creator', 'date', 'subject',
                'abstract', 'hasVersion', 'article']
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



    # Possibly: remove nodes without link
    if only_linked:
        ids_with_link = set(
            [d['source'] for d in links_json] + [d['target'] for d in
                                                 links_json])
        nodes_json = [node for node in nodes_json if
                      node['id'] in ids_with_link]
    # Add abstract:
    for node in nodes_json:
        node['abstract'] = get_abstract(node['ecli'])
    return nodes_json, links_json


def get_abstract(ecli):
    try:
        url = "http://data.rechtspraak.nl/uitspraken/content?id={}&return=META".format(ecli)
        el = etree.parse(url)
        abstract = ' '.join([x.text for x in el.iter('{http://purl.org/dc/terms/}abstract')])
        return abstract
    except:
        print('Error obtaining abstract for {}'.format(ecli))
        return ''
