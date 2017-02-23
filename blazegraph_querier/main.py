from . import query_to_json, links_to_json

import io
from flask import Flask, request, render_template, make_response, send_file
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query_keyword', methods=['POST'])
def query():
    network_json = None
    network_csv = None
    print(request.form)
    if('keyword' in request.form):
        searchstring = request.form['keyword']
        only_linked = request.form.get('only_linked', False)
        nodes, links = query_to_json.query(searchstring,
                                                     only_linked=only_linked)
        network_json = query_to_json.to_sigma_json(nodes, links, searchstring)
        network_csv = query_to_json.to_csv(nodes)

    return render_template("index.html",
                           network_json=network_json,
                           network_csv=network_csv)

@app.route('/query_links', methods=['POST'])
def query_links():
    network_json = None
    network_csv = None
    print(request.form)
    if('links' in request.form):
        links_csv = request.form['links']
        title = request.form.get('title', 'Network')
        links_df, eclis = links_to_json.read_csv(io.StringIO(links_csv),
                                                 sep=',', header=None)
        graph = links_to_json.make_graph(links_df, eclis)
        nodes, links = links_to_json.graph_to_network(graph)
        network_json = query_to_json.to_sigma_json(nodes, links, title)
        network_csv = query_to_json.to_csv(nodes)
    return render_template("index.html",
                           network_json=network_json,
                           network_csv=network_csv)

@app.route('/download-json/', methods=['POST', 'GET'])
def download_json():
    # TODO: get the json from somewhere (cache)
    network_json = ""
    response = make_response(network_json)
    response.headers["Content-Disposition"] = "attachment; filename=network_json.json"
    return response
