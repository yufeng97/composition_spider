import os
import re
import requests
import math
from lxml.etree import HTML
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from threading import Thread


BASE_URL = ""
index = "www.yyzw.com"


def fetch(url) -> requests.Response:
    """
        Fetch given url page by using requests and return response html text if success
    """
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36"
    cookie = '__mta=210532266.1597856646388.1597856709219.1597857662901.12; uuid_n_v=v1; uuid=F50E50E0E23D11EA9E4093FE693252837CA0C6EB724249F5B2111828D7A1B702; _csrf=985048b5e3059160ef776c933c08512465d19b9070cf587b9c5768f5a4ddc007; _lxsdk_cuid=17407ad819cc8-0e8bad765cfc1b-3323767-384000-17407ad819cc8; _lxsdk=F50E50E0E23D11EA9E4093FE693252837CA0C6EB724249F5B2111828D7A1B702; mojo-uuid=05bca89a7fafaed21a6f70d22cb566ff; mojo-session-id={"id":"42f0a7841796018ad3658f182a68b1b6","time":1597856646270}; Hm_lvt_703e94591e87be68cc8da0da7cbd0be2=1597856646,1597856696,1597856709; __mta=210532266.1597856646388.1597856707790.1597856709219.11; mojo-trace-id=16; Hm_lpvt_703e94591e87be68cc8da0da7cbd0be2=1597857662; _lxsdk_s=17407ad819d-908-03e-960%7C%7C29'
    headers = {'user-agent': user_agent, 'cookie': cookie}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            res.encoding = res.apparent_encoding
            return res
        print("status code:", res.status_code)
    except requests.RequestException as e:
        raise e


def parse_index(url):
    """
            alternative xpath: //h3[@class="title fw3"]/a
        """
    response = fetch(url)
    selector = HTML(response.text)
    category_tags = selector.xpath('//div[@id="subnav"]/ul/li/a/@href')
    category_urls = [urljoin(BASE_URL, url) for url in category_tags]
    return category_urls


def parse_category(url):
    response = fetch(url)
    selector = HTML(response.text)
    "http://www.yyzw.com/chuzhong/chuyi/list_20_1.html"
    last_page = selector.xpath('//ul[@class="pagelist"]/li[position()=last()-1]/a/@href')[0]
    list_num, total_page = last_page.rsplit("_", 1)
    total_num = int(total_page.split(".")[0])
    return [urljoin(url, f"list_") for i in range(1, total_num + 1)]


def parse_page(url):
    response = fetch(url)
    selector = HTML(response.text)
    href = selector.xpath('//div[@class="list-article list-short"]/ul/li/a/@href')
    return [urljoin(BASE_URL, url) for url in href]


def parse_article(url):
    response = fetch(url)
    selector = HTML(response.text)
    # http://www.yyzw.com/zuowen/4117.html
    article_id = url.rsplit("/", 1)[-1].split(".")[0]
    title = selector.xpath("//h1/text()")[0]
    category = selector.xpath('//div[@class="article-position"]/a[position()=last()-1]/text()')[0]
    bodybox = selector.xpath('//div[@class="content"]')[0]
    content = "\n".join(s for s in bodybox.xpath("./p/text()"))
    print(content)
    save(category, article_id, content, title)


def remove_invalid_character(string):
    invalid = "\/:*?\"<>|？“”："
    return re.sub("[%s]+" % invalid, "", string)


def save(category, filename, context, title=None, author=None):
    if not context:
        return
    dir_path = os.path.join("outputs", index, category)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    filepath = os.path.join(dir_path, filename + ".txt")
    with open(filepath, "w", encoding="utf-8") as f:
        if title:
            f.write(f'{title}/n')
        if author:
            f.write(f"作者： {author}\n")
        f.write(context)
    print(f"{filepath} saved")


def main():
    parse_article("http://www.yyzw.com/zuowen/4116.html")


if __name__ == '__main__':
    main()
