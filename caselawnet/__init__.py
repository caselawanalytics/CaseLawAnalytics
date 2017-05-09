import os

from .caselawnet import *
from .utils import to_sigma_json, to_csv

_DATAPATH = os.environ.get('RECHTSPRAAK_DATAPATH', None)
_DBPATH = os.environ.get('RECHTSPRAAK_DBPATH', None)

def rechtspraak_datapath():
    return _DATAPATH


def rechtspraak_dbpath():
    return _DBPATH