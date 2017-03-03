"""
This script gets a csv file with links. it should contain two columns,
denoting the ECLI identifiers for 'from' and 'to' (it assumes headers).

Usage:
python scripts/links_to_json.py input_file.csv output_file.json "title"
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
from query_app import links_to_json, query_to_json



if __name__ == "__main__":
    import sys
    print(sys.argv)
    file_in = sys.argv[1]
    file_out = sys.argv[2]
    title = sys.argv[3]
    links_df, eclis = links_to_json.read_csv(file_in, sep=',')
    graph = links_to_json.make_graph(links_df, eclis)
    nodes, links = links_to_json.graph_to_network(graph)
    query_to_json.to_sigma_json(nodes, links, title, filename=file_out)



