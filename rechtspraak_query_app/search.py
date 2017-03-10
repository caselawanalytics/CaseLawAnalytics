import pycurl
import json
import pandas as pd
from io import BytesIO
from rechtspraak_query_app import links_to_json


def get_post_data(keyword, maximum=1000):
    # TODO: add more options
    post_data = {
        "Advanced": {
            "PublicatieStatus": "Ongedefinieerd"
        },
        "Contentsoorten": [{
                "NodeType": 7,
                "Identifier": "uitspraak",
                "level": 1
            }],
        "DatumPublicatie": [],
        "DatumUitspraak": [],
        "Instanties": [{
                "NodeType": 1,
                "Identifier": "Spirit.Npi.Ecli.Domain.TypeHr",
                "level": 1
            }],
        "PageSize": maximum,
        "Rechtsgebieden": [],
        "SearchTerms": [
            {
                "Field": "AlleVelden",
                "Term": keyword
            }
        ],
        "ShouldCountFacets": True,
        "ShouldReturnHighlights": False,
        "SortOrder": "Relevance",
        "StartRow": 0
    }
    return json.dumps(post_data)

def get_query_result(keyword):
    post_data = get_post_data(keyword)
    buffer = BytesIO()

    c = pycurl.Curl()
    c.setopt(c.URL, 'https://uitspraken.rechtspraak.nl/api/zoek')
    c.setopt(pycurl.HTTPHEADER, ['Content-Type: application/json',
                                'Accept: application/json'])
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(pycurl.POST, 1)
    c.setopt(pycurl.POSTFIELDS, post_data)

    c.perform()
    c.close()

    body = buffer.getvalue()
    result = json.loads(body.decode('utf-8'))
    return result

def get_network_from_keyword(keyword, verbose=True):
    result = get_query_result(keyword)

    if verbose:
        print(result['ResultCount'], 'results')
        for key in result['FacetCounts']:
            facetcounts = result['FacetCounts'][key]
            print(key)
            print(pd.DataFrame(facetcounts)[['Identifier', 'Count']])
            print('\n')

    eclis = [res['DeeplinkUrl'].split('=')[-1] for res in result['Results']]
    # TODO: get links from somewhere
    links = pd.DataFrame()
    g, eclis = links_to_json.make_graph(links, eclis)
    nodes_json, links_json = links_to_json.graph_to_network(g)
    return nodes_json, links_json


nodes_json, links_json = get_network_from_keyword(keyword = "7:658")