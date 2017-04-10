import itertools
from lxml import etree
import os
import re
from caselawnet import matcher, utils



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
        node['ecli'] = utils.url_to_ecli(node['id'])
        node['year'] = utils.ecli_to_year(node['ecli'])

    # get the keys (case id) and value (article name)
    articles_kv = [(item['id'], item['article']) for item in articles]
    articles_grouped = itertools.groupby(articles_kv, lambda x: x[0])
    articles_dict = {k: list(set([val[1] for val in g]))
                     for k, g in articles_grouped}

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


##################################
# Functions for retrieving complete xml documents
##################################
def retrieve_from_web(ecli):
    link = 'http://data.rechtspraak.nl/uitspraken/content?id={}'.format(ecli)
    return etree.ElementTree().parse(link)


def retrieve_from_filesystem(ecli, rootpath):
    year = ecli[11:15]
    fn = str(year) + '/' + re.sub(':', '_', ecli) + '.xml'
    path = os.path.join(rootpath, fn)
    try:
        return etree.ElementTree().parse(path)
    except Exception as e:
        return None

def retrieve_from_any(ecli, rootpath):
    """
    Checks if it can find the xml document in the filesystem,
    otherwise retrieves it from the web.

    :param ecli:
    :param rootpath:
    :return:
    """
    el = retrieve_from_filesystem(ecli, rootpath)
    if el is None:
        try:
            el = retrieve_from_web(ecli)
        except Exception as e:
            el = None
    return el