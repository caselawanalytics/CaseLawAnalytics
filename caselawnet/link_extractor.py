import rdflib
import requests
from io import StringIO
from lxml import etree
import pandas as pd



def get_links_articles(eclis, parser=None, auth=None, nr_degrees=0):
    '''

    :param eclis:
    :return:
    '''
    if parser is None:
        parser = LinkExtractorXMLParser(auth=auth)
    ecli_list = [ecli for ecli in eclis]
    new_ecli_list = ecli_list
    load_eclis = ecli_list
    while nr_degrees >= 0:

        ecli_list = new_ecli_list
        for ecli in load_eclis:
            parser.load_ecli(ecli)
        parser.retrieve_all_references()
        links_df = parser.filter_caselaw_links()
        links_df['source_id'] = links_df['source_id'].apply(
            parser.lido_to_ecli)
        links_df['target_id'] = links_df['target_id'].apply(
            parser.lido_to_ecli)

        leg_df = parser.filter_legislation_links()
        leg_df['source_id'] = leg_df['source_id'].apply(
            parser.lido_to_ecli)

        new_ecli_list = set(links_df['source_id']).union(links_df['source_id'])

        load_eclis = new_ecli_list.difference(ecli_list)
        nr_degrees -= 1

    links_df = links_df[links_df['source_id'].isin(ecli_list)]
    links_df = links_df[links_df['target_id'].isin(ecli_list)]
    links_df = links_df.drop_duplicates()
    links_df.columns = ['source', 'target']
    leg_df = leg_df[leg_df['source_id'].isin(ecli_list)]

    return links_df, leg_df



class LinkExtractorParser(object):

    def __init__(self, auth=None):
        if auth is None:
            try:
                auth = {}
                filename = 'settings.cfg'
                with open(filename) as f:
                    exec(compile(f.read(), filename, 'exec'))
                auth['username'] = LIDO_USERNAME
                auth['password'] = LIDO_PASSWD
            except Exception:
                'No valid authentication file!'
                raise
        self.auth = auth
        self.links_df = pd.DataFrame()

    def clear(self):
        self.links_df = pd.DataFrame()

    def load_ecli(self):
        """
        abstract method
        :return:
        """
        pass

    def get_lido_id(self, ecli):
        return "http://linkeddata.overheid.nl/terms/jurisprudentie/id/" + ecli

    def lido_to_ecli(self, lido_id):
        return lido_id.split('/')[-1]

    def filter_legislation_links(self):
        """
        Filters links from case law to legislation
        """
        valid_target_types = ['http://linkeddata.overheid.nl/terms/Wet',
                              'http://linkeddata.overheid.nl/terms/Artikel']
        links_legislation = self.links_df[
            self.links_df['target_type'].isin(valid_target_types)]
        links_legislation = links_legislation[
            ['source_id', 'target_id', 'target_title']]
        links_legislation = links_legislation.drop_duplicates()
        return links_legislation

    def filter_caselaw_links(self):
        """
        Filters computer-extracted links between case law
        """
        valid_target_types = [
            'http://linkeddata.overheid.nl/terms/Jurisprudentie']
        links_caselaw = self.links_df[
            self.links_df['target_type'].isin(valid_target_types)]
        valid_link_types = [
            'http://linkeddata.overheid.nl/terms/linktype/id/lx-referentie']
        links_caselaw = links_caselaw[
            links_caselaw['link_type'].isin(valid_link_types)]
        links_caselaw = links_caselaw[['source_id', 'target_id']].drop_duplicates()
        return links_caselaw


class LinkExtractorXMLParser(LinkExtractorParser):
    def __init__(self, auth=None):
        super().__init__(auth)
        self.xml_elements = []

    def clear(self):
        super().clear()
        self.xml_elements = []

    def load_ecli(self, ecli):
        url = "http://linkeddata.overheid.nl/service/get-links?id={}&output=xml".format(
            self.get_lido_id(ecli))
        response = requests.get(url,
                                auth=requests.auth.HTTPBasicAuth(
                                    self.auth['username'], self.auth['password']))
        xml_text = response.text
        self.xml_elements.append(etree.fromstring(xml_text.encode('utf8')))

    def get_links_from_outgoing(self, sub_ref, source_id):
        return {
                'target_id': sub_ref.attrib['idref'],
                'link_type': sub_ref.attrib['type'],
                'source_id': source_id
                }

    def get_links_from_incoming(self, sub_ref, target_id):
        return {
                'source_id': sub_ref.attrib['idref'],
                'link_type': sub_ref.attrib['type'],
                'target_id': target_id,
                }

    def merge_links_nodes(self, links_df, nodes_df):
        links_df = links_df.merge(nodes_df, left_on=['source_id'],
                                  right_on=['id'], how='left')
        links_df = links_df.rename(
            columns={'title': 'source_title', 'type': 'source_type'})
        links_df = links_df.drop('id', axis=1)
        links_df = links_df.merge(nodes_df, left_on=['target_id'],
                                  right_on=['id'], how='left')
        links_df = links_df.rename(
            columns={'title': 'target_title', 'type': 'target_type'})
        links_df = links_df.drop('id', axis=1)
        return links_df

    def retrieve_all_references(self):
        links = []
        nodes = []
        for el in self.xml_elements:
            for sub in list(el.iterchildren('subject')):
                sub_id = sub.attrib['id']

                node_type = ''
                for s in sub.iterchildren('{*}type'):
                    # TODO: can there be multiple types?
                    node_type = s.attrib['resourceIdentifier']

                node_title = ''
                for s in sub.iterchildren('{*}title'):
                    # TODO: can there be multiple titles?
                    node_title = s.text

                nodes.append({'id':sub_id, 'title':node_title, 'type': node_type})

                for inkomende_links in sub.iterchildren('inkomende-links'):
                    for sub_ref in inkomende_links.iterchildren():
                        links.append(self.get_links_from_incoming(sub_ref, sub_id))
                for uitgaande_links in sub.iterchildren('uitgaande-links'):
                    for sub_ref in uitgaande_links.iterchildren():
                        links.append(self.get_links_from_outgoing(sub_ref, sub_id))
        links_df = pd.DataFrame.from_dict(links)
        nodes_df = pd.DataFrame.from_dict(nodes)
        links_df =  self.merge_links_nodes(links_df, nodes_df)
        self.links_df = links_df
        return self.links_df


class LinkExtractorRDFParser(LinkExtractorParser):

    def __init__(self, auth=None):
        super().__init__(auth)
        self.graph = rdflib.Graph()

    def load_ecli(self, ecli):
        lido_id = "http://linkeddata.overheid.nl/terms/jurisprudentie/id/" + ecli
        url = "http://linkeddata.overheid.nl/service/get-links?id={}".format(lido_id)
        response = requests.get(url,
                                auth=requests.auth.HTTPBasicAuth(
                                self.auth['username'], self.auth['password'] ))
        xml_rdf = response.text

        with StringIO(xml_rdf) as buff:
            self.graph.parse(buff)

    def retrieve_all_references(self):
        """
        Retrieves all references with jurispudentie source
        """

        query = '''
        prefix overheidrl: <http://linkeddata.overheid.nl/terms/>
        prefix dct: <http://purl.org/dc/terms/>
        select ?source_id ?source_identifier ?target_id ?target_identifier ?target_type ?target_title ?link_type
        where {
          ?target_id a ?target_type.
          ?source_id a overheidrl:Jurisprudentie.
          ?source_id dct:identifier ?source_identifier.
          ?target_id dct:identifier ?target_identifier.
          ?link overheidrl:linktNaar ?target_id.
          ?link overheidrl:linktVan ?source_id.
          ?link overheidrl:heeftLinktype ?link_type.
          optional{ ?target_id dct:title ?target_title.}
        }
        '''
        links = self.graph.query(query)
        links_df = pd.DataFrame(list(links),
                                columns=['source_id', 'source_identifier',
                                         'target_id', 'target_identifier',
                                         'target_type', 'target_title',
                                         'link_type'])
        links_df = links_df.astype('str')
        self.links_df = links_df
        return links_df