import requests
import bs4
import re
import os
import random
import time
import re
from urllib import parse
from bs4 import BeautifulSoup as soup
import socket
import string
import threading
import pyhera
import subprocess

h = pyhera.Pool("proxies.db") # Github.com/lstil/pyhera

def token(l):
    return ''.join(random.choice( \
    string.ascii_lowercase) for x in range(l))


class crawler(object):
    def __init__(self):
        self.alive = True
        self.lastmsg_id = None
        self.sent  = []
        self.active = []

        # Channels to scrape data from : @channel1 @channel2 ...
        self.source = [ 'channel1', 'channel2' ]
        self.core()


    def core(self):
        temp = []
        funcs = [self.pinger,
                 self.pool,
                   ]


        for func in funcs:
            self.active.append(func)

            t = threading.Thread(target=func)
            temp.append(t)
            t.start()

        for _t in temp:
            _t.join()


    def pinger(self, host=None):
        if host != None:
            if host == 'bad':
                while len(self.temp) != 0:
                    _host = self.temp.pop()
                    if self.ping(_host):
                        h.ldel('black:proxy', _host)
                        h.ladd('bad:proxy', _host)

                return


            p = h.dret(host)
            if not self.ping(host):

                if h.lexist('proxy', host):
                    print(f'[-] DELETING ' + host)
                    h.ldel('proxy', host)
                    h.ladd('bad:proxy', host)

                elif h.lexist('bad:proxy', host):
                    print(f'[-] BANNING ' + host)
                    h.ldel('bad:proxy', host)
                    h.ladd('black:proxy', host)

            else:
                if h.lexist('bad:proxy', host):
                    print(f'[+] READDING ' + host)
                    h.ldel('bad:proxy', host)
                    h.ladd('proxy', host)

            return

        print('#> PINGER ACTIVATED')
        while self.alive:
            if not self.pinger in self.active:
                self.idle(5)
                continue

            x = random.choice([0] * 4 + [1] * 10)
            if x == 1:
                if h.exist('proxy'):
                    for proxy in h.lret('proxy'):
                        threading.Thread(target=self.pinger, args=[proxy]).start()

            elif x == 0:
                if h.exist('bad:proxy'):
                    for proxy in h.lret('bad:proxy'):
                        threading.Thread(target=self.pinger, args=[proxy]).start()

            else:
                if h.exist('black:proxy'):
                    self.temp = h.lret('black:proxy')
                    for i in range(20):
                        threading.Thread(target=self.pinger, args=['bad']).start()

            self.idle(random.randint(10, 30))


    def pool(self):
        while self.alive:
            if not self.pool in self.active:
                self.idle(5)
                continue

            try:
                for x in self.source:
                    y = self.request(x)
                    for url in self.parser(y):
                        z = self.regex(url)
                        if z == 400:
                            continue

                        if not isinstance(z['server'], list):
                            prx = [z['server']]
                        else:
                            prx = z['server']

                        for proxy in prx:

                            if ':' in proxy:
                                continue

                            if not h.lexist('proxy', proxy) and not h.lexist('bad:proxy', proxy) \
                                and not h.lexist('black:proxy', proxy):
                                print(f'[+] ADDING ' + proxy)
                                h.ladd('proxy', proxy)
                                h.dmls(proxy, {'secret': z['secret'], 'port': z['port'], 'source': x})
            except:
                pass

            print('[!] ' + str(h.llen('proxy')) + " ACTIVE PROXIES" )
            self.idle(random.randint(10, 20))

        return


    def request(self, channel, proxy=False):
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        if proxy:
            p = {'http': '127.0.0.1:9910', 'https': '127.0.0.1:9910'} # Givin tor a try!
            c = requests.get(f"https://t.me/s/{channel}", proxies=p, headers=headers).text
        else:
            c = requests.get(f"https://t.me/s/{channel}", headers=headers).text

        return c


    def parser(self, content):
        resoup, res = soup(content,'html.parser'), []
        for x in resoup.find_all('div', class_ = 'tgme_widget_message_wrap js-widget_message_wrap'):
            i = x.find_all('a')
            for z in i:
                if 'server=' in z['href']:
                    res.append(z['href'])

        return res


    def post_grabber(self, content, channel):
        resoup, res = soup(content,'html.parser'), []
        for x in resoup.find_all('div', class_ = 'tgme_widget_message_wrap js-widget_message_wrap'):

            if x.find('i', class_ = 'tgme_widget_message_video_thumb') != None:
                continue

            if x.find('a', class_ = 'tgme_widget_message_photo_wrap') != None:
                continue

            if x.find('a', class_ = 'tgme_widget_message_document_wrap') != None:
                continue

            y = x.find('div', class_ = 'tgme_widget_message_text js-message_text')
            if y != None:
                if not channel in y.text.lower():
                    if '@' in y.text or 'http' in y.text.lower() or 't.me' in y.text.lower():
                        continue

                z = y.get_text(separator=" ").strip()
                for p in [f'@{channel}', f't.me/{channel}']:
                    z = z.lower().replace(p, '')

                if 10 < len(z):
                    res.append(z)

            else:
                continue

        return res


    def idle(self, sec):
        time.sleep(sec)
        return


    def regex(self, url):
        url, res = url.lower(), {}
        if 'tg://' in url:
            url = url.replace('tg://', 'https://t.me/')

        for i in ['server', 'port', 'secret']:
            x = parse.parse_qs(parse.urlparse(url).query)[i][0]
            if i == 'server':
                if x.endswith('.'):
                    x = x[:-1]

                try:
                    v = x.replace('.', '')
                    v = int(v)
                except:
                    try:
                        z = socket.gethostbyname(x)
                        y = re.findall('Address: (.*)', os.popen(f'nslookup {x}').read())
                        if len(y) > 1:
                            x = y
                        else:
                            x = [z]
                    except:
                        return 400

            res[i] = x

        return res


    def ping(self, host):
        proc = subprocess.Popen(
            ['ping', '-c', '1', host],
            stdout=subprocess.PIPE)

        stdout, stderr = proc.communicate()
        if proc.returncode == 0:
            return True
        else:
            return False


if __name__ == "__main__":
    obj = crawler()
