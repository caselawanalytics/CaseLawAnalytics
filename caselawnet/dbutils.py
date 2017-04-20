from sqlite3 import dbapi2 as sqlite3

schema = """
drop table if exists cases;
create table cases (
  ecli text primary key,
  id text not null,
  abstract text
);
"""

def connect_db(dbpath='caselaw.db'):
    """Connects to the specific database."""
    rv = sqlite3.connect(dbpath)
    rv.row_factory = sqlite3.Row
    return rv


def init_db(db):
    """Initializes the database."""
    if db is None:
        db = connect_db()
    db.cursor().executescript(schema)
    db.commit()
    fill_db()


def fill_db(db):
    # TODO: fill database with rechtspraak.nl meta data
    return None