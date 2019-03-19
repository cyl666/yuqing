from spider_handler import sp
import re
from urllib.parse import urljoin
from extract_info import Match_title # 获取标题 时间 内容

class No_ruler(object):
    def __init__(self,url):
        self.list_url = url[0]
        self.filter_url = url[1]

    def find_url(self):
        content = sp.info(self.list_url)
        # 定义规则
        rule = re.compile(r'''href=['"](.*?)["']''',re.S|re.I)
        if content:
            # 匹配网页中的所有的 url
            pp = re.findall(rule, content)
            # 过滤一些没用的url
            pp = [_ for _ in pp if '.css' not in _ and 'javascript:'  not in _ and '.js' not in '_'  and len(_) > 7]
            pp = [_ for _ in [urljoin(self.list_url,i.replace('\\','')) for i in pp] if self.filter_url in _]
            print('过滤后的url',pp)

            for i in set(pp):
                try:
                    self.handler_no_ruler(i)
                except Exception as e:
                    print('没规则出错',e)


    def handler_no_ruler(self,url):

        print('开始访问没规则的url',url)
        html = sp.info(url)
        # 匹配无规则网站的标题
        title = Match_title().title(html)
        # 匹配无规则网站的时间
        extract_time = Match_title().extract_time(html)
        # 匹配无规则网站的内容
        content = Match_title().content(html)
        if title and title and extract_time:
            items = {
                'info_url': url,
                'title': title,
                'time': extract_time,
                'content': content
            }
            print(len(items),items)
            return items
        else:
            return None

