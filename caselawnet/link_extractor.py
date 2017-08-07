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
            auth = {}
            filename = 'settings.cfg'
            with open(filename) as f:
                exec(compile(f.read(), filename, 'exec'))
            auth['username'] = LIDO_USERNAME
            auth['password'] = LIDO_PASSWD
        except Exception:
            'No valid authentication file!'
            raise

    lido_id = "http://linkeddata.overheid.nl/terms/jurisprudentie/id/" + ecli
    url = "http://linkeddata.overheid.nl/service/get-links?id={}".format(lido_id)
    response = requests.get(url,
                            auth=requests.auth.HTTPBasicAuth(
                            auth['username'], auth['password'] ))
    xml_rdf = response.text

    g = rdflib.graph.Graph()
    with StringIO(xml_rdf) as buff:
        g.parse(buff)
    return g


def get_caselaw_references(g):
    query = '''
        prefix overheidrl: <http://linkeddata.overheid.nl/terms/>
        select ?id_from ?id_to ?link_type
        where {
          ?id_from overheidrl:linkt ?id_to.
          ?id_from a overheidrl:Jurisprudentie.
          ?id_to a overheidrl:Jurisprudentie.
          ?link overheidrl:linktVan ?id_from.
          ?link overheidrl:linktNaar ?id_to.
          ?link overheidrl:heeftLinktype ?link_type.
        }
        '''
    links = g.query(query)
    return pd.DataFrame(list(links), columns=['id_from', 'id_to', 'link_type'])

def get_legislation_references(g):
    query = '''
        prefix overheidrl: <http://linkeddata.overheid.nl/terms/>
        prefix dct: <http://purl.org/dc/terms/>
        select ?ecli ?ecliid ?wetid ?title ?linktype
        where {
          ?wetid a overheidrl:Wet.
          ?ecliid overheidrl:linkt ?wetid.
          ?ecliid dct:identifier ?ecli.
          ?ecliid a overheidrl:Jurisprudentie.
          ?link overheidrl:linktNaar ?wetid.
          ?link overheidrl:linktVan ?ecliid.
          ?link overheidrl:heeftLinktype ?linktype.
          ?wetid dct:title ?title.
        }
        '''
    leg_links = g.query(query)
    return pd.DataFrame(list(leg_links), columns=['ecli_id', 'ecli', 'wet_id', 'title', 'type'])