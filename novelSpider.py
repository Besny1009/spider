# -*- coding: utf-8 -*-
# 作者    :Besny
# 创建时间    : 15:40
import urllib.request

import re

import chardet

import pymysql

from datetime import datetime




class NovelSpider(object):
    # 连接数据库
    def get_conn(self):
        conntion = pymysql.connect(host="127.0.0.1", user="root", password="root", database="nuomi")
        return conntion

    # 获取小说分类
    def getCategory(self, url):
        if url != None:
            html = urllib.request.urlopen(url).read()
            html = html.decode('gbk')

            # 正则表达式
            categoryReg = r'<li><a href="(.*?)">(.*?)</a></li>'
            categoryReg = re.compile(categoryReg)
            content = re.findall(categoryReg, html)
            contentSlice = content[2:-2]

            try:

                conn = self.get_conn()
                with conn.cursor() as cursor:
                    # 选择所有的分类
                    categoryAll = 'select name from nuomi_category where id > 0'
                    cursor.execute(categoryAll)
                    result = cursor.fetchall()
                    exs = []
                    for ex in result:
                        exs.append(ex[0])
                    exs = tuple(exs)
                    data = []
                    for val in contentSlice:
                        items = val[1].split("·")
                        if len(items) > 1:
                            for item in items:
                                if item not in exs:
                                    data.append((item, 1))
                    if len(data):
                        # 添加数据
                        sql = "insert into nuomi_category(`name`,`is_show`) values (%s,%s)"
                        cursor.executemany(sql, data)
                        conn.commit()
            except Exception as e:
                print(e.args)
                conn.rollback()
            finally:
                conn.close()

    # 获取分类下的小说
    def getNovel(self, novelCategoryUrl):
        if novelCategoryUrl:
            html = urllib.request.urlopen(novelCategoryUrl).read()
            html = html.decode('gbk')
            # # 判断分类
            # categoryReg = r'<h2>(.*?)</h2>'
            # categoryReg = re.compile(categoryReg)
            # category = re.findall(categoryReg, html)
            # categoryName = category[0][3:5]

            # 获取分类下的文章
            reg = r'<span class="s2">(《?)<a href="(.*?)"(\s?)(.*?)>(.*?)</a>(》?)</span>'
            reg = re.compile(reg)
            newHtml = re.findall(reg, html)
            for item in newHtml:
                self.getNovelDetail(item[1])

            # # 获取数据库连接
            # conn = self.get_conn()
            #
            # try:
            #     with conn.cursor() as cursor:
            #         # 查询分类的ID
            #         categorySelectSql = 'select id from nuomi_category where name=%s'
            #         cursor.execute(categorySelectSql, (categoryName,))
            #         getCatResult = cursor.fetchone()
            #         if getCatResult != None:
            #             category_id = getCatResult[0]
            #
            #             data = []
            #             for item in newHtml:
            #                 # 获取该分类下的所有小说
            #                 findNovelOfCategorySql = 'select title,category_id,novel_url from nuomi_novel where category_id=%s and title=%s and novel_url=%s'
            #                 cursor.execute(findNovelOfCategorySql, (category_id, item[-2], item[1]))
            #                 if cursor.fetchone() == None:
            #                     data.append((item[-2], category_id, item[1]))
            #             # 获取新数据不为零时，向数据库插入新数据
            #             if len(data) > 0:
            #                 insertDataToNovel = 'insert into nuomi_novel(title,category_id,novel_url) values ()'
            # except Exception as e:
            #     print(e.args)
            #     conn.rollback()
            # finally:
            #     conn.close()

    # 获取小说详情页
    def getNovelDetail(self, detailUrl):
        if len(detailUrl):
            html = urllib.request.urlopen(detailUrl).read()
            html = html.decode('gbk')
            # print(html)
            # 获取分类
            categoryRag = r' &gt; <a href="(.*?)">(.*?)</a>  &gt; '
            categoryRag = re.compile(categoryRag)
            category = re.findall(categoryRag, html)
            category = category[0][1][0:2]

            # 获取作者
            authorReg = r'<p>作&nbsp;&nbsp;&nbsp;&nbsp;者：(.*?)</p>'
            authorReg = re.compile(authorReg)
            author = re.findall(authorReg, html)[0]

            # 获取小说名称
            titleReg = r'<h1>(.*?)</h1>'
            titleReg = re.compile(titleReg)
            title = re.findall(titleReg, html)[0]


            # 获取小说简介
            excerptReg = r'<p>(.*?)</p>'
            excerptReg = re.compile(excerptReg)
            excerpt = re.findall(excerptReg, html)[-2]

            # 获取章节
            partReg = r'<dd><a href="(.*?)">(.*?)</a></dd>'
            partReg = re.compile(partReg)
            parts = re.findall(partReg, html)
            # print(parts)


            conn = self.get_conn()
            try:
                cursor = conn.cursor()
                # 添加作者
                selectSql = 'select * from nuomi_author where name = %s'
                cursor.execute(selectSql, (author,))
                authorResult = cursor.fetchone()

                # 获取分类
                categorySql = 'select id from nuomi_category where name=%s'
                cursor.execute(categorySql, (category))
                catResult = cursor.fetchone()
                category_id = catResult[0]

                if authorResult == None:
                    insertSql = "insert into nuomi_author(name) values (%s)"
                    cursor.execute(insertSql, (author))
                    conn.commit()
                    author_id = cursor.lastrowid
                else:
                    author_id = authorResult[0]


                # 添加小说名称
                novelSql = 'select id from nuomi_novel where title=%s and excerpt=%s and author_id=%s and category_id=%s'
                cursor.execute(novelSql, (title, excerpt, author_id, category_id))
                novelSearchResult = cursor.fetchone()
                if novelSearchResult == None:
                    insertNovelSql = 'insert into nuomi_novel(title,excerpt,author_id,category_id,create_time,modified_time) values (%s,%s,%s,%s,%s,%s)'
                    cursor.execute(insertNovelSql, (title, excerpt, author_id, category_id, datetime.now(), datetime.now()))
                    conn.commit()
                    novel_id = cursor.lastrowid
                    # 获取章节内容
                    data = []
                    for part in parts:
                        current_time = datetime.now()
                        part = list(part)
                        part[0] = 'https://www.hongyeshuzhai.com' + part[0]
                        part.extend([novel_id, current_time, current_time])
                        data.append(tuple(part))
                    data = tuple(data)
                    insertPartSql = 'insert into nuomi_parts(part_url,title,novel_id,create_time,modified_time) values (%s,%s,%s,%s,%s)'
                    cursor.executemany(insertPartSql, data)
                    conn.commit()
                    # 获取每章详情
                    # for partDetail in data:
                    #     self.getPartContent(partDetail[0])
            except Exception as e:
                print(e.args)
                conn.rollback()
            finally:
                conn.close()


    # 获取章节内容
    def getPartContent(self, partUrl):
        if partUrl != None:
            html = urllib.request.urlopen(partUrl).read()
            html = html.decode('gbk')
            html = html.replace('<br />\r\n<br />\r\n', '<br /><br />')
            # 正则
            reg = r'<div id="content">(.*?)</div>'
            reg = re.compile(reg)
            content = re.findall(reg, html)
            content = content[0]

            conn = self.get_conn()
            try:
                with conn.cursor() as cursor:
                    getPartInfo = 'select id,body from nuomi_parts where part_url = %s and body is NULL '
                    cursor.execute(getPartInfo, (partUrl,))
                    result = cursor.fetchone()
                    print(result)
                    if result != None:
                        if result[1] == None:
                            # 添加数据
                            insertDataToParts = 'update nuomi_parts set body = %s where id = %s'
                            cursor.execute(insertDataToParts, (content, result[0]))
                            conn.commit()
                            print("更新数据成功")
            except Exception as e:
                print(e.args)
                conn.rollback()
            finally:
                conn.close()

        pass

    # 批量处理获取小说的每张的内容
    def dealParts(self):
        conn = self.get_conn()
        try:
            with conn.cursor() as cursor:
                partNullSql = 'select part_url from nuomi_parts where body is NULL '
                cursor.execute(partNullSql)
                result = cursor.fetchmany(10000)

                for item in result:
                    print(item[0])
                    self.getPartContent(item[0])

        except Exception as e:
            print(e.args)
            conn.rollback()
        finally:
            conn.close()
        pass



# 函数调用

novel = NovelSpider()
# 获取分类的文章
# url = 'https://www.hongyeshuzhai.com/'
# novel.getCategory(url)
# 测试数据库连接
# # print(novel.get_conn())
# 获取分类下的小说

# novelUrl = 'https://www.hongyeshuzhai.com/kehuanxiaoshuo/'
# novel.getNovel(novelUrl)
# 获取小说详情
# detailUrl = 'https://www.hongyeshuzhai.com/shuzhai/56609/'
# novel.getNovelDetail(detailUrl)

# 获取每一章的内容
# partUrl = 'https://www.hongyeshuzhai.com/shuzhai/3346/14768905.html'
# novel.getPartContent(partUrl)

novel.dealParts()

