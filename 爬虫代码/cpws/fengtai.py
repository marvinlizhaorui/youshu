#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2018/7/11 16:13
# Project: 
# @Author: ZQJ
# @Email : zihe@yscredit.com

from pyspider.libs.base_handler import *
import re
from urllib.parse import unquote
from pyquery import PyQuery as pq


class Handler(BaseHandler):
    crawl_config = {
    }

    def __init__(self):
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Cookie': 'PHPSESSID=0gmu2i0rj86b3npovlfo1tkuh6',
            'Host': 'ftqfy.chinacourt.org',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36',
        }

    def reverse_urlDecode_string(self, string_text):
        encoding_text = unquote(string_text)
        html_text = encoding_text.replace('%', '\\').replace(';psbn&', '').encode('utf-8', 'ignore').decode(
            'unicode-escape', 'ignore')
        return html_text[::-1]

    @every(minutes=24 * 60)
    def on_start(self):
        for i in range(1, 137):
            url = 'http://ftqfy.chinacourt.org/public/more.php?p={}&module=Paper&controller=Index&action=Index&LocationID=0800000000&enable=1&audit=1&foreign=0&excellent=0&cat1_id=&cat2_id=1.0000&cat3_id=&reg_time=&casenumber=&title=&content='.format(
                i)
            self.crawl(url, headers=self.headers, save={'type1': '民事文书'}, callback=self.index_page)
        for j in range(1, 19):
            url = 'http://ftqfy.chinacourt.org/public/more.php?p={}&module=Paper&controller=Index&action=Index&LocationID=0800000000&enable=1&audit=1&foreign=0&excellent=0&cat1_id=&cat2_id=2.0000&cat3_id=&reg_time=&casenumber=&title=&content='.format(
                j)
            self.crawl(url, headers=self.headers, save={'type1': '邢事文书'}, callback=self.index_page)

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        type1 = response.save['type1']
        a = response.doc('td.td_line a[href]').items()
        b = response.doc('td.td_time').items()
        time = []
        for each in b:
            print(each.text())
            time.append(each.text())
        titles = []
        url = []
        for each in a:
            href = each.attr['href']
            if len(href) < 100:
                url.append(href)
                title = each.text()
                print(title)
                print(href)
                titles.append(title)
        if len(time) == len(url) == len(titles):
            for i in range(len(time)):
                self.crawl(url[i], headers=self.headers, save={'title': titles[i], 'time': time[i], 'type1': type1},
                           callback=self.detail_page)

    @config(priority=2)
    def detail_page(self, response):
        type1 = response.save['type1']
        time = response.save['time']
        print(time)
        html = response.text
        title = response.save['title']
        patten = re.findall(r'tm\[.*?\]\=\"(.*?)\"', html)
        result = ''
        for x in patten:
            text = self.reverse_urlDecode_string(x)
            result = result + text

        print(result)
        try:
            time_xq = re.compile(r'(二[一二三四五六七八九十年月日月 ΟＯО0Oo○〇?]+)', re.S).findall(result)[-1].replace('?',
                                                                                                      'O')  # 如果有问号的话用大写的o代替
        except:
            time_xq = ''
        print(time_xq)
        try:
            content_type = re.compile('<!--类型 -->(.*?)</td></tr>', re.S).findall(result)[0][:2] + '案件'
            case_type = re.compile('<!--类型 -->(.*?)</td></tr>', re.S).findall(result)[0][-3:]
        except:
            content_type = ''
            case_type = ''
        print(content_type)
        try:
            court_name = re.compile('SIZE="4">(.*?)</FONT>', re.S).findall(result)[0]
        except:
            court_name = ''
        print(court_name)
        try:
            case_no = re.compile('<!--案件号 -->(.*?)</td>', re.S).findall(result)[0]
        except:
            case_no = ''
        print(case_no)
        try:
            publish_date = re.compile(r'0> ([\d-]+.*?)</FONT></DIV>', re.S).findall(result)[0]
        except:
            publish_date = ''
        print(publish_date)
        source = '丰台法院网'
        p = pq(result)
        total = []
        articles_doc = p('div')
        for each in p('div > *').items():
            if each.text:
                a = each.text().replace(' ', '').replace('\u3000', '').replace('\xa0', '').strip().split('\n')
                total = total + a
        b = []
        for x in total:
            if x != '':
                b.append(x)
        print(b)
        articles = str(b)
        yield {
            'title': title,
            'publish_date': time,
            'case_no': case_no,
            'articles': str(articles),
            'html': str(articles_doc),
            'type': case_type,
            'court_name': court_name,
            'content_type': content_type,
            'source': source,
            'org_url': response.url,
            'trial_date': time_xq,
            'trial_round': '',
            'reason': '',
        }