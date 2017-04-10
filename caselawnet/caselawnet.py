"""
This module forms the main interface to the functionalities of caselawnet.
"""
import warnings
from caselawnet import search, network_analysis

def search_keyword(keyword, **args):
    """
    Search the rechtspraak.nl api for this keyword.
    It returns a list of nodes, where each node represents one case.
    The nodes contain at least the field 'ecli' for ECLI identifier
    and the field 'id' for URI identifier.

    :param keyword: keyword to search for
    :param args: search parameters
    :return: list of rich nodes
    """
    nodes = search.search(keyword, **args)
    return nodes


def enrich_eclis(eclis):
    """
    Retrieves meta information for the proviced ECLI identifiers.
    :param eclis: list of ECLI identifiers
    :return: list of rich nodes.
    """
    nodes = [{'ecli': ecli} for ecli in eclis]

    return nodes


def retrieve_links(eclis):
    """
    Retrieve references between cased from the LiDO api (http://linkeddata.overheid.nl)
    If the nodes are not yet rich (so: only ecli number),
     the metadata is retrieved as well.
    :param eclis: either a list of ecli number or a list of rich nodes
    :return:
    """
    warnings.warn('The LiDO link API is not functional yet!', Warning)
    links = []
    return links


def get_network(nodes, links):
    """
    Add network information

    :param nodes: List of nodes
    :param links: List of links
    :return: nodes, links: nodes has network information
    """
    nodes = network_analysis.add_network_statistics(nodes, links)
    return nodes, links

