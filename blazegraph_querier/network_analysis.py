import networkx as nx
from networkx.readwrite import json_graph

def get_network(nodes, links):
    edges = []
    node_indices = {nodes[i]['id']: i for i in range(len(nodes))}
    for link in links:
        edge = {}
        edge['source'] = node_indices[link['source']]
        edge['target'] = node_indices[link['target']]
        edge['id'] = link['id']
        edges.append(edge)
    graph = json_graph.node_link_graph({'nodes': nodes, 'links': edges},
                                       directed=True, multigraph=False)
    return graph


def add_network_statistics(nodes, links):
    graph = get_network(nodes, links)
    hubs, authorities = nx.hits(graph)
    statistics = {
        'degree': nx.degree(graph),
        'in_degree': graph.in_degree(),
        'out_degree': graph.out_degree(),

        'degree_centrality': nx.degree_centrality(graph),
        'in_degree_centrality': nx.in_degree_centrality(graph),
        'out_degree_centrality': nx.out_degree_centrality(graph),
        'betweenness_centrality': nx.betweenness_centrality(graph),
        'hubs': hubs,
        'authorities': authorities
    }
    for node in nodes:
        nodeid = node['id']
        for var in statistics.keys():
            node[var] = statistics[var][nodeid]

    return nodes

