import os
import zipfile
from lxml import etree
from . import enrich, parser
import sqlalchemy
from sqlalchemy.orm import sessionmaker

schema = """
create table if not exists cases (
  ecli varchar(100) primary key,
  id varchar(200) not null,
  title varchar(200),
  creator varchar(200),
  date char(10),
  subject varchar(200),
  abstract text
);
"""

    
def get_session(adress):
    db = sqlalchemy.create_engine(adress)
    Session = sessionmaker(bind=db)
    return Session()

def retrieve_ecli(ecli, db_session):
    """
    Retrieves the ecli from a database
    
    :param ecli: The ECLI identifier
    :param db_session: a sqlalchemy session object
    """
    res = db_session.execute('select * from cases where ecli=:ecli', 
                                {"ecli":ecli})
    field_names = res.keys()
    results = res.fetchall()
    if len(results)>0:
        return {field_names[i]: results[0][i] for i in range(len(field_names))}
    else:
        return None

def fill_db(db_session, filepath):
    db_session.execute(schema)
    for dir0 in os.listdir(filepath):
        print("Processing directory", dir0)
        dir0 = os.path.join(filepath, dir0)
        if os.path.isdir(dir0):
            for dir1 in os.listdir(dir0):
                dir1 = os.path.join(dir0, dir1)
                if zipfile.is_zipfile(dir1):
                    zf = zipfile.ZipFile(dir1, 'r')
                    for n in zf.namelist():
                        file_to_db(n, db_session, zf)

def file_to_db(filename, db_session, zf):
    try:
        ecli = filename.split('.')[0].replace('_', ':')
        # Check if ecli already exists
        if retrieve_ecli(ecli, db_session) is None:
            data = zf.read(filename)
            node = parse_data(data, ecli)
            insert_node(node, db_session)
            db_session.commit()
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


def insert_node(node, db_session):
    db_session.execute('INSERT OR IGNORE INTO cases VALUES (:ecli,:id,:title,:creator,:date,:subject,:abstract) ',
           {'ecli': node['ecli'],
            'id': node['id'],
            'title': node['title'],
            'creator': node['creator'],
             'date': node['date'],
             'subject': node['subject'],
             'abstract': node['abstract']})