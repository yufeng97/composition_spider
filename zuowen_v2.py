import os
import re
import requests
import random
import time
from multiprocessing import Pool
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from fake_useragent import UserAgent


index = "www.zuowen.com"


def remove_invalid_character(string):
    invalid = "\/:*?\"‘’'<>|？“”："
    return re.sub("[%s]+" % invalid, "", string)


def extract_page_list(category_url, proxies):
    res = requests.get(category_url, headers=headers(), proxies=random_proxy(proxies))
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "lxml")
    pagebar = soup.find("div", class_="artpage")
    total_num = int(pagebar.find_all("a")[-2].get_text())
    print("total_num:", total_num)
    url_list = []
    for i in range(1, total_num + 1):
        if i == 1:
            url = urljoin(category_url, "index.shtml")
        else:
            url = urljoin(category_url, "index_{}.shtml".format(i))
        url_list.append(url)
    # print(url_list)

    # for url in url_list:
    #     extract_article_list(url, proxies)
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
    tags = soup.select(".artbox_l_t a")
    article_urls = [urljoin(page_url, a.get('href')) for a in tags]
    # print(article_urls)
    for url in article_urls:
        if random.random() > 0.7:
            time.sleep(random.random())
        extract_content(url, proxies)


def extract_content(article_url, proxies):
    i = 0
    while i < 3:
        res = requests.get(article_url, headers=headers(), proxies=random_proxy(proxies))
        if res.status_code == 200:
            break
        i += 1
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "lxml")
    title = soup.find("h1").get_text()
    title = remove_invalid_character(title)
    try:
        category = soup.find("div", class_="path").find_all("a")[-1].get_text()
    except Exception as e:
        print(soup.find("div", class_="path"))
        print("wrong", res.status_code)
        print(article_url)
        return
    # print(category)
    # 查找中文的正则表达式
    zh_pattern = re.compile(u'[\u4e00-\u9fff]+')
    bodybox = soup.select(".con_content > p")
    contents = []
    for p in bodybox:
        # 去除p中间的广告
        # temp = BeautifulSoup(str(p), "lxml")
        # if temp.a:
        #     temp.a.decompose()
        # s = temp.p.get_text().strip()
        if p.a:
            p.a.decompose()
        s = p.get_text().strip()
        if not zh_pattern.search(s):
            s = re.sub("[%s]+" % "、【】；：‘’“”，。《》（）——", "", s)
            if s:
                contents.append(s)
    content = "\n".join(contents)
    # print(content)

    save(category, title, content)


def main():
    pool = Pool()
    # proxies = read_proxy()
    # proxies = read_available_proxy()
    # proxies = pool.map(test_proxy, proxies)
    # proxies = [p for p in proxies if p is not None]
    proxies = []

    urls = [
        "http://www.zuowen.com/yingyuzw/gzyingyu/gyyy/",
        "http://www.zuowen.com/yingyuzw/gzyingyu/geyy/",
        "http://www.zuowen.com/yingyuzw/gzyingyu/gsyy/",
        "http://www.zuowen.com/yingyuzw/czyingyu/cyyy/",
        "http://www.zuowen.com/yingyuzw/czyingyu/ceyy/",
        "http://www.zuowen.com/yingyuzw/czyingyu/csyy/",
        "http://www.zuowen.com/yingyuzw/rdyingyu/jieriyy/",
        "http://www.zuowen.com/yingyuzw/rdyingyu/renwuyy/",
        "http://www.zuowen.com/yingyuzw/rdyingyu/shijianyy/",
        "http://www.zuowen.com/yingyuzw/rdyingyu/jijieyy/",
        "http://www.zuowen.com/yingyuzw/rdyingyu/dongwuyy/",
        "http://www.zuowen.com/yingyuzw/rdyingyu/qitayy/",
    ]
    for url in urls:
        extract_page_list(url, proxies)


if __name__ == '__main__':
    main()

    proxies = []
    # extract_page_list("http://www.zuowen.com/yingyuzw/gzyingyu/gyyy/", proxies)
    # extract_article_list('http://www.zuowen.com/yingyuzw/gzyingyu/gyyy/index.shtml', proxies)
    # extract_content('http://www.zuowen.com/e/20200525/5ecbbfa37210b.shtml', proxies)
