import requests
import json

'''These functions harvest public data from hudoc.echr.coe.int.'''

hudoc_base = 'https://hudoc.echr.coe.int'
selectColumns = '&select=sharepointid,Rank,ECHRRanking,languagenumber,itemid,docname,doctype,application,appno,conclusion,importance,originatingbody,typedescription,kpdate,kpdateAsText,documentcollectionid,documentcollectionid2,languageisocode,extractedappno,isplaceholder,doctypebranch,respondent,ecli,appnoparts,sclappnos,article'
filters = 'contentsitename:ECHR AND '
filters+= '(NOT (doctype=PR OR doctype=HFCOMOLD OR doctype=HECOMOLD)) AND '
filters+= '((documentcollectionid="GRANDCHAMBER") OR (documentcollectionid="CHAMBER") OR documentcollectionid="DECISIONS")'

# Values scraped from hudoc -- not 100% they are correct
kpthesaurus = {
    '(Art. 1) Obligation to respect human rights': '293',
    '(Art. 1) High Contracting Party': '176',
    '(Art. 1) Jurisdiction of States': '210',
    '(Art. 1) Responsibility of States': '430',
    '(Art. 2) Right to life': '449',
    '(Art. 3) Prohibition of torture': '350',
    '(Art. 4) Prohibition of slavery and forced labour': '349',
    '(Art. 5) Right to liberty and security': '448',
    '(Art. 6) Right to a fair trial': '445',
    '(Art. 7) No punishment without law': '288',
    '(Art. 8) Right to respect for private and family life': '451',
    '(Art. 9) Freedom of thought, conscience and religion': '154',
    '(Art. 10) Freedom of expression-{general}': '149',
    '(Art. 11) Freedom of assembly and association': '145',
    '(Art. 12) Right to marry': '450',
    '(Art. 13) Right to an effective remedy': '444',
    '(Art. 14) Prohibition of discrimination': '343',
    '(Art. 15) Derogation in time of emergency': '96',
    '(Art. 16) Restrictions on political activity of aliens-{general}': '571',
    '(Art. 17) Prohibition of abuse of rights': '340',
    '(Art. 18) Limitation on use of restrictions on rights': '232',
    '(Art. 19) Establishment of the Court': '120',
    '(Art. 33) Inter-State cases': '567',
    '(Art. 34) Individual applications': '183',
    '(Art. 35) Admissibility criteria': '14',
    '(Art. 37) Striking out applications-{general}': '609',
    '(Art. 38) Examination of the case-{general}': '121',
    '(Art. 39) Friendly settlements': '138',
    '(Art. 41) Just satisfaction-{general}': '216',
    '(Art. 46) Binding force and execution of judgments': '26',
    '(Art. 47) Advisory opinions-{general}': '563',
    '(Art. 48) Advisory jurisdiction of the Court-{general}': '562',
    '(Art. 52) Inquiries by the Secretary General': '569',
    '(Art. 53) Rights otherwise guaranteed': '441',
    '(Art. 54) Powers of the Committee of Ministers': '312',
    '(Art. 55) Renunciation of other means of settlement': '414',
    '(Art. 56) Territorial application-{general}': '483',
    '(Art. 57) Reservations-{general}': '570',
    '(Art. 58) Denunciation': '517',
    '(Art. 59) Signature and ratification-{general}': '465',
    '(P1-1) Protection of property': '369',
    '(P1-2) Right to education-{general}': '573',
    '(P1-3) Right to free elections-{general}': '574',
    '(P1-4) Territorial application': '484',
    '(P1-6) Signature and ratification': '466',
    '(P4-1) Prohibition of imprisonment for debt-{general}': '560',
    '(P4-2) Freedom of movement-{general}': '566',
    '(P4-3) Prohibition of expulsion of nationals': '345',
    '(P4-4) Prohibition of collective expulsion of aliens-{general}': '341',
    '(P4-5) Territorial application': '485',
    '(P4-7) Signature and ratification': '467',
    '(P6-1) Abolition of the death penalty-{general}': '561',
    '(P6-2) Death penalty in time of war-{general}': '564',
    '(P6-4) Prohibition of reservations-{general}': '568',
    '(P6-5) Territorial application': '486',
    '(P6-7) Signature and ratification': '468',
    '(P7-1) Procedural safeguards relating to expulsion of aliens': '338',
    '(P7-2) Right of appeal in criminal matters': '443',
    '(P7-3) Compensation for wrongful conviction': '47',
    '(P7-4) Right not to be tried or punished twice-{general}': '572',
    '(P7-5) Equality between spouses-{general}': '565',
    '(P7-6) Territorial application': '487',
    '(P7-8) Signature and ratification': '469',
    '(P12-1) General prohibition of discrimination': '600',
    '(P13-1) Abolition of the death penalty': '642',
    'Accessibility': '597',
    'Extradition': '630',
    'Foreseeability': '598',
    'Expulsion': '631',
    'Jurisdiction of the Court': '211',
    'Margin of appreciation': '238',
    'Non-derogable rights and freedoms': '276',
    'Positive obligations': '310',
    'Proportionality': '354',
    'Safeguards against abuse': '599',
    '(Former Art. 25)': '610',
    '(Former Art. 32)': '611',
    '(Former Art. 44) Capacity to bring a case before the Court': '516',
    '(Former Art. 46)': '612',
    '(Former Art. 47) Three-month period': '490',
    '(Former Art. 48) State whose national is a victim': '477',
    '(Former Art. 49) Dispute as to jurisdiction': '102'
}

def buildJurisdictionQueryUrl():
    kpthesaurus_keyword = '(Art. 1) Jurisdiction of States'
    query_url = buildKeywordQueryUrl(kpthesaurus_keyword)
    return query_url

def buildKeywordQueryUrl(kpthesaurus_keyword):
    kptVal = kpthesaurus[kpthesaurus_keyword]
    query = '((kpthesaurus="' + kptVal + '")) AND '
    query+= '((languageisocode="ENG")) '    # Filter: language = English
    query_url = buildECHRurl(query)
    return query_url

def buildECHRurl(querySeed, selectColumns=selectColumns):
    query = querySeed
    query+= ' AND ' + filters
    query+= selectColumns
    query_url = hudoc_base + '/app/query/results?sort=&start=0&length=1000&query=' + query
    return query_url

def buildAppNoUrl(appNo):
    query = '((appno:"' + appNo + '"))'
    query_url = buildECHRurl(query)
    return query_url

def buildECLIUrl(ecli):
    query = '((ecli:"' + ecli + '"))'
    query_url = buildECHRurl(query)
    return query_url

def buildSCLUrl(appno):
    query = '((sclappnos:"' + appno + '"))'
    query_url = buildECHRurl(query)
    return query_url

def kpdateToDate(kpdate):
    '''Confert date from format: 1/19/2010 12:00:00 AM to format: yyyy-mm-dd'''
    parts = kpdate.split(' ')[0].split('/')
    return '{}-{}-{}'.format(parts[2], parts[1], parts[0])

def columnToNode(column):
    ecli = column['ecli']
    appno = column['appno'].split(';')[0]
    title = column['docname']
    abstract = column['conclusion']
    date = kpdateToDate(column['kpdate'])
    year = int(date.split('-')[0])
    creator = column['doctypebranch']
    subject = column['article']
    articles = column['article'].split(';')
    refersTo = list(set(column['sclappnos'].split(';') + column['extractedappno'].split(';')))
    return {
        # "id": "http://deeplink.rechtspraak.nl/uitspraak?id=" + ecli,
        "id": 'https://hudoc.echr.coe.int/eng#{"appno":["%s"]}'%appno,
        "appno": appno,
        "ecli": ecli,
        "creator": creator,
        "title": title,
        "abstract": abstract,
        "date": date,
        "subject": subject,
        "articles": articles,
        "year": year,
        "refersTo": refersTo,
        "language": column["languageisocode"]
    }

def construct_or_clause(li, s):
    return '((' + ' OR '.join([s.format(l) for l in li]) + '))'

def buildKeywordUrl(kpthesaurus_keyword, languages = ['ENG', 'FRE'], doc_types = ['JUDGMENTS', 'DECISIONS']):
    kptVal = kpthesaurus[kpthesaurus_keyword]
    keyword_filter = '((kpthesaurus="' + kptVal + '"))'
    language_filter = construct_or_clause(languages, 'languageisocode="{}"')
    doc_type_filter = construct_or_clause(doc_types, 'documentcollectionid="{}"')

    filters = [keyword_filter, language_filter, doc_type_filter]
    query = ' AND '.join(filters)

    query_url = hudoc_base + '/app/query/results?sort=&start=0&length=1000&query=' + query + selectColumns
    return query_url


def getDataForKeyword(kpthesaurus_keyword):
    url = buildKeywordQueryUrl(kpthesaurus_keyword)
    nodes = getDataForUrl(url)
    return nodes

def getDataForUrl(url):
    resp = requests.get(url)
    data = json.loads(resp.text)
    nodes = [ columnToNode(hit['columns']) for hit in data['results'] ]
    return nodes

def getCasesCiting(appNo):
    url = buildSCLUrl(appNo)
    resp = requests.get(url)
    data = json.loads(resp.text)
    cases = [ columnToNode(hit['columns']) for hit in data['results'] ]
    return cases
