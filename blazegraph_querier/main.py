from . import query_to_json

from flask import Flask, request, render_template
app = Flask(__name__)


@app.route('/')
def hello_world():
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