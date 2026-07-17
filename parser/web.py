import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import random
import time
from requests.exceptions import ProxyError as ProxyError
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import cfscrape

scraper = cfscrape.CloudflareScraper()

ua = UserAgent()


def try_repeat(func):
    def wrapper(*args, **kwargs):
        for i in range(0, 10):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print('\nОшибка:', e)
                time_sleep = random.randint(11, 21) / 10
                print(f'Ждем после ошибки {time_sleep} секунд.')
                time.sleep(time_sleep)
        raise RuntimeError(f'Exception is:{e}')

    return wrapper


class Proxy:
    def __init__(self, proxy):
        self.proxy = proxy
        self.is_bad = False

    def __bool__(self):
        if self.proxy is None:
            return False
        return True
    def __repr__(self):
        return self.proxy

    def __str__(self):
        return self.proxy

    def as_dict(self):
        return str_to_proxy_dict(self.proxy)

    @staticmethod
    def all_proxies_bad(proxies):
        for proxy in proxies:
            if not proxy.is_bad:
                return False
        return True

    def reset_proxy_status(self):
        self.is_bad = False

    @staticmethod
    def reset_proxies(proxies):
        for proxy in proxies:
            proxy.reset_proxy_status()


def get_proxy_list(uptime=40, local=False, use_your_ip=False, path = None, **kwargs):
    if local:
        if path is None:
            with open('../data/proxies.html') as f:
                bs = BeautifulSoup(f.read())
        else:
            with open(path) as f:
                bs = BeautifulSoup(f.read())
    else:
        bs = BeautifulSoup(html_code(f'http://www.freeproxylists.net/ru/?u={uptime}&s=rs', **kwargs))
    proxy_table = bs.find('table', class_='DataGrid').find_all('tr')
    proxies = [Proxy(f"{row.findAll('td')[2].text.lower()}://{row.findAll('td')[0].text}:{row.findAll('td')[1].text}")
               for
               row in proxy_table[1:] if len(row.findAll('td')) > 1]
    if use_your_ip:
        proxies.insert(0, Proxy(None))
    return proxies


def str_to_proxy_dict(proxy):
    if not proxy:
        return None
    proxy_list = str(proxy).split("://")
    return {proxy_list[0]: str(proxy)}


class Response:
    def __init__(self, response, status_code=200, proxy_error=False):
        self.response = response
        self.status_code = status_code
        self.proxy_error = proxy_error

    def __repr__(self):
        return self.response

    def __str__(self):
        return self.response


def get_request(url, json=False, proxy=None, headers=None, cookies=None, **kwargs):
    if headers is None:
        headers = {'User-Agent': ua.random}
    proxy = str_to_proxy_dict(proxy) if proxy is not None else None
    try:
        response = requests.get(url, headers=headers, proxies=proxy, cookies=cookies)
    except requests.exceptions.ProxyError:
        raise ProxyError
    if response.status_code == requests.codes['ok']:
        return response.text if not json else response.json()
    elif response.status_code == requests.codes['not_found']:
        return response.text if not json else response.json()
    elif response.status_code == requests.codes['too_many']:
        raise Exception("Too many requests")
    else:
        raise Exception(f"Exception on error code {response.status_code}")


def class_to_css_selector(class_name):
    return '.' + '.'.join(class_name.split())


def get_request_js(url, loaded_element_class=None, proxy=None, **kwargs):
    if proxy is not None:
        webdriver.DesiredCapabilities.CHROME['proxy'] = {
            "httpProxy": proxy,
            "ftpProxy": proxy,
            "sslProxy": proxy,
            "proxyType": "MANUAL",

        }
    with webdriver.Chrome() as driver:
        driver.get(url)
        if loaded_element_class is not None:
            WebDriverWait(driver, 10).until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, class_to_css_selector(loaded_element_class))))
        # return driver.find_element_by_css_selector(class_to_css_selector(loaded_element_class)).get_attribute(
        #     'innerHTML')
        return driver.page_source


def html_code(url, js=False, **kwargs):
    if not js:
        return get_request(url, **kwargs)
    else:
        return get_request_js(url, **kwargs)


def proxy_loop(address, proxies, additional_proxy_checker_func=None, **kwargs):
    if Proxy.all_proxies_bad(proxies):
        Proxy.reset_proxies(proxies)
    for proxy in proxies:
        if not proxy.is_bad:
            try:
                code = html_code(address, proxy=proxy, **kwargs)
            except ProxyError:
                proxy.is_bad = True
                return proxy_loop(address, proxies, additional_proxy_checker_func=additional_proxy_checker_func,
                                  **kwargs)
            if code is not None:
                break
    if additional_proxy_checker_func is not None and additional_proxy_checker_func(code) is True:
        proxy.is_bad = True
        return proxy_loop(address, proxies, additional_proxy_checker_func=additional_proxy_checker_func, **kwargs)
    else:
        return code
