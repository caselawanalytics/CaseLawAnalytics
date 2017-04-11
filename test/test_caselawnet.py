import caselawnet

def test_links_to_network_empty():
    links = []
    nodes, links = caselawnet.links_to_network(links)
    assert len(nodes) == 0
    assert len(links) == 1