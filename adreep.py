import os
import re
import requests
import random
import time
from multiprocessing import Pool
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from fake_useragent import UserAgent


index = "www.adreep.cn"


def headers():
    header = {
        "User-Agent": UserAgent().random,
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.9 ",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "close",
    }
    return header


def read_proxy(filename="host.txt"):
    with open(filename, "r") as f:
        proxies = []
        for line in f.readlines():
            address, port, type_ = line.strip().split()
            proxy = {"http": "http://{}:{}".format(address, port)}
            proxies.append(proxy)
    return proxies


def test_proxy(proxy):
    try:
        res = requests.get("https://www.adreep.cn/", headers={"User-Agent": UserAgent().random}, proxies=proxy, timeout=3)
        return proxy
    except Exception as e:
        print("fail", e)


def random_proxy(proxies):
    if not proxies:
        return
    rand_int = random.randint(0, len(proxies) - 1)
    return proxies[rand_int]


def remove_invalid_character(string):
    invalid = r"\/:*?\"<>|？“”："
    return re.sub("[%s]+" % invalid, "", string)


def extract_page_list(category_url, proxies):
    res = requests.get(category_url, headers=headers(), proxies=random_proxy(proxies))
    soup = BeautifulSoup(res.text, "lxml")
    total_page = soup.find("a", string="末页").get("href")
    total_num = int(total_page.rsplit("=", 1)[-1])
    print("total_num:", total_num)

    # page_urls = [urljoin(category_url, "?page={}".format(i)) for i in range(1, total_num + 1)]
    # print(page_urls)

    params = ((urljoin(category_url, "?page={}".format(i)), proxies) for i in range(1, total_num + 1))
    p1 = Pool(16)
    p1.starmap_async(extract_article_list, params)
    p1.close()
    p1.join()


def extract_article_list(page_url, proxies):
    page_num = page_url.rsplit("=", 1)[-1]
    print("current page:", page_num)
    try:
        res = requests.get(page_url, headers=headers(), proxies=random_proxy(proxies))
    except Exception as e:
        print(e)
        raise e
    soup = BeautifulSoup(res.text, "lxml")
    tags = soup.select("h4 a")
    article_urls = [urljoin(page_url, a.get('href')) for a in tags]
    # print(article_urls)
    for url in article_urls:
        if random.random() > 0.5:
            time.sleep(random.random())
        extract_content(url, proxies)


def extract_content(article_url, proxies):
    res = requests.get(article_url, headers=headers(), proxies=random_proxy(proxies))
    soup = BeautifulSoup(res.text, "lxml")
    title = soup.find("h1").get_text()
    title = remove_invalid_character(title)
    try:
        category = soup.select(".breadcrumb a")[-1].get_text()
    except Exception as e:
        print("wrong", res.status_code)
        print(article_url)
        return

    # 查找中文的正则表达式
    zh_pattern = re.compile(u'[\u4e00-\u9fff]+')

    bodybox = soup.find("div", id="bodybox")
    contents = []
    for p in bodybox.strings:
        s = p.strip()
        if not zh_pattern.search(s):
            s = re.sub("[%s]+" % "、【】；：‘’“”，。《》（）——", "", s)
            if s:
                contents.append(s)
    content = "\n".join(contents)
    save(category, title, content)


def save(category, filename, context):
    if not context:
        return
    dir_path = os.path.join("outputs", index, category)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    filepath = os.path.join(dir_path, filename + ".txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(context)
    print("{} saved".format(filepath))


def main():
    # pool = Pool()
    # proxies = read_proxy("host.txt")
    # proxies = pool.map(test_proxy, proxies)
    # proxies = [p for p in proxies if p is not None]
    proxies = []
    urls = [
        "https://www.adreep.cn/dxyy/",
        "https://www.adreep.cn/gz/",
        "https://www.adreep.cn/cz/",
        "https://www.adreep.cn/fw/",
    ]
    for url in urls:
        extract_page_list(url, proxies)


if __name__ == '__main__':
    main()
    proxies = []

    # extract_page_list("https://www.adreep.cn/dxyy/", proxies)
    # extract_article_list("https://www.adreep.cn/dxyy/?page=377", proxies)
    # extract_content("https://www.adreep.cn/dxyy/57003.html", proxies)
