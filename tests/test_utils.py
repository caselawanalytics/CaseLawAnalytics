from caselawnet import utils


def test_valid_eclis():
    test_eclis = [
        'ECLI:NL:HR:2009:BH2815',
        'ECLI:DE:BVerwG:2016:141116U5C10.15D0',
        'ECLI:HR:VSRH:2016:4048',
        'ECLI:FR:CCASS:2017:CR00727',
        'ECLI:EU:T:2017:291',
        'ECLI:EU:C:2017:308',
        'ECLI:EP:BA:2017:T086314.20170202',
        'ECLI:IT:CASS:1996:3230CIV'
    ]
    for e in test_eclis:
        assert utils.is_valid_ecli(e)