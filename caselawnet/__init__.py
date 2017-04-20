import os

from .caselawnet import *
from .utils import to_sigma_json, to_csv

_DATAPATH = os.environ.get('RECHTSPRAAK_DATAPATH', None)

def rechtspraak_datapath():
    return _DATAPATH