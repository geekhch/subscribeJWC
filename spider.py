import requests,redis
from lxml import etree

MAIL = ['709531006@qq.com']
JWC = 'http://jwc.scu.edu.cn/'
R = redis.Redis('localhost')

def GET(url):
    """GET请求"""
    response = requests.get(url)
    return response.content.decode('utf-8')

def parse(html):
    selector = etree.HTML(html)
    data = selector.xpath('//ul[@class="list-llb-s"]/li')
    for e in data:
        article = {
            'title': e.xpath('./@title'),
            'li': e.xpath('./a/@href'),
            'date': e.xpath('./a/em/text()')
        }
        yield article

def downArticle(url):
    html = GET(url)
    

def newArticle(generator):
    already = R.get('article')
    for e in generator:
        if not e['title'] in already:
            

if __name__ == "__main__":
    index = GET(JWC)
    arts = parse(index)
    for e in arts:
        print(e)
