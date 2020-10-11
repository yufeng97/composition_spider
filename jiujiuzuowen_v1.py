import os
import re
import requests
import random
import time
from multiprocessing import Pool
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from fake_useragent import UserAgent


index = "https://www.jiujiuzuowen.com"


def headers():
    header = {
        "User-Agent": UserAgent().random,
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.9 ",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    return header


def extract_page_list(category_url: str):
    res = requests.get(category_url, headers=headers(),)
    soup = BeautifulSoup(res.text, "lxml")
    total_num = soup.find("div", class_="item-t mbx-nav").get_text()
    # Extract total num and trim space
    total_num = total_num.strip().rsplit(">")[-1].strip()
    total_num = int(total_num[1:-1])
    total_page = total_num // 30
    left = category_url.rsplit(".", 1)[0]
    print("total page:", total_page)

    params = (("{}/{}.html".format(left, i)) for i in range(1, total_page + 1))
    p1 = Pool(16)
    p1.starmap_async(extract_article_list, params)
    p1.close()
    p1.join()

    # for i in range(1, total_page + 1):
    #     if random.random() > 0.5:
    #         time.sleep(random.random())
    #     print("current page:", i)
    #     extract_article_list("{}/{}.html".format(left, i), proxies)


def extract_article_list(page_url: str):
    if random.random() > 0.5:
        time.sleep(random.random())
    res = requests.get(page_url, headers=headers(), )
    soup = BeautifulSoup(res.text, "lxml")
    # Extract page index from url
    page_index = page_url.rsplit("/", 1)[-1].split(".")[0]
    print("current page:", page_index)
    tags = soup.select(".tm_pageList li a")
    article_urls = [a.get('href') for a in tags]

    [extract_content(urljoin(index, url)) for url in article_urls]

    # params = ((urljoin(index, url), proxies) for url in article_urls)
    # p1 = Pool(16)
    # p1.starmap_async(extract_content, params)
    # p1.close()
    # p1.join()


def extract_content(article_url: str):
    if random.random() > 0.5:
        time.sleep(random.random())
    try:
        res = requests.get(article_url, headers=headers(),)
        soup = BeautifulSoup(res.text, "lxml")
        category = soup.find("a", title=True).get_text()
        header = soup.find("h1").get_text()
        content_tags = soup.select(".content p")
        content = "\n".join(p.get_text() for p in content_tags)
        save(category, header, content)
    except Exception:
        return


def save(category, filename, context):
    if not context:
        return
    dir_path = os.path.join("outputs", category)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    filepath = os.path.join(dir_path, filename + ".txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(context)
    print("{} saved".format(filepath))


def main():
    pool = Pool()
    urls = [
        # "https://www.jiujiuzuowen.com/category/gaoyizuowen.html",
        # "https://www.jiujiuzuowen.com/category/gaoerzuowen.html",
        # "https://www.jiujiuzuowen.com/category/gaosanzuowen.html",
        # "https://www.jiujiuzuowen.com/category/gaokaozuowen.html"
        # "https://www.jiujiuzuowen.com/category/zuowenfanwen.html",
        # "https://www.jiujiuzuowen.com/category/shuqingzuowen.html",
        # "https://www.jiujiuzuowen.com/category/xierenzuowen.html",
        # "https://www.jiujiuzuowen.com/category/huatizuowen.html",
        # "https://www.jiujiuzuowen.com/category/jixuwen.html",
        # "https://www.jiujiuzuowen.com/category/yilunwen.html",
        "https://www.jiujiuzuowen.com/category/shuomingwen.html",
    ]

    for url in urls:
        extract_page_list(url)


if __name__ == '__main__':
    main()
