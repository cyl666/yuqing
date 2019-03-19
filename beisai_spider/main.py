import pymysql
import redis
import queue
from fake_useragent import UserAgent # 随机请求头
import json
import re
from spider_handler import sp
from no_ruler_url_handler import No_ruler
# 连接数据库
db = pymysql.connect('192.168.0.121','develop','abc123','baysidedevelop',charset='utf8')
# db = pymysql.connect('127.0.0.1','root','cyl666.','test',charset='utf8')
cursor = db.cursor()

# 连接 redis 数据库
rediscli = redis.Redis(host="47.93.114.131", port=6111, password='bayside801', db=0)


# 查询 mysql 数据
def find_data():
    # 创建 url 队列,数据库取出来的 url 放里面
    q = queue.Queue()
    cursor.execute('select url,domain from bs_listview_site limit 100 offset 10')
    row = cursor.fetchall()
    # row = [('http://www.xjcbcr.gov.cn/news/bmdt.htm','xjcbcr.gov.cn')]

    # 把查询到的数据添加到 队列中
    for i in row:
        try:
            q.put(i)
        except:
            print('没添加到队列中')
            pass
    return q


# 当 redis 数据库匹配不到的时候, 进行过滤三级域名
def filter_u(u):
    # 过滤三级域名
    filter_url = re.search(r'(.*?)\.(com|cn|net|gov|tv|org|club|xyz|top|edu|int|pub).*', u[1])
    if filter_url.group(1) and filter_url.group(1).count('.') >= 1:
        url = '.'.join(u[1].split('.')[1:])
        return url
    else:
        return u[1]


def main():
    # 查询数据
    a = find_data()
    while not a.empty():
        try:
            # 取一个 url
            u = a.get()
            # 去 redis 中进行匹配
            print('开始---------匹配main文件中的url',u[1])
            ruler = rediscli.hget('siterule', u[1]) # 0 是url 1是域名
            # 如果 mysql 和 redis 相匹配
            if ruler:
                js = json.dumps(eval(ruler))
                print('::::::::::',u)
                sp.handler_info(u,js,)

            # 处理没有匹配到规则的
            else:
                # print('没有匹配到,去掉三级域名在匹配')
                url = filter_u(u)
                ruler = rediscli.hget('siterule', url)  # 0 是url 1是域名
                # 如果 mysql 和 redis 相匹配
                if ruler:
                    print('经过域名过滤后匹配到了规则',url)
                    js = json.dumps(eval(ruler))
                    # 把 url 和 域名 全传过去 通过域名在进行过滤
                    sp.handler_info(u, js)

                # 如果 redis 中没有这个网站的规则走自己写的脚本
                else:
                    print('还是没有匹配到规则',u)
                    # 把 url 和 域名 全传过去 通过域名在进行过滤
                    # 匹配 无规则的网站
                    No_ruler(u).find_url()

        except Exception as e:
            print('规则有报错,转不了json',e,u)
            # 如果 '\x13' 在规则中 替换一下
            if ruler and '\x13' in ruler.decode():
                print('规则中有\x13')
                js = json.dumps(eval(ruler.decode().replace('\x13','').replace('\x0D','')))
                # print(js)
                url = filter_u(u)
                print(url)
                # 请求网页
                sp.handler_info(u, js)



if __name__ == '__main__':
    main()