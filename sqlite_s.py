# -*- coding:utf-8 -*-
# ! python3
import re

Col_stg = ["date", "code", "name", "trend", "next_hl",
           "temp_hl", "temp_m", "from_hl", "from_temp", "use_space", "space_h", "space_l"]
Col_stk = ["date", "hl", "price", "confirmed_date"]

def create_Strategy(tup_list, conn):
    """
    创建样本股票的高低点和趋势汇总表

    :param tup_list: 每个tuple包含12个变量
                     date:最新日期
                     code:股票代码或名称
                     name:股票简称
                     trend:当前趋势
                     next_hl:下一个将出现的是高点=1或低点=0
                     temp_hl:待判定高点或低点的价位
                     temp_m:待判定高点或低点以来的最低位或最高位
                     from_hl:待判定高点或低点距离前一个确认的低点或高点的交易天数
                     from_temp:当前距离待判定高点或低点的交易天数
                     use_space:是否满足空间高低点使用条件
                     space_h:回调平均幅度
                     space_l:反弹平均幅度
    :param conn: 数据库connection实例
    :return:
    """
    cur = conn.cursor()
    sql_del = "drop table if exists Strategy_s"
    cur.execute(sql_del)
    cur.execute(
        '''create table Strategy_s (date varchar(30), code varchar(20) primary key, name text,
        trend text, next_hl int, temp_hl real, temp_m real, from_hl int, from_temp int, use_space int,
        space_h real, space_l real)'''
    )
    if tup_list:
        cur.execute("BEGIN TRANSACTION")
        cur.executemany('''insert into Strategy_s values (?,?,?,?,?,?,?,?,?,?,?,?)''', tup_list)
        cur.execute("COMMIT")


def create_Stock(tup_list, conn, codename):
    """
    创建股票历史信息分表
    :param tup_list:每个tuple包含4个变量
                    date:日期
                    hl:高低点标记，高点=H，低点=L
                    price:高低点价位
                    confirmed_date:判定日期
    :param conn:数据库connection实例
    :param codename:
    :return:
    """
    cur = conn.cursor()
    name = code_helper(codename)
    sql_del = f'drop table if exists "{name}"'
    cur.execute(sql_del)
    cur.execute(f'''create table "{name}" (date text, hl text, price real, confirmed_date text)''')
    cur.execute("BEGIN TRANSACTION")
    cur.executemany(f'''insert into "{name}" values (?,?,?,?)''', tup_list)
    cur.execute("COMMIT")


def code_helper(codename, rev=False):
    """
    由于数据库的表名不能够以数字开头，以股票代码命名表的时候需要转换格式
    eg:000001.SH-->SH000001, 0001.HK-->HK0001, BABA-->BABA

    :param codename: 股票代码
    :param rev: 是否是逆转表名为代码名
    :return:
    """
    if not rev:
        if codename[0].isdigit():
            name = codename.split('.')
            name.reverse()
            codename = ''.join(name)

    else:
        if codename[-1].isdigit():
            res=re.search("([\w]{2})([\d]+)", codename)
            name = [res.group(2), res.group(1)]
            codename = ".".join(name)
    return codename

if __name__ == '__main__':
    res = code_helper("BABA.N")
    print(res)
