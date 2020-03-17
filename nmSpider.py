# -*- coding: utf-8 -*-
# 作者    :Besny
# 创建时间    : 17:35

import urllib.request
import chardet
import pymysql
import re
import json

def regPath(reg,string):
    newReg = re.compile(reg)
    result = re.findall(newReg, string)
    if len(result) < 2 and len(result) > 0:
        result = result[0]
        result = result.replace('&nbsp;', '')

    return result
conn = pymysql.connect("127.0.0.1", 'root', 'root','nuomi')
cursor = conn.cursor()


url = 'http://www.nuomi9.com/list1_1/'
html = urllib.request.urlopen(url).read()
# 查看编码格式
# chardet.detect(html)
# 修改网页编码格式
html = html.decode('gbk')

reg = r'<span class="s2">(《?)<a href="(.*?)" target="_blank">(.*?)</a>(》?)</span>'

reg = re.compile(reg)

urls = re.findall(reg, html)


urls = urls[0:1]
# 作者
author = []
# 小说名称
novel = []
# 分类
category = []
for link in urls:
    if link[0] == '《':
        newUrl = "http://www.nuomi9.com" + link[1]
    else:
        newUrl = link[1]
    newUrl = "http://www.nuomi9.com/book/20/20071/"
    # print(newUrl)
    content = urllib.request.urlopen(newUrl).read()
    content = content.decode('gbk')

    content = content.replace("\r\n.html", ".html")
    content = content.replace('target="_blank">', ">")
    content = content.replace('target="_self" >', ">")
    content = content.replace('<a class="empty"', "<a")

    # 获取类型
    categoryReg = r'<a href="http://www.nuomi9.com/">糯米小说网</a> > (.*?) > '

    categoryName = regPath(categoryReg, content)
    # 获取分类ID
    try:
        categorySql = 'select id from nuomi_category where name = "%s"' % '二小'
        categoryRow = cursor.execute(categorySql)
        categoryId = cursor.fetchone()[0]
    except TypeError.NoneType:
       pass



    # 获取小说名
    novelReg = r'<h1>(.*?)</h1>'
    novelName = regPath(novelReg, content)

    # 获取作者姓名
    authorReg = r'<p>作&#160;&#160;&#160;&#160;者：(.*?)</p>'
    authorName = regPath(authorReg, content)

    # 判断作者是否存在
    ahtuorSql = 'select id from nuomi_author where name = "%s"' % authorName


    # 获取简介
    excerptReg = r'<div id="intro">内容介绍：<p>(.*?)</p></div>'
    excerpt = regPath(excerptReg, content)

    # 获取章节
    partReg = r'<dd><a href="(.*?)"(.*?)>(.*?)</a></dd>'

    parts = regPath(partReg, content)

    partTitle = []
    for part in parts:

        if part[0].find("book") == -1:
            partUrl = newUrl + part[0]
        else:
            partUrl = newUrl + part[0].split("/")[4]

        # 获取标题和内容
        partUrl = 'http://www.nuomi9.com/book/20/20071/9143257.html'
        partContent = urllib.request.urlopen(partUrl).read()
        partContent = partContent.decode('gbk')
        partContent = partContent.replace('<br />\r\n<br />\r\n', '<br /><br />')

        # print(partContent)
        # 获取章节名称
        bookReg = r'<h1>(.*?)</h1>'

        bookName = regPath(bookReg, partContent).strip()

        sort = bookName.split(' ')[0][1:-1]

        # 获取内容
        bodyReg = r'&nbsp;&nbsp;&nbsp;&nbsp;(.*?)<br /><br />'
        bodySlice = regPath(bodyReg, partContent)
        bodyString = ""
        for s in bodySlice:
            bodyString = bodyString + '&nbsp;&nbsp;&nbsp;&nbsp;'+ s + '<br />\r\n<br />\r\n'
