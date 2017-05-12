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

UPLOAD_FOLDER = '/tmp/'
ALLOWED_EXTENSIONS = set(['json', 'csv'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DBPATH = 'mysql+mysqldb://caselawapp:abc@localhost/caselaw'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = dbutils.get_session(DBPATH)
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
    with open(os.path.join(app.config['UPLOAD_FOLDER'], name), 'w') as fn:
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

@app.route('/downloads/<filename>')
def download_file(filename):
    fn, ext = os.path.splitext(filename)
    filename_out = 'network' + ext
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename,
                               as_attachment=True,
                               attachment_filename=filename_out)

@app.route('/download-json/', methods=['POST'])
def download_json():
    network_json = ""
    if('network_json' in request.form):
        network_json = request.form['network_json']
    response = make_response(network_json)
    response.headers[
        "Content-Disposition"] = "attachment; filename=network_json.json"
    return response


@app.route('/download-csv/', methods=['POST'])
def download_csv():
    network_csv = ""
    if('network_csv' in request.form):
        network_csv = request.form['network_csv']
    response = make_response(network_csv)
    response.headers[
        "Content-Disposition"] = "attachment; filename=network_csv.csv"
    return response



def get_parameter_values():
    values = getattr(g, '_values', None)
    if values is None:
        with open('static/values.json') as f:
            values = json.load(f)
        g._values = values
    return values

#@app.route('/search/')
def search():
    values = get_parameter_values()
    return render_template('search.html',
                           values=values)

#@app.route('/search_query/', methods=['POST'])
def search_query():
    print(request.form)
    print(request.form.getlist('Instanties'))
    values = get_parameter_values()
    return render_template('search.html',
                           values=values)
    
if __name__ == '__main__':
    app.run(debug=True)