import re
import requests
from bs4 import BeautifulSoup as bs
from difflib import SequenceMatcher # 两个文本相似度
from fake_useragent import UserAgent
from urllib.parse import urljoin

import time


def info_html(url):
    rule = re.compile('''href=.*?['"](.*?)['"]''')
    headers = {
        'User-Agent': UserAgent().random
    }
    html = requests.get(url,headers=headers)
    pp = re.findall(rule,html.text)
    pp = [_ for _ in pp if '.css' not in _ and 'javascript:' not in _ and len(_) > 7]
    # 过滤属于自己域名的 url
    pp = [urljoin(url, i.replace('\\','')) for i in pp]
    print(set(pp))
    return set(pp)


# 检测两个文本的相似度
def text_similarity(t1,t2):
    return SequenceMatcher(None, t1, t2).ratio()

def woshou(list):
    def test(a, b=0, index=0,similarity_list=[]):
        for i in range(len(a) - 1):
            index += 1
            # print(a[b], a[i + 1], index)
            num = text_similarity(a[b],a[i+1])
            if num >=0.7:
                similarity_list.append((num,a[b],a[i+1]))
                # print(num,a[b], a[i+1])

            if i + 1 == len(a) - 1:
                b += 1
                a = a[b:]
                if len(a) == 1:
                    break
                test(a, b=0, index=index)
                return similarity_list
    return test(list)

def test(url):
    heasers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'
    }
    html = requests.get(url,headers=heasers,timeout=5)
    html.encoding = html.apparent_encoding
    # print(html.text)
    soup = bs(html.text,'lxml')

    # 存放匹配到的内容
    b = []
    # 匹配 class
    a = soup.find_all(attrs={'class': re.compile('(.*?title.*?)|(.*?TITLE.*?)|(.*?bt.*?)|(.*?_ti.*?)',re.I)})
    if a:
        [b.append(str(i)) for i in a]

    # 匹配 id
    a = soup.find_all(attrs={'id': re.compile('(.*?title.*?)|(.*?TITLE.*?)|(.*?bt.*?)|(.*?_ti.*?)',re.I)})
    if a:
        [b.append(str(i)) for i in a]

    # 匹配标签是 title 的
    a = soup.find_all(re.compile('(.*?title.*?)|(.*?TITLE.*?)|(.*?bt.*?)',re.I))
    if a:
        [b.append(str(i)) for i in a]

    # 匹配 h1 到 h3 标签
    a = soup.find_all(['h1','h2','h3'])
    if a:
        [b.append(str(i)) for i in a]

    lll = re.findall(r'''class=['"].*?title.*?['"].*?>(.*?)</''',html.text,re.S)
    if lll:
        lll = [i for i in lll if '<' in i or '\n' in i or '\t' in i or '>' in i]
        [b.append(i) for i in lll]

    # 过滤 js 代码 和 html标签
    pp = re.compile('(<!--.*?-->)|(<script.*?</script>)|(<.*?>)|(\s)|(<SCRIPT.*?</SCRIPT>)',re.S)
    # 可能会有空值
    b = [_ for _ in [re.sub(pp,'',i) for i in b] if _]
    # 过滤有日期的 和 标题内容必须大于6
    b = [i for i in b if len(i) >= 6]

    # 过滤列表
    filter_list = ['时间', '日期', '点击数', '字体','联系电话','ICP备','打印此文','关闭窗口','门户网站','|']

    def filter_title(a, b):
        '''
        :param a:  要过滤的列表
        :param b:  规则列表
        :return:   返回过滤后的列表
        '''
        c = []
        tt = True
        for i in a:
            for _ in b:
                if _ in i:
                    tt = False
                    break
                else:
                    continue
            if tt:
                c.append(i)
            tt = True
        return c

    b = filter_title(b,filter_list)
    # b = [i for i in b if '字体' not in i]
    # b = [i for i in b if '时间' not in i]
    # b = [i for i in b if '点击数' not in i]
    # b = [i for i in b if '联系电话' not in i]
    # b = [i for i in b if 'ICP备' not in i]

    print('开始','='*20,url)
    print(len(b),b)
    if len(b) == 1:
        title = b[0]
        print('只有一个标题',title)
    elif 4 >= len(b) >= 2:
        print(b)
        if len(b)==2 and min(b) in max(b):
            title = min(b)
        else:
            title = max([(len(_),_) for _ in b])[1]
        print('只有两个到4个',title)
    elif 13 >= len(b) > 4:
        ls = woshou(b)
        # ls = [i for i in ls if i[0]]
        print('ls',ls)
        if ls:
            ls2 = max([(len(str(i)),i) for i in ls])

            # print('过滤出来的',ls)
            if ls2:
                title = ls2[1][1]
                print(title)
        else:
            title = None

    elif len(b) > 14:
        title =None
        print('这可能是个列表页')
    else:
        title = None
        print('走的else',b)


    print('结束','='*20)

    return title

def test2(url):
    heasers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'
    }
    html = requests.get(url, headers=heasers, timeout=5)
    html.encoding = html.apparent_encoding

    text = html.text
    # 找到今年的年数
    year = str(time.localtime().tm_year)[2:]
    print(year)
    # 只提取今年的
    gz = '(20%s[年|\-|.|/][01]?\d{1}[月|\-|.|/][0123]?\d{1}日?).*?([012]?\d{1}:[0-6]?\d{1}:?[0-6]?\d?)?'%(year)
    p = re.compile(gz,re.S)
    pp = re.findall(p,text)
    pp = [(i[0].replace('/','-').replace('年','-').replace('月','-').replace('.','-').replace('日',''),i[1]) for i in pp]

    if pp:

        if len(set(pp)) == 1:
            info_time = (pp[0][0] + ' ' + pp[0][1]).strip()
            print('时间',info_time)
            return info_time
        elif 6 >= len(set(pp)) >= 2:
            print('elif--pp',set(pp))
            # 转换成时间戳
            times = [time.mktime(time.strptime(i[0], '%Y-%m-%d')) for i in set(pp)]
            # print(times)
            # 找到最大的时间戳的索引
            max_index = times.index(max(times))

            info_time = (pp[max_index][0] + ' ' + pp[max_index][1]).strip()
            print('elif时间',info_time)
            return info_time
        else:
            print('这可能是个列表页',url)
            return None

def conten(url):
    heasers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'
    }
    html = requests.get(url, headers=heasers, timeout=5)
    html.encoding = html.apparent_encoding

    text = html.text





url = 'http://www.gucn.com/Service_CurioShop_Index.html'
# test(url)
for i in info_html(url):
    # try:
    print('开始-----------',i)
    test2(i)
    test(i)
    print('结束\n\n')

    # except Exception as e:
    #     print(e,i)
