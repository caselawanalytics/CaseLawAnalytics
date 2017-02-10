"""
Use:
python cloudant-meta-to-rdf.py [-s 0 -e 10000 -b 5000 -f turtle] output_path

-s  start index
-e  end index
-b  batch size (number of documents to retrieve at once)
-f  format (turtle or n3)
"""

import os
import json
from rdflib import Graph
import six.moves.urllib as urllib

def json_from_url(url):
    hdr = {
    'Accept':'application/ld+json, application/json;p=0.9, */*;q=0.1',
    'User-agent':
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'
    }
    req = urllib.request.Request(url,headers=hdr)
    page = urllib.request.urlopen(req)
    all_json = json.loads(page.read().decode('utf-8'))
    return all_json

def serialize_metadata(maximum, skip, outputpath, form):
    g = Graph()
    base_url = "https://rechtspraak.lawreader.nl/_all/"
    url = base_url+'?limit='+str(maximum)+'&skip='+str(skip)
    try:
        all_json = json_from_url(url)
        context = all_json['@context']
        for graph in all_json['@graph']:
            g.parse(data=json.dumps(graph), format='json-ld', context=context)
        g.serialize(outputpath, format=form)
    except Exception as e:
        print(e)
    return g


if __name__ == "__main__":
    import sys
    import getopt
    optlist, args = getopt.getopt(sys.argv[1:], 's:e:b:f:')
    optdict = dict(optlist)
    outputpath = args[0]
    start = int(optdict.get('-s', 0))
    end = optdict.get('-e', None)
    batchsize = int(optdict.get('-b', 5000))
    form = optdict.get('-f', 'turtle')
    if form == 'turtle':
        ext = '.ttl'
    else:
        ext = '.'+form

    print("Writing {} files to {}, starting from {} in batches of size {}".format(
        form, outputpath, start, batchsize
    ))
    if end is None:
        alldocs_json = json_from_url("https://rechtspraak.cloudant.com/ecli/_all_docs?limit=0")
        end = alldocs_json['total_rows']
        print('Total nr of documents: ', end)
    end = int(end)


    for i in range(start, end, batchsize):
        outfile = os.path.join(outputpath, 'meta_' + str(i) + ext)
        serialize_metadata(batchsize, i, outfile, form)
        print("Done with batch" + str(i))