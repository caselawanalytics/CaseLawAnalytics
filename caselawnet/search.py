import pycurl
import json
import pandas as pd
from io import BytesIO
from lxml import etree
from . import matcher, utils, network_analysis


def get_post_data(keyword, contentsoorten=['uitspraak'], rechtsgebieden=[], instanties=[], maximum=1000):
    # TODO: add more options
    post_data = {
        "Advanced": {
            "PublicatieStatus": "Ongedefinieerd"
        },
        "Contentsoorten": [{
                           "NodeType": 7,
                           "Identifier": u,
                           "level": 1
                           } for u in contentsoorten],
        "DatumPublicatie": [],
        "DatumUitspraak": [],
        "Instanties": [{
                       "NodeType": 1,
                       "Identifier": i,
                       "level": 1
                       } for i in instanties],
        "PageSize": maximum,
        "Rechtsgebieden": [{
                       "NodeType": 3,
                       "Identifier": r,
                       "level": 1
                       } for r in rechtsgebieden],
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



def get_query_result(keyword, **args):
    post_data = get_post_data(keyword, **args)
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


def search(keyword, **args):
    result = get_query_result(keyword, **args)
    nodes = [result_to_node(res) for res in result['Results']]
    return nodes


def result_to_node(result):
    node = {}
    node['id'] = result['DeeplinkUrl']
    node['ecli'] = result['TitelEmphasis']
    node['creator'] = 'Hoge Raad'  # TODO
    node['title'] = result.get('Titel', node['id'])
    node['abstract'] = result.get('Tekstfragment', '')
    node['date'] = result['Publicatiedatum']
    node['subject'] = result['Rechtsgebieden'][0]

    matched_articles = matcher.get_articles(node['abstract'])
    node['articles'] = [art + ' ' + book for (art, book), cnt in
                        matched_articles.items()]
    node['year'] = int(node['date'].split('-')[-1])
    node['count_version'] = len(result['Vindplaatsen'])
    node['count_annotation'] = len([c for c in result['Vindplaatsen'] if
                                    c['VindplaatsAnnotator'] != ''])
    # New:
    node['procedure'] = result['Proceduresoorten']
    return node

