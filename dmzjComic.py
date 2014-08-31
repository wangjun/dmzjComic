#!/usr/bin/env python3
# encoding: utf-8

import requests
import re
import json
import os
import argparse

requestSession = requests.session()

class ErrorCode(Exception):
    '''自定义错误码:
        1: URL不正确
        2: 中断下载'''
    def __init__(self, code):
        self.code = code

    def __str__(self):
        return repr(self.code)

def isLegelUrl(url):
    legalUrl1 = re.compile(r'^http://(manhua|mh)\.dmzj\.com/\w+/?$')

    if legalUrl1.match(url):
        return True
    else:
        return False

def getmobileurl(url):
    if not isLegelUrl(url):
        print('请输入正确的url！具体支持的url请在命令行输入-h|--help参数查看帮助文档。')
        raise ErrorCode(1)

    url_test = re.compile(r'^http://manhua\.dmzj\.com/\w+/?$')
    if url_test.match(url):
        url = url.replace('manhua', 'mh')
    
    return url

def getContent(url):
    comic = requestSession.get(url)
    name_re = re.compile(r'var\sg_comic_name\s=\s\"(.+)\"\;')
    comicName = name_re.findall(comic.text)[0]
    comicName = comicName.strip()
    if '为此给各位漫友带来的不便，敬请谅解！' in comic.text:
        intrd_re = re.compile(r'</span><br><br>\n*(.+)\n*.*?<p>')
    else:
        intrd_re = re.compile(r'<p>\n*(.+)\n*.*?<br/>欢迎在动漫之家漫画网观看')
    comicIntrd = intrd_re.findall(comic.text)[0]
    chapterlist_re = re.compile(r'href="(.+?)"\sclass="list_href"\stitle="(.+?)".+?rel="external"')
    chapterlist = chapterlist_re.findall(comic.text)
    count = len(chapterlist)
    sortedContentList = []
    for item in chapterlist:
        chapter, chapterurl = item[1], 'http://mh.dmzj.com' + item[0]
        sortedContentList.append((chapter,chapterurl))
    return (comicName, comicIntrd, count, sortedContentList)


def getImgList(contenttuple):
    imgcontenturl = contenttuple[1]
    chapercontent = requestSession.get(imgcontenturl)
    imgurl_re = re.compile(r'var\simglist\s=\s(.+?);')
    imgurllist = imgurl_re.findall(chapercontent.text)[0]
    imgurllist = imgurllist.replace('url: fast_img_host+"', '"url": "http://images.dmzj.com').replace('caption', '"caption"')
    imgurllist = json.loads(imgurllist, encoding='utf-8')
    imgList = []
    for item in imgurllist:
        imgList.append(item['url'])
    return imgList

def downloadImg(contenttuple, imgUrlList, contentPath):
    imgcontenturl = contenttuple[1]
    count = len(imgUrlList)
    print('该集漫画共计{}张图片'.format(count))
    i = 1

    for imgUrl in imgUrlList:
        print('\r正在下载第{}张图片...'.format(i), end = '')
        imgPath = os.path.join(contentPath, '{0:0>3}.jpg'.format(i))
        i += 1
        
        #目标文件存在就跳过下载
        if os.path.isfile(imgPath):
            continue

        try:
            requestSession.headers['Referer'] = imgcontenturl
            downloadRequest = requestSession.get(imgUrl, stream=True)
            with open(imgPath, 'wb') as f:
                for chunk in downloadRequest.iter_content(chunk_size=1024): 
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
                        f.flush()
        except (KeyboardInterrupt, SystemExit):
            print('\n\n中断下载，删除未下载完的文件！')
            if os.path.isfile(imgPath):
                os.remove(imgPath)
            raise ErrorCode(2)

    print('完毕!\n')

def parseLIST(lst):
    '''解析命令行中的-l|--list参数，返回解析后的章节列表'''
    legalListRE = re.compile(r'^\d+([,-]\d+)*$')
    if not legalListRE.match(lst):
        raise LISTFormatError(lst + ' 不匹配正则: ' + r'^\d+([,-]\d+)*$')

    #先逗号分割字符串，分割后的字符串再用短横杠分割
    parsedLIST = []
    sublist = lst.split(',')
    numRE = re.compile(r'^\d+$')

    for sub in sublist:
        if numRE.match(sub):
            if int(sub) > 0: #自动忽略掉数字0
                parsedLIST.append(int(sub))
            else:
                print('警告: 参数中包括不存在的章节0，自动忽略')
        else:
            splitnum = list(map(int, sub.split('-')))
            maxnum = max(splitnum)
            minnum = min(splitnum)       #min-max或max-min都支持
            if minnum == 0:
                minnum = 1               #忽略数字0
                print('警告: 参数中包括不存在的章节0，自动忽略')
            parsedLIST.extend(range(minnum, maxnum+1))

    parsedLIST = sorted(set(parsedLIST)) #按照从小到大的顺序排序并去重
    return parsedLIST

def main(url, path, lst=None):
    '''url: 要爬取的漫画首页。 path: 漫画下载路径。 lst: 要下载的章节序号列表(-l|--list后面的参数)'''
    try:
        if not os.path.isdir(path):
           os.makedirs(path)
        url = getmobileurl(url)
        comicName,comicIntrd,count,contentList = getContent(url)
        contentNameList = []
        for item in contentList:
            contentNameList.append(item[0])
        print('漫画名: {}'.format(comicName))
        print('简介: {}'.format(comicIntrd))
        print('章节数: {}'.format(count))
        print('章节列表:')
        try:
            for i in range(1, count+1):
                print('{0:0>3}:'.format(i), contentNameList[i-1], end='\n')
        except Exception:
            print('章节列表包含无法解析的特殊字符\n')
        comicName = re.sub(r'[\\/"\':*?<>|]', '', comicName)
        comicPath = os.path.join(path, comicName)
        if not os.path.isdir(comicPath):
            os.mkdir(comicPath)
        print()

        if lst:
            contentRange = parseLIST(lst)
        else:
            lst = input('要下载的漫画章节列表，不指定则下载所有章节。格式范例: \n'
                    'N - 下载具体某一章节，如 1, 下载第1章\n'
                    'N,N... - 下载某几个不连续的章节，如 "1,3,5", 下载1,3,5章\n'
                    'N-N... - 下载某一段连续的章节，如 "10-50", 下载[10,50]章\n'
                    '杂合型 - 结合上面所有的规则，如 "1,3,5-7,11-111"\n'
                    '请输入要下载的漫画章节序号: ')
            if not lst:
                contentRange = range(1, len(contentList) + 1)
            else:
                contentRange = parseLIST(lst)

        for i in contentRange:
            if i > len(contentList):
                print('警告: 章节总数 {} ,'
                        '参数中包含过大数值,'
                        '自动忽略'.format(len(contentList)))
                break

            contentPath = os.path.join(comicPath, '第{0:0>3}话'.format(i))

            print('正在下载{0:0>3}: {1}'.format(i, contentNameList[i -1]))
            #如果章节名有左右斜杠时，不创建带有章节名的目录，因为这是路径分隔符
            forbiddenRE = re.compile(r'[\\/":*?<>|]') #windows下文件名非法字符\ / : * ? " < > |
            if not forbiddenRE.search(contentNameList[i - 1]):
                    contentPath = os.path.join(comicPath, '{0:0>3}-{1}'.format(i, contentNameList[i - 1]))

            if not os.path.isdir(contentPath):
                os.mkdir(contentPath)

            imgList = getImgList(contentList[i - 1])
            downloadImg(contentList[i - 1], imgList, contentPath)

    except ErrorCode as e:
        exit(e.code)
    
if __name__ == '__main__':
    defaultPath = os.path.join(os.path.expanduser('~'), 'dmzj_comic')

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description='*下载动漫之家漫画，仅供学习交流，请勿用于非法用途*\n'
                                     '空参运行进入交互式模式运行。')
    parser.add_argument('-u', '--url', help='要下载的漫画的首页，可以下载以下类型的url: \n'
            'http://mh.dmzj.com/sishen/\n'
            'http://manhua.dmzj.com/sishen/')
    parser.add_argument('-p', '--path', help='漫画下载路径。 默认: {}'.format(defaultPath), 
                default=defaultPath)
    parser.add_argument('-l', '--list', help=("要下载的漫画章节列表，不指定则下载所有章节。格式范例: \n"
                                              "N - 下载具体某一章节，如-l 1, 下载第1章\n"
                                              'N,N... - 下载某几个不连续的章节，如 "-l 1,3,5", 下载1,3,5章\n'
                                              'N-N... - 下载某一段连续的章节，如 "-l 10-50", 下载[10,50]章\n'
                                              '杂合型 - 结合上面所有的规则，如 "-l 1,3,5-7,11-111"'))
    args = parser.parse_args()
    url = args.url
    path = args.path
    lst = args.list

    if lst:
        legalListRE = re.compile(r'^\d+([,-]\d+)*$')
        if not legalListRE.match(lst):
            print('LIST参数不合法，请参考--help键入合法参数！')
            exit(1)

    if not url:
        url = input('请输入漫画首页地址: ')
        path = input('请输入漫画保存路径(默认: {}): '.format(defaultPath))
        if not path:
            path = defaultPath

    main(url, path, lst)
