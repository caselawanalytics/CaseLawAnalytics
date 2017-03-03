"""
These are names of common law bookds

    Strafrecht (sw of sr),
    Strafvorderingen (sv),
    Burgelijk WB (bwb, 7 boeken 7:658),
    AWB (algemene wet bestuursrecht, meerdere gedeelten)
    evrm = europees verdrag rechten van de mens


"""

import re
import nltk
from collections import Counter

def get_article_regex():
    known_books = ['sw', 'sr', 'sv', 'bwb', 'bw', 'awb', 'evrm', 'ro', 'zfw']
    regex_knownbooks = r"(?:<" + "|".join(known_books) + r">)"

    article_regex = r"<art(?:ikel)?> " + \
                    r"<\.>? " + \
                    r"<[0-9]+(?::[0-9]+)?[a-z]*> " + \
                    r"(?:<,>? <lid> <[0-9]+>)?" + \
                    r"(?:<van> <het|de> <wet>? <.*> | " + \
                    regex_knownbooks + ")"
    return article_regex


def get_articles(text):
    """

    :param text:
    :return:
    """
    if type(text) == str :
        text = nltk.Text(nltk.word_tokenize(text.lower()))
    article_regex = get_article_regex()
    references = nltk.TokenSearcher(text).findall(article_regex)
    articles = []
    for v in references:
        art_number = nltk.TokenSearcher(v).findall("<[0-9]+(?::[0-9]+)?[a-z]*> ")[0][0]
        art_name = v[-1]
        articles.append((art_number, art_name))

    result = {}
    # Aggregate with counter
    for (art_number, art_name), cnt in Counter(articles).most_common():
        result[(art_number, art_name)] = cnt
    return result

def get_ecli_references(text):
    """

    :param text:
    :return:
    """
    ecli_regex =  r'''ECLI:[A-Z]{2}:[A-Z]+:[0-9]{4}:[A-Z0-9]+'''

    references = re.findall(ecli_regex, text)

    result = {}
    # Aggregate with counter
    for ecli, cnt in Counter(references).most_common():
        result[ecli] = cnt
    return result