import pycurl
import json
import pandas as pd
from io import BytesIO
from lxml import etree
from rechtspraak_query_app import links_to_json, parser, network_analysis, query_to_json


def get_post_data(keyword, uitspraak_conclusie=['uitspraak'], rechtsgebieden=[], instanties=[], maximum=1000):
    # TODO: add more options
    post_data = {
        "Advanced": {
            "PublicatieStatus": "Ongedefinieerd"
        },
        "Contentsoorten": [{
                           "NodeType": 7,
                           "Identifier": u,
                           "level": 1
                           } for u in uitspraak_conclusie],
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


def get_result_from_rss(rss_url):
    attributes = rss_url.split('?')[-1]
    url = 'http://data.rechtspraak.nl/uitspraken/zoeken?' + attributes
    el = etree.parse(url)
    root = el.getroot()


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

    nodes_json = [result_to_node(res) for res in result['Results']]
    # TODO: get links from lido
    links_json = links_from_abstract(nodes_json)
    # Add network analysis
    nodes_json = network_analysis.add_network_statistics(nodes_json,
                                                         links_json)
    return nodes_json, links_json


def links_from_abstract(nodes):
    links = []
    eclis = [node['ecli'] for node in nodes]
    for node in nodes:
        matched = parser.matcher.get_ecli_references(node['abstract'])
        for ecli in matched.keys():
            if ecli in eclis:
                target = links_to_json.ecli_to_url(ecli)
                links.append({'source': node['id'],
                              'target': target,
                             'id': node['id'] + '_' + target})
    return links


def result_to_node(result):
    node = {}
    node['id'] = result['DeeplinkUrl']
    node['ecli'] = result['TitelEmphasis']
    node['creator'] = 'Hoge Raad'  # TODO
    node['title'] = result.get('Titel', node['id'])
    node['abstract'] = result.get('Tekstfragment', '')
    node['date'] = result['Publicatiedatum']
    node['subject'] = result['Rechtsgebieden'][0]

    matched_articles = parser.matcher.get_articles(node['abstract'])
    node['articles'] = [art + ' ' + book for (art, book), cnt in
                        matched_articles.items()]
    node['year'] = int(node['date'].split('-')[-1])
    node['count_version'] = len(result['Vindplaatsen'])
    node['count_annotation'] = len([c for c in result['Vindplaatsen'] if
                                    c['VindplaatsAnnotator'] != ''])
    # New:
    node['procedure'] = result['Proceduresoorten']
    return node

if __name__ == "__main__":
    keyword = "7:658"
    nodes_json, links_json = get_network_from_keyword(keyword=keyword)
    query_to_json.to_sigma_json(nodes_json, links_json, keyword, filename=None)
