from caselawnet import matcher

def test_get_articles_empty():
    text = ''
    articles = matcher.get_articles(text)
    assert len(articles) == 0

def test_get_articles_1():
    text = 'art. 7:658 BW'
    articles = matcher.get_articles(text)
    assert len(articles) == 1
    assert ('7:658', 'bw') in articles

def test_get_articles_2():
    text = 'Artikel 10:11 Awb'
    articles = matcher.get_articles(text)
    assert len(articles) == 1
    assert ('10:11', 'awb') in articles