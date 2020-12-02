import os
import re
import requests
import random
import time
from multiprocessing import Pool
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from fake_useragent import UserAgent


index = "www.yyzw.com"


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


def read_proxy2(filename="ips.txt"):
    with open(filename, "r") as f:
        proxies = []
        for line in f.readlines():
            line = line.strip()
            proxy = {"http": "http://{}".format(line) }
            proxies.append(proxy)
    return proxies


def read_available_proxy(filename="available_ip.txt"):
    with open(filename, "r") as f:
        proxies = []
        for line in f.readlines():
            line = line.strip()
            proxy = {"http": line}
            proxies.append(proxy)
    return proxies


def test_proxy(proxy):
    try:
        res = requests.get("http://www.dioenglish.com/writing/", headers={"User-Agent": UserAgent().random}, proxies=proxy, timeout=3)
    except Exception as e:
        print("fail", e)
    else:
        print(res)
        return proxy


def random_proxy(proxies):
    if not proxies:
        return
    rand_int = random.randint(0, len(proxies) - 1)
    return proxies[rand_int]


def remove_invalid_character(string):
    invalid = "\/:*?\"<>|？“”："
    return re.sub("[%s]+" % invalid, "", string)


def extract_page_list(category_url, proxies):
    res = requests.get(category_url, headers=headers(), proxies=random_proxy(proxies))
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "lxml")
    total_page = soup.find("a", string="末页").get("href")
    total_num = int(total_page.rsplit("_", 1)[-1].split(".")[0])
    print("total_num:", total_num)
    list_num = total_page.split("_", 1)[1].split("_")[0]
    url_list = [urljoin(category_url, "list_{}_{}.html".format(list_num, i))for i in range(1, total_num + 1)]
    # print(url_list)
    params = ((url, proxies) for url in url_list)
    p1 = Pool(16)
    p1.starmap(extract_article_list, params)
    p1.close()
    p1.join()


def extract_article_list(page_url, proxies):
    page_num = page_url.rsplit("_", 1)[-1].split(".")[0]
    print("current page:", page_num)
    res = requests.get(page_url, headers=headers(), proxies=random_proxy(proxies))
    soup = BeautifulSoup(res.text, "lxml")
    tags = soup.find_all("a", class_="title")
    article_urls = [urljoin(page_url, a.get('href')) for a in tags]
    # print(article_urls)
    for url in article_urls:
        if random.random() > 0.7:
            time.sleep(random.random())
        extract_content(url, proxies)


def extract_content(article_url, proxies):
    res = requests.get(article_url, headers=headers(), proxies=random_proxy(proxies))
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "lxml")
    title = soup.find("h1").get_text()
    title = remove_invalid_character(title)
    # 查找中文的正则表达式
    zh_pattern = re.compile(u'[\u4e00-\u9fff]+')
    bodybox = soup.select(".content > p")
    contents = []
    for p in bodybox:
        s = p.get_text().strip()
        if not zh_pattern.search(s):
            s = re.sub("[%s]+" % "、【】；：‘’“”，。《》（）——", "", s)
            contents.append(s)
    content = "\n".join(contents)
    # print(content)
    category = soup.find("div", class_="article-position").find_all("a")[-1].get_text()
    # print(category)
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
    pool = Pool()
    # proxies = read_proxy()
    # proxies = read_available_proxy()
    # proxies = pool.map(test_proxy, proxies)
    # proxies = [p for p in proxies if p is not None]
    proxies = []

    urls = [
        "http://www.yyzw.com/gaozhong/",
        "http://www.yyzw.com/daxue/",
        "http://www.yyzw.com/yuedu/meiwen/",
        "http://www.yyzw.com/yuedu/duanwen/",
        "http://www.yyzw.com/yuedu/wenhua/",
        "http://www.yyzw.com/yanjiang/",
        "http://www.yyzw.com/chuzhong/",
    ]
    for url in urls:
        extract_page_list(url, proxies)


if __name__ == '__main__':
    main()

    proxies = []
    # extract_page_list("http://www.yyzw.com/gaozhong/", proxies)
    # extract_article_list("http://www.yyzw.com/gaozhong/list_3_1.html", proxies)
    # extract_content("http://www.yyzw.com/yuedu/meiwen/3125.html", proxies)
