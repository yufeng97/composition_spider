import os
import requests
import random
import time
import math
from lxml.etree import HTML
from multiprocessing import Pool
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Queue


BASE_URL = "https://www.jiujiuzuowen.com"


def fetch(url):
    """
        Fetch given url page by using requests and return response html text if success
    """
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36'
    cookie = '__mta=210532266.1597856646388.1597856709219.1597857662901.12; uuid_n_v=v1; uuid=F50E50E0E23D11EA9E4093FE693252837CA0C6EB724249F5B2111828D7A1B702; _csrf=985048b5e3059160ef776c933c08512465d19b9070cf587b9c5768f5a4ddc007; _lxsdk_cuid=17407ad819cc8-0e8bad765cfc1b-3323767-384000-17407ad819cc8; _lxsdk=F50E50E0E23D11EA9E4093FE693252837CA0C6EB724249F5B2111828D7A1B702; mojo-uuid=05bca89a7fafaed21a6f70d22cb566ff; mojo-session-id={"id":"42f0a7841796018ad3658f182a68b1b6","time":1597856646270}; Hm_lvt_703e94591e87be68cc8da0da7cbd0be2=1597856646,1597856696,1597856709; __mta=210532266.1597856646388.1597856707790.1597856709219.11; mojo-trace-id=16; Hm_lpvt_703e94591e87be68cc8da0da7cbd0be2=1597857662; _lxsdk_s=17407ad819d-908-03e-960%7C%7C29'
    headers = {'user-agent': user_agent, 'cookie': cookie}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res
        print("status code:", res.status_code)
    except requests.RequestException as e:
        raise e


def parse_index(url):
    response = fetch(url)
    selector = HTML(response.text)
    # categories = selector.xpath('//div[@class="fenlei2"]//a/text()')
    href = selector.xpath('//div[@class="fenlei2"]//a/@href')
    # urls = (urljoin(BASE_URL, url) for url in href)
    for url in href:
        yield urljoin(BASE_URL, url)
    # for category, url in zip(categories, urls):
    #     print(category, url)
    # # print(categories)
    # # print(urls)
    # return categories, urls


def parse_pages(url):
    response = fetch(url)
    selector = HTML(response.text)
    navbox = selector.xpath('//div[@class="item-t mbx-nav"]')[0]
    # nav box like:
    # 当前位置：九九作文网 > 动物作文 > 共848篇
    total_num = navbox.xpath('string(.)').split(">")[-1][2:-1]
    total_pages = math.ceil(int(total_num) / 30)
    first = url.rsplit('.', 1)[0]
    for i in range(1, total_pages + 1):
        url_page = "{}/{}.html".format(first, i)
        yield url_page


def parse_article_list(url):
    response = fetch(url)
    selector = HTML(response.text)
    href = selector.xpath('//h3/a/@href')
    for url in href:
        yield urljoin(BASE_URL, url)
    # urls = (urljoin(BASE_URL, url) for url in href)
    # return urls

def parse_article(url):
    response = fetch(url)
    selector = HTML(response.text)
    category = selector.xpath('//a[2]/@title')[0]
    title = selector.xpath('//h1/text()')[0]
    author = selector.xpath('//div[@class="meta"]/a/text()')[0]
    contents = selector.xpath('//div[@class="content"]//p/text()')
    content = '\n'.join(contents)
    # save(category, title, content, author)


def save(category, filename, context, author=None):
    if not context:
        return
    dir_path = os.path.join("outputs", BASE_URL, category)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    filepath = os.path.join(dir_path, filename + ".txt")
    with open(filepath, "w", encoding="utf-8") as f:
        if author:
            f.write("作者： {}\n".format(author))
        f.write(context)
    print("{} saved".format(filepath))


def main():
    # pool = Pool()
    # proxies = read_proxy("host.txt")
    # proxies = pool.map(test_proxy, proxies)
    # proxies = [p for p in proxies if p is not None]
    # urls = [
    #     # "https://www.jiujiuzuowen.com/category/gaoyizuowen.html",
    #     # "https://www.jiujiuzuowen.com/category/gaoerzuowen.html",
    #     # "https://www.jiujiuzuowen.com/category/gaosanzuowen.html",
    #     # "https://www.jiujiuzuowen.com/category/gaokaozuowen.html"
    #     # "https://www.jiujiuzuowen.com/category/zuowenfanwen.html",
    #     # "https://www.jiujiuzuowen.com/category/shuqingzuowen.html",
    #     # "https://www.jiujiuzuowen.com/category/xierenzuowen.html",
    #     # "https://www.jiujiuzuowen.com/category/huatizuowen.html",
    #     # "https://www.jiujiuzuowen.com/category/jixuwen.html",
    #     # "https://www.jiujiuzuowen.com/category/yilunwen.html",
    #     "https://www.jiujiuzuowen.com/category/shuomingwen.html",
    # ]
    #
    # for url in urls:
    #     extract_page_list(url, proxies)
    # parse_index(BASE_URL)
    # parse_article('https://www.jiujiuzuowen.com/XiaoJiShiZongJiZuoWen500Zi.html')
    for url_page in parse_pages("https://www.jiujiuzuowen.com/category/dongwuzuowen.html"):
        for url_article in parse_article_list(url_page):
            # parse_article(url_article)
            pass
    # with ThreadPoolExecutor(8) as executor:
    #     pass


if __name__ == '__main__':
    main()
