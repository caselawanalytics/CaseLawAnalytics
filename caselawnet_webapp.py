import caselawnet
import traceback
import json
import io
from flask import Flask, request, render_template, make_response, g, send_from_directory
import pandas as pd
import random
import os
from caselawnet import dbutils
app = Flask(__name__)


ALLOWED_EXTENSIONS = set(['json', 'csv'])
app.config.from_pyfile('settings.cfg')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        if app.config['DBPATH'] is not None:
            db = g._database = dbutils.get_session(app.config['DBPATH'])
    return db
    
    
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    return render_template('index.html')


def read_csv(path, sep=',', header='infer'):
    links_df = pd.read_csv(path, sep=sep, header=header)
    links_df.columns = ['source', 'target']
    # Strip leading or trailing whitespace
    links_df.source = links_df.source.str.strip()
    links_df.target = links_df.target.str.strip()
    links_df = links_df.drop_duplicates()
    eclis = list(pd.concat([links_df['source'], links_df['target']]).unique())
    return links_df, eclis

def save_result(data, extension):
    name = '%030x' % random.randrange(16 ** 30) + '.' + extension
    with open(os.path.join(app.config['UPLOAD_FOLDER'], name), 'w', encoding='utf-8') as fn:
        fn.write(data)
    return name

@app.route('/query_links', methods=['POST'])
def query_links():
    try:
        network_json = None
        network_csv = None
        warning = None
        if('links' in request.form):
            links_csv = request.form['links']
            title = request.form.get('title', 'Network')
            links_df, eclis = read_csv(io.StringIO(links_csv),
                                                     sep=',', header=None)
            links_dict = links_df.to_dict(orient='records')
            nodes, links = caselawnet.links_to_network(links_dict, db_session=get_db())
            if len(nodes) < len(eclis):
                existing_eclis = [node['ecli'] for node in nodes]
                difference = set(eclis) - set(existing_eclis)
                warning = "The following ECLI cases were not found: " + \
                    str(difference)
            if len(nodes) == 0:
                return render_template("index.html",
                                       error="No resulting matches!")
            network_json = caselawnet.to_sigma_json(nodes, links, title)
            network_csv = caselawnet.to_csv(nodes)

            json_file = save_result(network_json, 'json')
            csv_file = save_result(network_csv, 'csv')
            print(json_file, csv_file)
        return render_template("index.html",
                               network_json=network_json,
                               network_csv=network_csv,
                               json_file=json_file,
                               csv_file=csv_file,
                               warning=warning)
    except Exception as error:
        print(error)
        traceback.print_exc()
        return render_template("index.html",
                               error="Sorry, something went wrong!")

@app.route('/downloads/<filename>_<filename_out>')
def download_file(filename, filename_out):
    print(filename_out)
    if filename_out is None:
        fn, ext = os.path.splitext(filename)
        filename_out = 'network' + ext
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename,
                               as_attachment=True,
                               attachment_filename=filename_out)



def get_parameter_values():
    values = getattr(g, '_values', None)
    if values is None:
        with open('static/values.json') as f:
            values = json.load(f)
        g._values = values
    return values

@app.route('/search/')
def search():
    values = get_parameter_values()
    return render_template('search.html',
                           values=values)

@app.route('/search_query/', methods=['POST'])
def search_query():
    nodes_file = None
    links_file = None
    network_file = None
    nr_results = None
    print(request.form)
    print(request.form.getlist('Instanties'))
    values = get_parameter_values()
    form = {k.lower(): request.form.getlist(k) for k in request.form.keys()}
    kw = form.pop('keyword', '')[0]
    print(kw, form)
    if kw is not '':
        nodes = caselawnet.search_keyword(kw, **form)
        nr_results = len(nodes)
        if nr_results > 0:
            nodes_csv = caselawnet.to_csv(nodes)
            nodes_file = save_result(nodes_csv, 'csv')
            links = caselawnet.retrieve_links(nodes)
            nodes, links = caselawnet.get_network(nodes, links)
            links_csv = pd.DataFrame(links).to_csv(index=False)
            links_file = save_result(links_csv, 'csv')
            network_json = caselawnet.to_sigma_json(nodes, links, kw)
            network_file = save_result(network_json, 'json')
    return render_template('search.html',
                           values=values,
                           nodes_file=nodes_file,
                           links_file=links_file,
                           network_file= network_file,
                           nr_results=nr_results)
    
if __name__ == '__main__':
    app.run(debug=True)
