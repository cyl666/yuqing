import re
from bs4 import BeautifulSoup as bs
from difflib import SequenceMatcher # 两个文本相似度
import time


class Match_title(object):
    # 检测两个文本的相似度
    def text_similarity(self,t1, t2):
        return SequenceMatcher(None, t1, t2).ratio()

    # 匹配相似度
    def woshou(self,list):
        def test(a, b=0, index=0, similarity_list=[]):
            for i in range(len(a) - 1):
                index += 1
                # print(a[b], a[i + 1], index)
                num = self.text_similarity(a[b], a[i + 1])
                if num >= 0.8:
                    similarity_list.append((num, a[b], a[i + 1]))
                    # print(num,a[b], a[i+1])
                if i + 1 == len(a) - 1:
                    b += 1
                    a = a[b:]
                    if len(a) == 1:
                        break
                    test(a, b=0, index=index)
                    return similarity_list

        return test(list)


    # 提取标题 title
    def title(self,text):
        soup = bs(text, 'lxml')
        # 存放匹配到的内容
        b = []
        # 匹配 class
        a = soup.find_all(attrs={'class': re.compile('(.*?title.*?)|(.*?bt.*?)|(.*?_ti.*?)', re.S|re.I)})
        if a:
            [b.append(str(i)) for i in a]

        # 匹配 id
        a = soup.find_all(attrs={'id': re.compile('(.*?title.*?)|(.*?bt.*?)|(.*?_ti.*?)', re.S|re.I)})
        if a:
            [b.append(str(i)) for i in a]

        # 匹配标签是 title 的
        a = soup.find_all(re.compile('(.*?title.*?)|(.*?bt.*?)', re.S|re.I))
        if a:
            [b.append(str(i)) for i in a]

        # 匹配 h1 到 h3 标签
        a = soup.find_all(['h1', 'h2', 'h3'])
        if a:
            [b.append(str(i)) for i in a]


        lll = re.findall(r'''class=['"].*?title.*?['"].*?>(.*?)</''', text, re.S|re.I)
        if lll:
            lll = [i for i in lll if '<' in i or '\n' in i or '\t' in i or '>' in i]
            [b.append(i) for i in lll]

        # 过滤 js 代码 和 html标签
        pp = re.compile('(<!--.*?-->)|(<script.*?</script>)|(<.*?>)|(\s)', re.S|re.I)
        # 可能会有空值
        b = [_ for _ in [re.sub(pp, '', i) for i in b] if _]
        # 过滤有日期的 和 标题内容必须大于6
        b = [i for i in b if len(i) >= 6]

        # 过滤列表
        filter_list = ['时间', '日期', '点击数', '字体', '联系电话', 'ICP备',
                       '打印此文', '关闭窗口', '门户网站', '|','+str','...'
                       'PoweredbyDiscuz','船员招聘就业的平台','招聘职位',
                       'after','$','["','([','人民政府网站'
                       ]

        # 页可以写成正则版本
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

        b = filter_title(b, filter_list)
        # b = [i for i in b if '字体' not in i]
        # b = [i for i in b if '时间' not in i]
        # b = [i for i in b if '点击数' not in i]
        # b = [i for i in b if '联系电话' not in i]
        # b = [i for i in b if 'ICP备' not in i]
        if len(b) == 1:
            title = b[0]
        elif 4 >= len(b) >= 2:
            if len(b) == 2 and min(b) in max(b):
                title = min(b)
                # print('2到4个的if',title)
            else:
                title = max([(len(_), _) for _ in b])[1]
                # print('2个到4个else', title)

        elif 10 >= len(b) > 4:
            ls = self.woshou(b)
            ls = [i for i in ls if i[0] == 1]
            ls2 = max([(len(str(i)), i) for i in ls])
            # print('过滤出来的',ls)
            if ls2:
                title = ls2[1][1]
                # print(title)
            else:
                title = None
        elif 14 >= len(b) > 10:
            title = max([(len(i),i) for i in b])[1]
            print('10-14之间',title )
        elif len(b) >= 15:
            title = None
            print('这可能是个列表页')
        else:
            print('直接没有匹配到')
            title = None
        return title

    # 提取时间
    def extract_time(self,text):
        # 替换注释
        zhushi = re.compile('(<!--.*?-->)',re.S|re.I)
        text = re.sub(zhushi,'',text)
        # 只提取今年的
        gz = '(20\d{2}[年|\-|.|/][01]?\d{1}[月|\-|.|/][0123]?\d{1}日?).*?([012]?\d{1}:[0-6]?\d{1}:?[0-6]?\d?)'
        p = re.compile(gz, re.S)
        pp = re.findall(p, text)
        pp = [(i[0].replace('/', '-').replace('年', '-').replace('月', '-').replace('.', '-').replace('日', ''), i[1]) for i in pp]

        if pp:
            # 找到今年的年数
            year = str(time.localtime().tm_year)
            if len(set(pp)) == 1:
                info_time = (pp[0][0] + ' ' + pp[0][1]).strip()
                # 转时间戳
                sjc = time.mktime(time.strptime(info_time,'%Y-%m-%d'))
                if sjc > time.time():
                    return None
                else:
                    # 如果今年在 时间中 就返回
                    if str(year) not in info_time:
                        return None
                    else:
                        return info_time
            elif 7 >= len(set(pp)) >= 2:
                # 转换成时间戳
                times = [time.mktime(time.strptime(i[0], '%Y-%m-%d')) for i in pp[:2]]
                # 提取的时间戳不能大于今天
                times = [t for t in times if t<time.time()]
                # 找到最大的时间戳的索引
                max_index = times.index(max(times))
                info_time = (pp[max_index][0] + ' ' + pp[max_index][1]).strip()
                # 如果今年在 时间中 就返回
                if str(year) not in info_time:
                    return None
                else:
                    return info_time
            else:
                print('这可能是个列表页', )
                return None
        else:
            return None

    # 匹配内容
    def content(self,text):
        soup = bs(text, 'lxml')

        # 存放匹配到的内容
        b = []
        # 匹配 class
        a = soup.find_all(
            attrs={'class': re.compile('(.*?con.*?)|(.*?text.*?)|(.*?news.*?)|(.*?article.*?)|(.*?t_fsz.*?)', re.I | re.S)})
        if a:
            [b.append(str(i)) for i in a]

        # 匹配 id
        a = soup.find_all(
            attrs={'id': re.compile('(.*?con.*?)|(.*?text.*?)|(.*?news.*?)|(.*?article.*?)|(.*?t_fsz.*?)', re.I | re.S)})
        if a:
            [b.append(str(i)) for i in a]

        # 标签过滤规则
        lis = ['<style type="text/css">.*?</style>', '<!--.*?-->',
               '<script.*?</script>', '<.*?>', '\s',
               '<SCRIPT.*?</SCRIPT>', 'type="text/css">.*?</style>'
               ]

        # 过滤 html 标签
        def filter_table(texts, lis):
            for index, t in enumerate(texts):
                for i in lis:
                    aaa = re.compile(i, re.S | re.I)
                    texts[index] = re.sub(aaa, '', texts[index])
            return texts
        # 过滤没用的标签
        b = filter_table(b, lis)

        # 过滤列表
        filter_list = ['上一篇', '下一篇','上一页','下一页','打印此页',
                       '关闭窗口','当前位置','打印本页','关闭本页','{{'
                       ]
        # 页可以写成正则版本
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

        b = filter_title(b, filter_list)
        b = [(len(i), i) for i in b]

        if b:
            # 返回匹配的内容
            return max(b)[1]
        else:
            return None

