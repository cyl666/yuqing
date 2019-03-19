import io
import sys
import requests
from fake_useragent import UserAgent # 随机请求头
import re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8')
url = 'http://www.qh.gov.cn/zwgk/xwdt/bmdt/'
headers = {
	'User-Agent': UserAgent().random
}
html = requests.get(url,timeout=5)
html.encoding = html.apparent_encoding

print(html.text)

# 定义规则
rule = re.compile(r'''href=['"](.*?)["']''',re.S|re.I)
if html.text:
    # 匹配网页中的所有的 url
    pp = re.findall(rule, html.text)
    print(pp)