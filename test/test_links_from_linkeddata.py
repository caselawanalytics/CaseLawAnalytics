from rechtspraak_query_app import links_from_linkeddata

def test_retrieve_graph_empty():
    ecli = "NONEXISTINGECLI"
    g = links_from_linkeddata.retrieve_graph(ecli)
    assert len(g) == 0
