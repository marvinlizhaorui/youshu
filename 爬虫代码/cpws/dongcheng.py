#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2018/7/11 16:05
# Project: 
# @Author: ZQJ
# @Email : zihe@yscredit.com

from pyspider.libs.base_handler import *
import re
from urllib.parse import unquote
from pyquery import PyQuery as pq


# 东城区裁判文书2015年前数据全量


class Handler(BaseHandler):
    crawl_config = {
        'itag': 'beijing_day_6.23',
        'proxy': 'H21WNK49K6PFSR3P:BF2B9DDE973F0C02@http-pro.abuyun.com:9010',
    }

    def __init__(self):
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': 'dcqfy.chinacourt.org',
            'If-Modified-Since': 'Mon, 09 Jul 2018 01:19:09 GMT',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36',
        }

    @every(minutes=24 * 60)
    def on_start(self):
        # 民事文书
        for i in range(1, 40):
            url = 'http://dcqfy.chinacourt.org/paper/more/paper_mid/MzA0gAMA/page/{}.shtml'.format(i)
            # print(url)
            self.crawl(url, headers=self.headers, save={'case_type': '民事案件',
                                                        'special': 0}, callback=self.index_page)
        # 刑事文书
        for j in range(1, 11):
            url = 'http://dcqfy.chinacourt.org/paper/more/paper_mid/MzAygAMA/page/{}.shtml'.format(j)
            self.crawl(url, headers=self.headers, save={'case_type': '刑事案件',
                                                        'special': 0}, callback=self.index_page)

        # 行政文书
        for k in range(1, 2):
            url = 'http://dcqfy.chinacourt.org/paper/more/paper_mid/MzA2gAMA.shtml'
            self.crawl(url, headers=self.headers, save={'case_type': '行政案件',
                                                        'special': 0}, callback=self.index_page)
        # 执行文书
        url = 'http://dcqfy.chinacourt.org/paper/more/paper_mid/MzAxgAMA.shtml'
        self.crawl(url, headers=self.headers, save={'case_type': '执行案件',
                                                    'special': 0}, callback=self.index_page)

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        type1 = response.save['case_type']
        a = response.doc('div#list.font14 li a[href]').items()
        b = response.doc('div#list.font14 ul li span.right').items()
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
        time = response.save['time']
        case_type = response.save['type1']
        title = response.save['title']
        html = response.text

        patten = re.findall(r'tm\[.*?\]\=\"(.*?)\"', html)
        result = ''
        for x in patten:
            text = self.reverse_urlDecode_string(x)
            result = result + text

        print(result)
        try:
            time_xq = re.compile(r'(二[一二三四五六七八九十年月日ΟО0Oo○〇?]+)', re.S).findall(result)[-1].replace('?',
                                                                                                   'O')  # 如果有问号的话用大写的o代替
        except:
            time_xq = ''
        print(time)
        try:
            content_type = re.compile('<li class="type">(.*?)</li>', re.S).findall(result)[0][-3:]
        except:
            content_type = ''
        # print(case_type)
        try:
            court_name = re.compile('<li class="title"><b>(.*?)</b></li>', re.S).findall(result)[0]
        except:
            court_name = ''
        # print(court_name)
        try:
            case_no = re.compile('<li class="number">(.*?)</li>', re.S).findall(result)[0]
        except:
            case_no = ''
        # print(case_no)
        try:
            publish_date = re.compile(r'<span>([\d:-].*?)</span>', re.S).findall(result)[0]
        except:
            publish_date = ''
        # print(publish_date)
        source = '北京市东城区人民法院'
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
            'type': content_type,  # 字段是那个字段，还要把..文书，改成什么什么案件
            'court_name': court_name,
            'content_type': case_type,
            'source': source,
            'org_url': response.url,
            'trial_date': time_xq,
            'trial_round': '',
            'reason': '',
        }

    def reverse_urlDecode_string(self, string_text):
        encoding_text = unquote(string_text)
        html_text = encoding_text.replace('%', '\\').replace(';psbn&', '').encode('utf-8', 'ignore').decode(
            'unicode-escape', 'ignore')
        return html_text[::-1]