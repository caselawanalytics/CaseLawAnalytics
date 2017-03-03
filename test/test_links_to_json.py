from rechtspraak_query_app import links_to_json
import io

def test_read_csv():
    path = io.StringIO("ECLI:NL:HR:2012:BX7943,ECLI:NL:HR:2010:BL1943")
    links_df, eclis = links_to_json.read_csv(path, sep=',', header=None)
    assert len(eclis) == 2
    assert links_df.shape == (1,2)