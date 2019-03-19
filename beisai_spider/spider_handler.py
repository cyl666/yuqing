import requests
from bs4 import BeautifulSoup as bs
import json
import jsonpath
import re
from urllib.parse import urljoin
from fake_useragent import UserAgent # 随机请求头
from scrapy.selector import Selector
import queue

class Spider_info(object):
    def __init__(self):
        self.headers = {
            'User-Agent': UserAgent().random
        }

    # url 请求
    def info(self, url):
        try:
            html = requests.get(url, headers=self.headers,timeout=5)
            html.encoding = html.apparent_encoding # 自动编码
            print('状态码', html.status_code, url)
            if html.status_code == 200:
                return html.text
        except:
            print('网站可能挂了', url)
            return None

    # 根据规则匹配指定的字段
    def matching(self,rule,info_url):
        print('&&&&&&&&&&&&&规则&&&&&&&&&&&')
        # 获取 键 和 值
        for k,v in rule.items():pass
        # print('键值对',k,v)
        rule_list = {}
        title = v.get('titlerule')
        time = v.get('pubdaterule')
        content = v.get('contentrule')

        rule_list['title'] = title
        rule_list['time'] = time
        rule_list['content'] = content
        print('打印规则',rule_list)


        # 请求详细页
        info_html = self.info(info_url)
        if info_html:
            soup = bs(info_html, 'lxml')
        else:
            print('请求详细页有问题',info_url)

        try:
            # 字段信息存放
            info_list = {}
            info_list['info_url'] = info_url
            for k,v in rule_list.items():
                # print('进入循环')
                # 判断是字符串还是列表
                if isinstance(v,str):
                    print('走的if 语句',v)
                    try:
                        bt = soup.select(v)
                        if bt:
                            # 如果匹配到了 添加列表 去两边空白,并删除这个变量
                            info_list[k] = bt[0].text.strip()
                            # print('匹配到了',bt)
                            del bt
                    except Exception as e:
                        # python bs4 不支持 nth-child  可以调用 python的scrapy 框架
                        if 'nth-of-type' in str(e):
                            # 有 nth-child的时候 bs4 解析不准确, 调用 scrapy 的 css 选择器
                            try:
                                # 必须指定 text 参数 , 不然会报错
                                select_css = Selector(text=info_html)
                                bt2 = select_css.css(v+'::text') # ::text 匹配内容
                            except Exception as e:
                                print('if 中的 error报错', e)
                                print(v)
                            # 如果匹配到了
                            if bt2:
                                info_list[k] = bt2.extract()[0]

                # 如果是列表 进行循环匹配
                elif isinstance(v,list):
                    # 循环匹配
                    for index,_ in enumerate(v):
                        # print('匹配第{}个规则'.format(index+1),_)
                        # 捕获 bs4 匹配时的错误
                        try:
                            bt = soup.select(_)
                            if bt:
                                info_list[k] = bt[0].text.strip()
                                # print('匹配到了',bt)
                                del bt
                                break
                        except Exception as e:
                            if 'nth-of-type' in str(e):
                                # print('else规则中有nth-chile')
                                try:
                                    # 调用 scrapy 的 css 选择器
                                    g = _.strip() + '::text'
                                    select_css = Selector(text=info_html)
                                    bt2 = select_css.css(g)
                                except Exception as e:
                                    print('else中nth-chile报错', _, e)
                                if bt2:
                                    info_list[k] = bt2.extract()[0]
                                    # print('else匹配到了',bt2.extract()[0])
                                    break
            # 判断取到几个存数据
            if len(info_list) == 4:
                items = info_list
                # 判断时间 判断是否为今年 和 时间不能大于今天 和 时间是昨天今天
                t = items['time']
                filter_time = re.compile('(20\d{2}[年|\-|.|/][01]?\d{1}[月|\-|.|/][0123]?\d{1}日?).*?([012]?\d{1}:[0-6]?\d{1}:?[0-6]?\d?)')
                t2 = re.search(filter_time,t) # 1 是日期 2 是时间
                date = t2.group(1).replace('/', '-').replace('年', '-').replace('月', '-').replace('.', '-').replace('日', '')


                print('有规则网站提取时间',t2.group(1),'---',t2.group(2))
                print(len(items),items)
            else:
                print('没匹配到3个',len(info_list),info_list)
        except Exception as e:
            print('匹配规则是报错了',e)



    # 处理传过来的参数 和 规则
    def handler_info(self,url,js):
        jsp = jsonpath.jsonpath(json.loads(js), '.')
        # 定义规则
        # rule = re.compile(r'href="(.*?)"') #'''href=['"](.*?)['"]'''
        rule = re.compile('''href=.*?['"](.*?)['"]''')
        content = self.info(url[0]) #url[0]
        if content:
            # 匹配网页中的所有的 url
            pp = re.findall(rule, content)
            print(len(pp),'没过滤的url个数')
            # 过滤一些没用的url
            pp = [_ for _ in pp if '.css' not in _ and 'javascript:' not in _ and '.js' not in '_' and len(_) > 7]
            # 过滤属于自己域名的 url
            pp = [_ for _ in [urljoin(url[0],i) for i in pp] if url[1] in _]
            print(len(pp),'过滤后的url')

        if len(jsp[0]) == 1:
            print('开始','='*20)
            # 创建队列
            q = queue.Queue()
            # 把 url 添加到队列中
            [q.put(_) for _ in set(pp)]
            for index, _ in enumerate(set(pp)):
                info_url = urljoin(url[0], _)
                try:
                    self.matching(jsp[0],info_url)
                except Exception as e:
                    print('匹配中出现了错误^^^^^^^^^^^^^^',e)

            print('结束','=' * 20)

        # 如果匹配到多个规则 处理多个规则
        else:
            # 每个网站可能有多个规则
            for index,(k, v )in enumerate(jsp[0].items()):
                erji_url = url[0].split('/')[2].replace('www.','')
                # 如果域名和多规则的域名其中一个相同
                if  erji_url == k:
                    # 组合成单个规则 进行传参
                    math_ruler = {k:v}
                    print('开始', '=' * 20)
                    for index, _ in enumerate(set(pp)):
                        info_url = urljoin(url[0], _)
                        print('开始请求url-------------', info_url)
                        try:
                            self.matching(math_ruler, info_url)
                        except Exception as e:
                            print('匹配中出现了错误^^^^^^^^^^^^^^^^^^^^^^',e)

sp = Spider_info()


