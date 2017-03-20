import rdflib
import requests
from io import StringIO
import json
import pandas as pd
import os


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


def retrieve_graph(ecli, auth=None):
    if auth is None:
        auth = get_authentication()

    lido_id = "http://linkeddata.overheid.nl/terms/jurisprudentie/id/" + ecli
    url = "http://linkeddata.overheid.nl/service/get-links?id={}".format(
        lido_id)
    response = requests.get(url,
                            auth=requests.auth.HTTPBasicAuth(
                                auth['username'], auth['password']))
    xml_rdf = response.text

    g = rdflib.graph.Graph()
    with StringIO(xml_rdf) as buff:
        g.parse(buff)
    return g


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
