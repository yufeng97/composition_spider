import os
import re
import requests
import math
from lxml.etree import HTML
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from threading import Thread


CRAWL_PAGE_THREADINGS = 4
PARSE_PAGE_THREADINGS = 4
CRAWL_ARTICLE_THREADINGS = 8
PARSE_ARTICLE_THREADINGS = 8
BASE_URL = "http://www.dioenglish.com/writing/"
index = "www.dioenglish.com"


class CrawlPageThread(Thread):
    Finished = False

    def __init__(self, thread_id, queue: Queue, page_data_queue: Queue):
        super().__init__()
        self.thread_id = thread_id
        self.queue = queue
        self.data_queue = page_data_queue

    def run(self) -> None:
        print(f'启动线程：{self.thread_id}')
        self.scheduler()
        print(f'结束线程：{self.thread_id}')

    def scheduler(self):
        while True:
            if self.queue.empty():
                CrawlPageThread.Finished = True
                break
            else:
                page = self.queue.get()
                print(f'下载线程为： {self.thread_id} 下载Page页面： {page}')
                try:
                    response = fetch(page)
                    self.data_queue.put(response)
                except Exception as e:
                    print('下载出现异常', e)
                    handle_exception("page", page)
                    self.queue.put(page)


class ParsePageThread(Thread):
    Finished = False

    def __init__(self, thread_id, data_queue: Queue, article_queue: Queue):
        super().__init__()
        self.thread_id = thread_id
        self.queue = data_queue
        self.article_queue = article_queue

    def run(self) -> None:
        print(f'启动线程：{self.thread_id}')
        while not CrawlPageThread.Finished:
            try:
                item = self.queue.get()
                if not item:
                    continue
                print("解析Page页面：", item.url)
                self.parse(item)
                self.queue.task_done()
            except Exception as e:
                pass
        print(f'结束线程：{self.thread_id}')

    def parse(self, item):
        selector = HTML(item.text)
        href = selector.xpath("//dt/a/@href")
        for url in href:
            self.article_queue.put(urljoin(BASE_URL, url))


class CrawlArticleThread(Thread):
    Finished = False

    def __init__(self, thread_id, queue: Queue, article_data_queue: Queue):
        super().__init__()
        self.thread_id = thread_id
        self.queue = queue
        self.data_queue = article_data_queue

    def run(self) -> None:
        print(f'启动线程：{self.thread_id}')
        self.scheduler()
        print(f'结束线程：{self.thread_id}')

    def scheduler(self):
        while True:
            if ParsePageThread.Finished and self.queue.empty():
                CrawlArticleThread.Finished = True
                break
            else:
                article = self.queue.get()
                print(f'下载线程为： {self.thread_id} 下载Article页面： {article}')
                try:
                    response = fetch(article)
                    self.data_queue.put(response)
                except Exception as e:
                    print('下载出现异常', e)
                    handle_exception("article", article)
                    self.queue.put(article)


class ParseArticleThread(Thread):
    def __init__(self, thread_id, data_queue: Queue):
        super().__init__()
        self.thread_id = thread_id
        self.queue = data_queue

    def run(self) -> None:
        print(f'启动线程：{self.thread_id}')
        while not CrawlArticleThread.Finished:
            try:
                item = self.queue.get()
                if not item:
                    continue
                print(f'解析Article页面： {item.url}')
                self.parse(item)
                self.queue.task_done()
            except Exception as e:
                pass
        print(f'结束线程：{self.thread_id}')

    def parse(self, item):
        url = item.url
        selector = HTML(item.text)
        # http://www.dioenglish.com/writing/daxue/103021.html
        article_id = url.rsplit("/", 1)[-1].split(".")[0]
        title = selector.xpath("//h1/text()")[0]
        category = selector.xpath('////div[@class="breadcrumb container"]/a[position()=2]/text()')[0]
        bodybox = selector.xpath('//div[@class="article_content"]')[0]
        content = bodybox.xpath("string(.)").strip()
        save(category, article_id, content, title)



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
            return res
        print("status code:", res.status_code)
    except requests.RequestException as e:
        raise e


def parse_index(url):
    response = fetch(url)
    selector = HTML(response.text)
    category_tags = selector.xpath('//div[@class="fnav"]/a[position()<last()-3]/@href')
    category_urls = [urljoin(BASE_URL, url) for url in category_tags]
    return category_urls


def parse_category(url):
    """parse category url and extract page url"""
    response = fetch(url)
    selector = HTML(response.text)
    last_page = selector.xpath('//div[@class="pagebar"]/a[position()=last()]/@href')[0]
    # http://www.dioenglish.com/writing/daxue/index_101.html
    total_num = int(last_page.rsplit("_", 1)[-1].split(".")[0])
    page_list = []
    for i in range(1, total_num + 1):
        if i == 1:
            new_url = urljoin(url, "index.html")
        else:
            new_url = urljoin(url, f"index_{i}.html")
        page_list.append(new_url)
    return page_list


def parse_page(url):
    response = fetch(url)
    selector = HTML(response.text)
    href = selector.xpath("//dt/a/@href")
    return [urljoin(BASE_URL, url) for url in href]


def parse_article(url):
    response = fetch(url)
    selector = HTML(response.text)
    # http://www.dioenglish.com/writing/daxue/103021.html
    article_id = url.rsplit("/", 1)[-1].split(".")[0]
    title = selector.xpath("//h1/text()")[0]
    category = selector.xpath('////div[@class="breadcrumb container"]/a[position()=2]/text()')[0]
    bodybox = selector.xpath('//div[@class="article_content"]')[0]
    content = bodybox.xpath("string(.)").strip()
    save(category, article_id, content, title)


def remove_win_invalid_char(string):
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


def handle_exception(type_, url):
    if type_ == "page":
        with open("./failed_page.txt", "a") as f:
            f.writelines(f"{url}\n")
    elif type_ == "article":
        with open("./failed_url.txt", "a") as f:
            f.writelines(f"{url}\n")


def initialize_failure_log():
    f1 = open("./failed_page.txt", "w")
    f1.close()
    f2 = open("./failed_url.txt", "w")
    f2.close()


def main():
    category_urls = [url for url in parse_index(BASE_URL)]
    # category_urls = ['https://www.jiujiuzuowen.com/category/yanjianggao.html',
    #                  'https://www.jiujiuzuowen.com/category/sanwen.html']

    page_queue = Queue()
    page_data_queue = Queue()
    article_queue = Queue()
    article_data_queue = Queue()

    with ThreadPoolExecutor(8) as executor:
        futures = []
        for category in category_urls:
            futures.append(executor.submit(parse_category, category))
        for future in as_completed(futures):
            try:
                for url in future.result():
                    page_queue.put(url)
            except Exception as e:
                print(e)

    print(page_queue.qsize())

    initialize_failure_log()

    crawls_page_threads = []
    crawls_page_names = [f'crawl_page_{i}' for i in range(1, CRAWL_PAGE_THREADINGS + 1)]
    for thread_id in crawls_page_names:
        thread = CrawlPageThread(thread_id, page_queue, page_data_queue)
        thread.start()
        crawls_page_threads.append(thread)

    parse_page_threads = []
    parse_page_names = [f'parse_page_{i}' for i in range(1, PARSE_PAGE_THREADINGS + 1)]
    for thread_id in parse_page_names:
        thread = ParsePageThread(thread_id, page_data_queue, article_queue)
        thread.start()
        parse_page_threads.append(thread)

    crawls_article_threads = []
    crawls_article_names = [f'crawl_article_{i}' for i in range(1, CRAWL_ARTICLE_THREADINGS + 1)]
    for thread_id in crawls_article_names:
        thread = CrawlArticleThread(thread_id, article_queue, article_data_queue)
        thread.start()
        crawls_article_threads.append(thread)

    parse_article_threads = []
    parse_article_names = [f'parse_article_{i}' for i in range(1, PARSE_ARTICLE_THREADINGS + 1)]
    for thread_id in parse_article_names:
        thread = ParseArticleThread(thread_id, article_data_queue)
        thread.start()
        parse_article_threads.append(thread)

    # 结束crawl线程
    for t in crawls_page_threads:
        t.join()
    CrawlPageThread.Finished = True

    # 结束parse线程
    for t in parse_page_threads:
        t.join()
    ParsePageThread.Finished = True

    for t in crawls_article_threads:
        t.join()
    CrawlArticleThread.Finished = True

    for t in parse_article_threads:
        t.join()


if __name__ == '__main__':
    main()
