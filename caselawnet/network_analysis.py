import networkx as nx
from networkx.readwrite import json_graph
import community

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

def get_community(graph, nodes):
    graph_u = nx.Graph(graph)
    partition = community.best_partition(graph_u)
    for node in nodes:
        node['community'] = str(partition[node['id']])

def add_network_statistics(nodes, links):
    if len(nodes)==0:
        return nodes
    graph = get_network(nodes, links)
    degree = nx.degree(graph)
    if max(degree.values()) > 0:
        hubs, authorities = nx.hits(graph)
        statistics = {
            'degree': degree,
            'in_degree': graph.in_degree(),
            'out_degree': graph.out_degree(),

            'degree_centrality': nx.degree_centrality(graph),
            'in_degree_centrality': nx.in_degree_centrality(graph),
            'out_degree_centrality': nx.out_degree_centrality(graph),
            'betweenness_centrality': nx.betweenness_centrality(graph),
            'closeness_centrality': nx.closeness_centrality(graph),
            'pagerank': nx.pagerank(graph),
            'hubs': hubs,
            'authorities': authorities
        }
    else:
        statistics = {}

    # for relative in-degree we sort on date
    derive_date = lambda k: k['date'] if k['date']!='' else '{}-01-01'.format(k['year'])
    nodes.sort(key=derive_date, reverse=True)
    for i, node in enumerate(nodes):
        nodeid = node['id']
        for var in statistics.keys():
            node[var] = statistics[var][nodeid]
        if 'in_degree' in node:
            node['rel_in_degree'] = node['in_degree'] / float(max(i, 1))
    get_community(graph, nodes)
    return nodes
