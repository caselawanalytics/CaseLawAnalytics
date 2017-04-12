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