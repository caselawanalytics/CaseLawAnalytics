
from caselawnet import dbutils

# Settings
rechtspraak_datapath = '/data/caselaw/OpenDataRechtspraak/'
db_path = 'sqlite:///caselaw.db'



session = dbutils.get_session(adress=db_path)

dbutils.fill_db(session, rechtspraak_datapath)
session.close()

