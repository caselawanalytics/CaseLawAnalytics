from caselawnet import search
import json

def test_get_query_result():
    keyword = "ECLI:NL:HR:2015:295"
    result = search.get_query_result(keyword)
    assert 'Results' in result
    assert 'ResultCount' in result


def test_result_to_node():
    with open('test/test_ecli.json') as f:
        result = json.load(f)
    node = search.result_to_node(result)
    assert node['id'] == 'http://deeplink.rechtspraak.nl/uitspraak?id=ECLI:NL:HR:2015:295'
    assert node['ecli'] == 'ECLI:NL:HR:2015:295'