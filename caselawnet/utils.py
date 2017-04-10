import random
import json

def ecli_to_url(ecli):
    return "http://deeplink.rechtspraak.nl/uitspraak?id={}".format(ecli)


def url_to_ecli(url):
    ecli = url.split('=')[-1]
    return ecli


def ecli_to_year(ecli):
    return int(ecli.split(':')[3])


def to_d3_json(nodes, links, filename):
    with open(filename, 'w') as outfile:
        json.dump({'nodes': nodes, 'links': links}, fp=outfile)


def to_sigma_json(nodes, links, title, filename=None):
    # Add random start position
    nodes = [node.copy() for node in nodes]
    for node in nodes:
        node['x'] = random.random()
        node['y'] = random.random()
    if filename is None:
        return json.dumps({'title': title, 'nodes': nodes, 'edges': links})
    with open(filename, 'w') as outfile:
        json.dump({'title': title, 'nodes': nodes, 'edges': links}, fp=outfile)


def to_csv(nodes, filename=None, variables=None):
    import pandas as pd
    if len(nodes) == 0:
        df = pd.DataFrame()
    else:
        if variables is None:
            variables = nodes[0].keys()
        df = pd.DataFrame(nodes).set_index('id')
    if 'abstract' in variables:
        df['abstract'] = df['abstract'].str.replace('\s', ' ')
    if filename is None:
        return df.to_csv()
    else:
        df.to_csv(filename)