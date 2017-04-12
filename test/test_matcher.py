from caselawnet import matcher

def test_get_articles_empty():
    text = ''
    articles = matcher.get_articles(text)
    assert len(articles) == 0

def test_get_articles():
    text = 'art. 1:23 BWB'
    articles = matcher.get_articles(text)
    assert len(articles) == 1
    assert ('1:23', 'bwb') in articles