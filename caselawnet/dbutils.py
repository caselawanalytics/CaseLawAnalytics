from sqlite3 import dbapi2 as sqlite3
import os
import zipfile
from lxml import etree
from . import enrich, parser

schema = """
drop table if exists cases;
create table cases (
  ecli text primary key,
  id text not null,
  title text,
  creator text,
  date text,
  subject text,
  abstract text
);
"""

def connect_db(dbpath='caselaw.db'):
    """Connects to the specific database."""
    rv = sqlite3.connect(dbpath)
    return rv


def init_db(dbpath, filepath):
    """
    Initalizes the database and fills it with data.
    NB: if the database already contains data, it will be lost!

    :param dbpath: path to the database
    :param filepath: System path to the unzipped rechtspraak.nl data
    :return:
    """
    db = connect_db(dbpath)
    db.cursor().executescript(schema)
    db.commit()
    fill_db(db, filepath)


def retrieve_ecli(ecli, db):
    query = 'Select * from cases where ecli=?'
    cursor = db.execute(query, (ecli,))
    field_names = [d[0] for d in cursor.description]
    results = cursor.fetchall()
    if len(results)>0:
        return {field_names[i]: results[0][i] for i in range(len(field_names))}
    else:
        return None

def fill_db(db, filepath):
    for dir0 in os.listdir(filepath):
        print("Processing directory", dir0)
        dir0 = os.path.join(filepath, dir0)
        if os.path.isdir(dir0):
            for dir1 in os.listdir(dir0):
                dir1 = os.path.join(dir0, dir1)
                if zipfile.is_zipfile(dir1):
                    zf = zipfile.ZipFile(dir1, 'r')
                    for n in zf.namelist():
                        file_to_db(n, db, zf)

def file_to_db(filename, db, zf):
    try:
        c = db.cursor()
        ecli = filename.split('.')[0].replace('_', ':')
        # Check if ecli already exists
        if len(c.execute(
                'select ecli from cases where ecli=?',
                (ecli,)).fetchall()) == 0:
            data = zf.read(filename)
            node = parse_data(data, ecli)
            insert_node(node, c)
            db.commit()
    except Exception as e:
        print(filename, e)

def parse_data(data, ecli):

    el = etree.fromstring(data)
    g = parser.parse_xml_element(el, ecli)
    nodes = enrich.graph_to_nodes(g)
    if len(nodes)>1:
        print(ecli, len(nodes))
    node = nodes[0]
    return node


def insert_node(node, c):
    c.execute('INSERT OR IGNORE INTO cases VALUES (?,?,?,?,?,?,?) ',
              (node['ecli'],
               node['id'],
              node['title'],
              node['creator'],
              node['date'],
              node['subject'],
              node['abstract']))