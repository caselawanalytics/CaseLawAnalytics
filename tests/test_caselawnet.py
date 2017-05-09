import caselawnet

def test_links_to_network_empty():
    links = []
    nodes, links = caselawnet.links_to_network(links)
    assert len(nodes) == 0
    assert len(links) == 0


def test_links_to_network():
    links = [{'source': 'ECLI:NL:HR:2009:BF0003',
              'target': 'ECLI:NL:HR:2008:BD3129'}]
    nodes, links = caselawnet.links_to_network(links)
    assert len(nodes) == 2
    assert len(links) == 1

def test_links_to_network_invalid():
    """
    TODO: what is the desired outcome?

    """
    links = [{'source': 'NONEXISTENT_A',
              'target': 'NONEXISTENT_B'}]
    nodes, links = caselawnet.links_to_network(links)
    assert len(nodes) == 2
    assert len(links) == 1



def test_search_keyword():
    keyword = 'ECLI:NL:HR:2009:BF0003'
    nodes = caselawnet.search_keyword(keyword)
    assert len(nodes) > 0
    assert 'id' in nodes[0]
    assert 'ecli' in nodes[0]


def test_enrich_eclis_empty():
    eclis = []
    nodes = caselawnet.enrich_eclis(eclis, rootpath=None)
    assert len(nodes) == 0

def test_enrich_eclis():
    eclis = ['ECLI:NL:HR:2009:BF0003']
    nodes = caselawnet.enrich_eclis(eclis, rootpath=None)
    assert len(nodes) == 1
    assert 'id' in nodes[0]
    assert 'ecli' in nodes[0]
    assert 'year' in nodes[0]