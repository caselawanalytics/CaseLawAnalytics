import rdflib
import requests
from io import StringIO
import json
import pandas as pd


def lido_url_to_ecli(url):
    return url.split('/')[-1]


def retrieve_graph(ecli, auth=None):
    if auth is None:
        try:
            with open('rechtspraak_query_app/authentication.json') as f:
                auth = json.load(f)
                username = auth["username"]
                password = auth["password"]
        except Exception:
            'No valid authentication file!'
            raise

    lido_id = "http://linkeddata.overheid.nl/terms/jurisprudentie/id/" + ecli
    url = "http://linkeddata.overheid.nl/service/get-links?id={}".format(lido_id)
    response = requests.get(url,
                            auth=requests.auth.HTTPBasicAuth(
                            username, password  ))
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









