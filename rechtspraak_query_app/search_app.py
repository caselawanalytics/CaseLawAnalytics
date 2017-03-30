from . import search
import json
import traceback

import io
from flask import Flask, request, render_template, g
app = Flask(__name__)


def get_parameter_values():
    values = getattr(g, '_values', None)
    if values is None:
        with open('rechtspraak_query_app/values.json') as f:
            values = json.load(f)
        g._values = values
    return values

@app.route('/')
def index():
    values = get_parameter_values()
    return render_template('search.html',
                           values=values)

@app.route('/query/', methods=['POST'])
def query():
    print(request.form)
    print(request.form.getlist('Instanties'))
    values = get_parameter_values()
    return render_template('search.html',
                           values=values)