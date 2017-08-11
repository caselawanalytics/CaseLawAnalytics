from caselawnet import link_extractor
import json
import pytest

def get_auth():
    auth = {}
    filename = 'settings.cfg'
    with open(filename, 'r') as f:
        exec(compile(f.read(), filename, 'exec'), globals())
    auth['username'] = LIDO_USERNAME
    auth['password'] = LIDO_PASSWD
    return auth

def get_invalid_auth():
    return {'username': 'INVALID',
     'password': 'INVALID'}

def test_invalid_authorization():
    ecli = "ECLI:NL:HR:2015:295"
    with pytest.raises(Exception):
        links_df, leg_df = link_extractor.get_links_articles(ecli, auth=get_invalid_auth())

def test_invalid_authorization_XMLparser():
    with pytest.raises(Exception):
        parser = link_extractor.LinkExtractorXMLParser(auth=get_invalid_auth())


def test_invalid_authorization_RDFparser():
    with pytest.raises(Exception):
        parser = link_extractor.LinkExtractorRDFParser(auth=get_invalid_auth())

def test_get_links():
    ecli = "ECLI:NL:HR:2015:295"
    auth = get_auth()
    links_df, leg_df = link_extractor.get_links_articles([ecli], auth=auth)
    assert len(links_df) == 0

def test_invalid_ecli_XMLParser():
    ecli = "INVALID"
    auth = get_auth()
    parser = link_extractor.LinkExtractorXMLParser(auth=auth)
    parser.load_ecli(ecli)
    links_df = parser.retrieve_all_references()
    assert len(links_df) == 0

def test_invalid_ecli_RDFParser():
    ecli = "INVALID"
    auth = get_auth()
    parser = link_extractor.LinkExtractorRDFParser(auth=auth)
    parser.load_ecli(ecli)
    links_df = parser.retrieve_all_references()
    assert len(links_df) == 0