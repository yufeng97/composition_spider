import os
import re
import requests
import random
import time
from multiprocessing import Pool
from bs4 import BeautifulSoup, NavigableString, Tag
from urllib.parse import urljoin
from fake_useragent import UserAgent


ua = UserAgent()
not_include_category = {"一年级", "二年级", "三年级", "四年级", "五年级", "六年级",
                        "初一", "初二", "初三", "50字", "100字", "150字", "200字",
                        "250字", "300字", "350字", "400字", "450字", }


def read_proxy(filename="host.txt"):
    with open(filename, "r") as f:
        proxies = []
        for line in f.readlines():
            address, port = line.strip().split()
            proxy = {"http": "http://{}:{}".format(address, port)}
            proxies.append(proxy)
    return proxies


def test_proxy(proxy):
    try:
        res = requests.get("https://www.baidu.com", headers={"User-Agent": ua.random}, proxies=proxy, timeout=3)
        return proxy
    except Exception as e:
        print("fail", e)


def get_available_proxy(proxies):
    rand_int = random.randint(0, len(proxies) - 1)
    return proxies[rand_int]


def headers():
    header = {
        "User-Agent": ua.random,
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.9 ",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    return header


def extract_article_list(article_list_url, container, proxies):
    """
    Extract all the article urls from an article list url
    and add it into given container
    :param article_list_url:
    :param container: list
    :param proxies:
    :return:
    """
    res = requests.get(article_list_url, headers=headers(), proxies=get_available_proxy(proxies))
    soup = BeautifulSoup(res.text, 'lxml')
    tag_list = []
    if soup.find("div", class_="article"):
        tag_list = soup.select("div.article > ul a:not(.listtype)")
    elif soup.find("div", class_="zuowenbox"):
        tag_list = soup.select("div.zuowenbox a")
    s = set()
    for i in tag_list:
        added_url = i['href']
        if i['href'][:4] != "http":
            added_url = urljoin(article_list_url, i['href'])
        if ".html" not in added_url:
            continue
        s.add(added_url)
    container.extend(s)


def save(category, filename, text):
    if not os.path.exists("./outputs"):
        os.mkdir("./outputs")
    dir_path = os.path.join("./output", category)
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    filepath = os.path.join(dir_path, filename + ".txt")
    with open(filepath, "w") as f:
        f.write(text)
    print("{} saved".format(filepath))


def extract_page_url(subcategory_url, container, proxies):
    """
    Extract page address from the subcategory
    :param subcategory_url:
    :param container:
    :param proxies:
    :return:
    """
    res = requests.get(subcategory_url, headers=headers(), proxies=get_available_proxy(proxies))
    soup = BeautifulSoup(res.text, 'lxml')
    last_page = soup.find("a", string="末页")
    print("last page:", last_page)
    if last_page:
        relavent_addr = last_page['href']
        # find the last page's index
        last_index = int(re.split("[_.-]", relavent_addr)[-2])
        if '-' in last_page['href']:
            delimiter = '-'
        else:
            delimiter = '_'
        # left part of relevant address
        left = relavent_addr.rsplit(delimiter, 1)[0]
        print("last_index:", last_index)
        for i in range(1, last_index + 1):
            revalent = "{}{}{}{}".format(left, delimiter, i, ".html")
            final_url = urljoin(subcategory_url, revalent)
            if random.random() > 0.5 and i % 3:
                time.sleep(random.random())
            extract_article_list(final_url, container, proxies)
    else:
        extract_article_list(subcategory_url, container, proxies)
    return


def extract_categories(index_url, proxies):
    """
    Extract all the categories from index page
    :param index_url: index url
    :param proxies:
    :return:
    """
    res = requests.get(index_url, headers=headers(), proxies=get_available_proxy(proxies))
    print(res.encoding)  # 查看网页返回的字符集类型
    print(res.apparent_encoding)  # 自动判断字符集类型
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'lxml')
    navibox = soup.find("div", class_="swiper-slide")
    categories = {}
    for child in navibox.children:
        try:
            category = child.find("dt").string
            subcategory = child.find_all("a")
            for i in subcategory:
                if i.string not in not_include_category:
                    categories[category + "-" + i.string] = (urljoin(index, i['href']))
        except Exception:
            pass

    return categories


def get_content(article_url, proxies):
    """
    Extract article from article url
    :param article_url: article url
    :param proxies:
    :return:
    """
    res = requests.get(article_url, headers=headers(), proxies=get_available_proxy(proxies))
    soup = BeautifulSoup(res.text, "lxml")
    header = soup.find('h1').string
    if any(x in header for x in [":", "："]):
        title = re.split("[:：]", header)[-1]
    else:
        title = re.split("_|-", header)[0]
    print("title", title)
    content_tags = soup.select(".content p")
    content = "".join(p.get_text() for p in content_tags)
    return content


def extract_category(name, category_url, proxies):
    """
    提取一个类别中所有的article url
    :param name:
    :param category_url:
    :param proxies:
    :return:
    """
    res = requests.get(category_url)
    soup = BeautifulSoup(res.text, 'lxml')

    article_list = []
    if "考" not in name:
        tag_more = soup.find_all("a", string="更多")
        print(name)
        # 直接提取分页url
        if not tag_more:
            # if category == "节日-父亲节" or category == "节日-母亲节":
            #     print("1111")
            print("直接列表》》》》》")
            extract_page_url(category_url, article_list, proxies)
        else:
            subcategories = {}
            for a in tag_more:
                if a.find_next_sibling("h3"):
                    name = a.find_next_sibling("h3").get_text()
                else:
                    name = a.parent.find_next_sibling("h3").get_text()
                if "英语" in name:
                    continue
                subcategory_url = a['href']
                if subcategory_url[:4] != "http":
                    subcategory_url = urljoin(category_url, subcategory_url)
                subcategories[name] = subcategory_url
            print(subcategories)
            for subcategory_url in subcategories.values():
                time.sleep(random.random())
                extract_page_url(subcategory_url, article_list, proxies)
    else:
        subcategories = {}
        selected = ["满分作文", "作文预测"]
        for item in selected:
            title = name.split('-')[-1] + item
            revalent = soup.find("a", string=title)['href']
            subcategory_url = urljoin(category_url, revalent)
            subcategories[title] = subcategory_url
        print(subcategories)
        for subcategory_url in subcategories.items():
            time.sleep(random.random())
            extract_page_url(subcategory_url, article_list, proxies)
    print(article_list)
    for article_url in article_list:
        if random.random() > 0.5:
            time.sleep(random.random())
        content = get_content(article_list, proxies)
        filename = article_url.rsplit("/", 1)[-1].split(".")[0]
        save(name, filename, content)


def main():
    pass


if __name__ == '__main__':
    # main()

    pool = Pool()
    proxys = read_proxy("host.txt")
    proxys = (pool.map(test_proxy, proxys))
    proxys = [p for p in proxys if p is not None]

    index = "https://www.99zuowen.com/"
    categories = extract_categories(index, proxys)

    pool2 = Pool()
    params = ((category, url, proxys) for (category, url) in categories.items())
    pool2.starmap(extract_category, params)
    # for category, url in categories.items():
    #     extract_category(category, url)
