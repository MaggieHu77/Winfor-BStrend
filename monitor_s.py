# -*- coding:utf-8 -*-
# ! python3

from apscheduler.triggers.cron import CronTrigger
import sqlite3
from os import path, makedirs
# from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
import logging
from logging.handlers import TimedRotatingFileHandler
from sqlite_s import create_Strategy, create_Stock, code_helper, Col_stg
from graph import runbacktest
from WindPy import w
from datetime import date, timedelta
from numpy import nan
import locale
from pandas import DataFrame, concat
from email_s import SendEmail
from constant import *
from hlPoint import HLPoint
from trend import Trend


# 设置daily trigger，均以东八区时间为基准
# trigger1港股和A股市场获取最新日线行情c
trigger1 = None


def set_triggers():
    global trigger1
    trigger1 = CronTrigger(day_of_week="mon-fri", hour=int(SET_T.split(":")[0]), minute=SET_T.split(
        ":")[1])

# magic number:上证综指000001.SH, 恒生指数HSI.HI，标普500 SPX.GI
sh = "000001.SH"
hsi = "HSI.HI"
spx = "SPX.GI"

# 设置运行日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(filename)s [lineno)d] %(levelname)s %(" "message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    # filename="bsgui3_logging.txt",
    filemode="a",
    # handlers=TimedRotatingFileHandler(when="W0", backupCount=1)
)
mylogger = logging.getLogger()
mylogger.addHandler(TimedRotatingFileHandler(filename="BS_s_logging.txt", when="W0",
                                             backupCount=1))

class Monitor():
    def __init__(self):
        self.emailFreq = 1  # 发信默认是1
        # 声明参数文件编辑对象
        self.codeList = []
        self.rerunList = []
        # 初始化参数设置文件
        self.runIn()

    def runIn(self):
        """
        从文件中读入代码，并嵌入三大指数
        :return:
        """
        for code in open(CODE_FILE):
            code = code.strip("\n|;|,|/|")
            self.codeList.append(code)
        self.codeList = indexTop(self.codeList.copy(), True)

    def check_dir(self):
        if not path.exists(WORK):
            makedirs(WORK)
        if not path.exists(GRAPH):
            makedirs(GRAPH)
        if not path.exists(path.dirname(DATABASE)):
            makedirs(path.dirname(DATABASE))

    def init_single(self, code, end_date=str(date.today())):
        conn = sqlite3.connect(DATABASE, isolation_level=None, timeout=3)
        cur = conn.cursor()
        cur.execute(f'''drop table if exists "{code_helper(code)}"''')
        print(f"\t重新回测{code}")
        res = runbacktest(
            begin=BEGIN_DATE,
            codename=code,
            dir=GRAPH,
            end=end_date,
            paint=True,
            # end="20181106"
        )
        if not res:
            print("\t{code}不满足策略条件，已忽略")
            return
        else:
            strategy_info, stock_info = res[0:2]
            # 缺失当前趋势判断信息，无法继续判断应取出这只股票
            if not strategy_info[2]:
                print(f"Waring:{code}趋势信息缺失，请检查回测结果；"
                      f"继续运行策略将剔除该股票")
                self.codeList.remove(code)
                return
        create_Stock(stock_info, conn, code)
        cur.execute(f'''delete from Strategy_s where code="{code}"''')
        cur.execute('''insert into Strategy_s values (?,?,?,?,?,?,?,?,?,?,?,?)''',
                    strategy_info)

    def init(self):
        conn = sqlite3.connect(DATABASE, isolation_level=None, timeout=3)
        cur = conn.cursor()
        cur.execute('''select name from sqlite_master where type="table"''')
        table_list = [ii[0] for ii in cur.fetchall()]
        if table_list:
            if "Strategy_s" in table_list:
                table_list.remove("Strategy_s")
            else:
                create_Strategy((), conn)
            table_list1 = [code_helper(ii, rev=True) for ii in table_list]
            for code in self.codeList:
                if code not in table_list1:
                    self.rerunList.append(code)
        else:
            create_Strategy((), conn)
            self.rerunList = self.codeList
        print("---正在进行数据库初始化\n")
        if self.rerunList:
            print(f"---{len(self.rerunList)}只股票需初始化回测...\n")
            topaint = [False] * len(self.rerunList)
            if str(PAINT).isdigit():
                if int(PAINT):
                    topaint[0: int(PAINT)] = [True]*int(PAINT)
            elif not PAINT:
                pass
            elif ":" in PAINT:
                pp = PAINT.split(":")
                pp = [int(p.strip()) for p in pp]
                assert len(pp) == 2, "输入回测股票图像区间格式错误，期望m:n"
                if pp[0] < len(self.rerunList):
                    topaint[(pp[0] - 1):pp[1]] = [True]*(pp[1] - pp[0] + 1)
            elif ";" in PAINT:
                pp = PAINT.split(";")
                pp = [p.strip().upper() for p in pp]
                for p in pp:
                    if p in self.rerunList:
                        topaint[self.rerunList.index(p)] = True
            for code in self.rerunList:
                res = runbacktest(
                    begin=BEGIN_DATE,
                    codename=code,
                    dir=GRAPH,
                    end=str(date.today()),
                    paint=topaint[self.rerunList.index(code)],
                    # end="20181129"
                )
                # 返回结果为空，说明回测出现错误，股票不符合继续运行条件
                if not res:
                    self.codeList.remove(code)  # 列表中除去该股票
                    continue  # 继续运行下一只股票
                else:
                    strategy_info, stock_info = res[0:2]
                    # 缺失当前趋势判断信息，无法继续判断应取出这只股票
                    if not strategy_info[2]:
                        print(f"Waring:{code}趋势信息缺失，请检查回测结果；"
                              f"继续运行策略将剔除该股票")
                        self.codeList.remove(code)
                        continue
                create_Stock(stock_info, conn, code)
                cur.execute(f'''delete from Strategy_s where code="{code}"''')
                cur.execute('''insert into Strategy_s values (?,?,?,?,?,?,?,?,?,?,?,?)''',
                            strategy_info)
        print("---数据初始化完成！")
        cur.close()
        conn.close()

    def set_sche(self):
        """
        布置工作
        :return:
        """
        self.sche = BlockingScheduler()
        self.sche._logger = logging
        self.sche.add_job(
            func=self.daily1, args=(), trigger=trigger1, id="HK and A-share stock job"
        )
        # self.sche.add_job(
        #     func=self.daily2, args=(), trigger=trigger2, id="US stock job"
        # )
        self.sche.start()

    def daily1(self):
        if not w.isconnected():
            w.start()
        conn = sqlite3.connect(DATABASE, isolation_level=None, timeout=3)
        cur = conn.cursor()
        cur.execute('''select code from Strategy_s''')
        # 获取数据库中维护的股票代码
        codes = (code[0] for code in cur.fetchall())
        # 仅保留港股和A股代码
        codes = tuple(filter(lambda x: x[0].isdigit() or x == hsi, codes))
        # 获取今日日期时间戳
        stamp = str(date.today())
        # stamp = '2018-10-25'
        # 格式化今日时间戳
        locale.setlocale(locale.LC_CTYPE, "chinese")
        stampf = date.today().strftime("%Y年%m月%d日")
        # stampf = '2018年10月19日'
        self.chgList = []
        # 提取全部样本股的价格数据
        high_p = w.wsd(",".join(codes), "high", stamp, stamp).Data[0]
        low_p = w.wsd(",".join(codes), "low", stamp, stamp).Data[0]
        trade_status = w.wsd(",".join(codes), "trade_status", stamp, stamp).Data[0]
        # high_p = w.wsd(",".join(codes), "high", '2018-11-23', '2018-11-23').Data[0]
        # low_p = w.wsd(",".join(codes), "low", '2018-11-23', '2018-11-23').Data[0]
        # trade_status = w.wsd(",".join(codes), "trade_status", '2018-11-23', '2018-11-23').Data[0]
        for dd in codes:
            # 提取总表中信息
            # 取出今天数据
            print("正在更新："+dd)
            dd_i = codes.index(dd)
            high = high_p[dd_i]
            low = low_p[dd_i]
            status = trade_status[dd_i]
            # 提取总表中信息
            if dd not in [sh, hsi] and status == "停牌一天":
                continue
            if not high or not low or high == nan or low == nan:
                continue
            cur.execute(f'''select * from Strategy_s where code="{dd}"''')
            dd_dict = dict(zip(Col_stg, cur.fetchone()))
            stock_tb = code_helper(dd)
            # dat = dd_dict["date"]
            # if dat == stamp:
            #     continue
            trd = dd_dict["trend"]
            hl = dd_dict["next_hl"]
            temp_hl = dd_dict["temp_hl"]
            temp_m = dd_dict["temp_m"]
            from_hl = dd_dict["from_hl"]
            from_temp = dd_dict["from_temp"]
            use_space = dd_dict["use_space"]
            space_h = dd_dict["space_h"]
            space_l = dd_dict["space_l"]
            # 取出高点数据
            cur.execute(f'''select price from "{stock_tb}" where hl='H' order by date''')
            #print(cur.fetchall())
            highs = [h[0] for h in cur.fetchall()]
            pre_high = highs[-1]
            pre2_high = highs[-2]
            # 取出低点数据
            cur.execute(f'''select price from "{stock_tb}" where hl='L' order by date''')
            lows = [l[0] for l in cur.fetchall()]
            pre_low = lows[-1]
            pre2_low = lows[-2]
            cur.execute(f'''select hl from "{stock_tb}" order by date''')
            first_hl = cur.fetchone()[0]
            if first_hl == "H":
                n1 = min(len(highs) - 1, len(lows))
                n2 = min(len(highs), len(lows))
                l2h = [(lows[i], highs[i + 1]) for i in range(n1)]
                h2l = [(highs[i], lows[i]) for i in range(n2)]
            else:
                n1 = min(len(highs), len(lows))
                n2 = min(len(highs), len(lows) - 1)
                l2h = [(lows[i], highs[i]) for i in range(n1)]
                h2l = [(highs[i], lows[i + 1]) for i in range(n2)]
            # 新增数据对策略影响
            hl_res = HLPoint.step_hl_s(hl, high, low, temp_hl, temp_m, from_hl, from_temp,
                              pre_high, pre_low, use_space, space_h, space_l, l2h, h2l)
            if hl_res["is_high"]:
                t = w.tdaysoffset(-(from_temp + 1), stamp).Times[0].strftime("%Y-%m-%d")
                cur.execute(f"insert into '{stock_tb}' values (?,?,?,?)", (t, "H", temp_hl, stamp))
                pre2_high = pre_high
                pre_high = hl_res["pre_high"]
            elif hl_res["is_low"]:
                t = w.tdaysoffset(-(from_temp + 1), stamp).Times[0].strftime("%Y-%m-%d")
                cur.execute(f"insert into '{stock_tb}' values (?,?,?,?)", (t, "L", temp_hl, stamp))
                pre2_low = pre_low
                pre_low = hl_res["pre_low"]

            trdmax_res = Trend.step_trdmax_s(hl_res["hl"], low, high, hl_res["from_temp"],
                                             hl_res["from_hl"], hl_res["temp_hl"], trd)
            if trdmax_res[1]:
                self.chgList.append((dd, trdmax_res[0], trd))
                trd = trdmax_res[0]
            else:
                trd_res = Trend.step_trd_s(trd, hl_res["hl"],
                                 low, high, pre_low,
                                 pre_high, pre2_low,
                                 pre2_high)
                if trd_res != trd:
                    self.chgList.append((dd, trd_res, trd))
                    trd = trd_res

            try:
                cur.execute(f'''update Strategy_s set date="{stamp}", trend="{trd}",
                                        next_hl={hl_res["hl"]}, temp_hl={hl_res["temp_hl"]}, 
                                        temp_m={hl_res["temp_m"]},
                                        from_hl={hl_res["from_hl"]}, from_temp={hl_res[
                                        "from_temp"]}, 
                                        use_space={hl_res["use_space"]}, space_h={hl_res[
                                        "space_h"]},
                                        space_l={hl_res["space_l"]} where code="{dd}"''')
            except sqlite3.OperationalError as e:
                print(e)
                print(f'''Sqlite error: {dd} new info: trend:{trd}, next_hl:{hl_res['hl']}, 
                     temp_hl:{hl_res['temp_hl']}, temp_m:{hl_res['temp_m']}, from_hl:{hl_res[
                      'from_hl']}, from_temp:{hl_res['from_temp']}, use_space:{hl_res[
                      'use_space']}, space_h={hl_res['space_h']}, space_l={hl_res['space_l']}''')
        cur.close()
        conn.close()
        if len(codes) > 2:
            res = self.sent()
            if res:
                mail_obj = SendEmail()
                mail_obj.buildHTML(res["chg"], res["up"],
                                   res["down"], res["consd"], res["img"], stampf)
                mail_obj.imageHTML(res["chg_img"])
                subject = ["趋势策略每日报告", "趋势策略变动报告-A股、港股"][FREQ]
                mail_obj.setSend(subject, SENDER, RECEIVER, SENDER_KEY)
                print(stampf + f"邮件是否成功发送？{mail_obj.isSent}")

        self.daily2()

    def sent(self):
        if FREQ and not len(self.chgList):
            pass
        else:
            conn = sqlite3.connect(DATABASE, isolation_level=None, timeout=5)
            cur = conn.cursor()
            # 用list嵌套结构构建DataFrame
            chg_tb = []
            for ii in self.chgList:
                chg_tb.append([])
                chg_tb[-1].append(ii[0])
                cur.execute(f'''select name from Strategy_s where code="{ii[0]}"''')
                chg_tb[-1].append(cur.fetchone()[0])
                chg_tb[-1].append(ii[1])
                chg_tb[-1].append(ii[2])
            # 图像部分单独处理
            chg_img = [ii[0] for ii in self.chgList]
            chg_img = indexTop(chg_img.copy(), True)
            for jj in range(len(chg_img)):
                # 更新画图
                res = runbacktest(begin=BEGIN_DATE, codename=chg_img[jj], dir=GRAPH,
                                 star=True, end=str(date.today()))
                chg_img[jj] = res[2]
                # 可能会出现图片不存在的情况，会有assertionerror出现就不能继续画图的过程
                # if not path.isfile(chg_img[jj]):
            if self.chgList:
                chg_tb = DataFrame(chg_tb, columns=["股票代码", "股票名称", "当前趋势", "之前趋势"])
                # 为了用户友好，把趋势类型用文字替代
                chg_tb.iloc[:, 2] = \
                    chg_tb.iloc[:, 2].apply(lambda x: "上涨" if x == 'up' else '盘整'
                if x == 'consd' else
                '下跌')
                chg_tb.iloc[:, 3] = \
                    chg_tb.iloc[:, 3].apply(lambda x: "上涨" if x == 'up' else '盘整'
                if x == 'consd' else
                '下跌')
            else:
                chg_tb = DataFrame(columns=["股票代码", "股票名称", "当前趋势", "之前趋势"])
            # 用list-tuple嵌套结构构建DataFrame
            cur.execute('''select code, name, trend from Strategy_s where trend="up"''')
            up_tb = cur.fetchall()
            if up_tb:
                up_tb = DataFrame(up_tb, columns=["股票代码", "股票名称", "当前趋势"])
                up_tb.iloc[:, 2] = '上涨'
                upg = indexTop(list(up_tb.iloc[:, 0]), False)
                upidx = up_tb.loc[upg, :]
                upres = up_tb.drop(upg)
                up_tb = concat([upidx, upres], ignore_index=True)
            else:
                up_tb = DataFrame(columns=["股票代码", "股票名称", "当前趋势"])
            # 用list-tuple嵌套结构构建DataFrame
            cur.execute('''select code, name, trend from Strategy_s where trend="down"''')
            down_tb = cur.fetchall()
            if down_tb:
                down_tb = DataFrame(down_tb, columns=["股票代码", "股票名称", "当前趋势"])
                down_tb.iloc[:, 2] = '下跌'
                downg = indexTop(list(down_tb.iloc[:, 0]), False)
                downidx = down_tb.loc[downg, :]
                downres = down_tb.drop(downg)
                down_tb = concat([downidx, downres], ignore_index=True)
            else:
                down_tb = DataFrame(columns=["股票代码", "股票名称", "当前趋势"])
            # 用list-tuple嵌套结构构建DataFrame
            cur.execute('''select code, name, trend from Strategy_s where trend="consd"''')
            consd_tb = cur.fetchall()
            if consd_tb:
                consd_tb = DataFrame(consd_tb, columns=["股票代码", "股票名称", "当前趋势"])
                consd_tb.iloc[:, 2] = '盘整'
                consdg = indexTop(list(consd_tb.iloc[:, 0]), False)
                consdidx = consd_tb.loc[consdg, :]
                consdres = consd_tb.drop(consdg)
                consd_tb = concat([consdidx, consdres], ignore_index=True)
            else:
                consd_tb = DataFrame(columns=["股票代码", "股票名称", "当前趋势"])
            # 创建chg_tb的HTML字符串
            chg_th = '''<tr>'''
            chg_cell = ''
            for th in range(len(chg_tb.columns)):
                chg_th += f'''<th class="thbg0 thfont">{chg_tb.columns[th]}</th>'''
            chg_th += '''</tr>'''
            if chg_tb.shape[0]:
                for tr in range(chg_tb.shape[0]):
                    chg_cell += '<tr>'
                    for th in range(len(chg_tb.columns)):
                        chg_cell += f'''<td class="cell">{chg_tb.iloc[tr, th]}</td>'''
                    chg_cell += '</tr>'
            else:
                chg_cell += '<tr><td colspan="4" align="center">暂无变动信息</td></tr>'
            chg_html = chg_th + chg_cell

            # 创建up_tb的HTL字符串
            up_th = '''<tr>'''
            up_cell = ''
            for th in range(len(up_tb.columns)):
                up_th += f'''<th class="thbg thfont">{up_tb.columns[th]}</th>'''
            up_th += '''</tr>'''

            if up_tb.shape[0]:
                for tr in range(up_tb.shape[0]):
                    up_cell += '<tr>'
                    for th in range(len(up_tb.columns)):
                        up_cell += f'''<td class="cell">{up_tb.iloc[tr, th]}</td>'''
                    up_cell += '</tr>'
            else:
                up_cell = '<tr><td colspan="3" align="center">暂无变动信息</td></tr>'
            up_html = up_th + up_cell
            # 创建down_tb的HTML字符串
            down_th = '''<tr>'''
            down_cell = ''
            for th in range(down_tb.shape[1]):
                down_th += f'''<th class="thbg thfont">{down_tb.columns[th]}</th>'''
            down_th += '''</tr>'''
            if down_tb.shape[0]:
                for tr in range(down_tb.shape[0]):
                    down_cell += '<tr>'
                    for th in range(len(down_tb.columns)):
                        down_cell += f'''<td class="cell">{down_tb.iloc[tr, th]}</td>'''
                    down_cell += '</tr>'
            else:
                down_cell = '<tr><td colspan="3" align="center">暂无变动信息</td></tr>'
            down_html = down_th + down_cell
                # 创建consd_tb的HTML字符串
            consd_th = '''<tr>'''
            consd_cell = ''
            for th in range(consd_tb.shape[1]):
                consd_th += f'''<th class="thbg thfont">{consd_tb.columns[th]}</th>'''
            consd_th += '''</tr>'''
            if consd_tb.shape[0]:
                for tr in range(consd_tb.shape[0]):
                    consd_cell += '<tr>'
                    for th in range(len(consd_tb.columns)):
                        consd_cell += f'''<td class="cell">{consd_tb.iloc[tr, th]}</td>'''
                    consd_cell += '</tr>'
            else:
                consd_cell = '<tr><td colspan="4" align="center">暂无变动信息</td></tr>'
            consd_html = consd_th + consd_cell

            img_html = ''
            for ii in range(len(chg_img)):
                img_html += f'''<b><div align="center"><img src="cid:image{ii}" 
                alt="strategy trend picture" width="850" height="457" 
                style="display:block;font-family:Arial;"></div></b>'''
            return {"chg": chg_html, "up": up_html, "down": down_html,
                    "consd": consd_html, "img": img_html, "chg_img": chg_img}

    def daily2(self):
        if not w.isconnected():
            w.start()
        conn = sqlite3.connect(DATABASE, isolation_level=None, timeout=3)
        cur = conn.cursor()
        cur.execute('''select code from Strategy_s''')
        # 获取数据库中维护的股票代码
        codes = (code[0] for code in cur.fetchall())
        # 仅保留美股代码
        codes = tuple(filter(lambda x: not x[0].isdigit() and x != hsi, codes))
        # 获取今日日期时间戳，需要用美国东部时区的时间
        today = date.today()
        # 如果今天是北京时间周一
        if not today.weekday():
            # 换算成美国东部时间的上周五，减去三天
            stamp = today - timedelta(days=3)
        else:
            # 换算成美国时间的上个交易日，减去一天
            stamp = today - timedelta(days=1)
        stamp = stamp.strftime("%Y-%m-%d")
        # 格式化今日时间戳
        locale.setlocale(locale.LC_CTYPE, "chinese")
        stampf = "{}年{}月{}日 tz=US/Eastern".format(*stamp.split("-"))
        self.chgList = []
        high_p = w.wsd(",".join(codes), "high", stamp, stamp).Data[0]
        low_p = w.wsd(",".join(codes), "low", stamp, stamp).Data[0]
        # high_p = w.wsd(",".join(codes), "high", '2018-11-27', '2018-11-27').Data[0]
        # low_p = w.wsd(",".join(codes), "low", "2018-11-27", "2018-11-27").Data[0]
        for dd in codes:
            # 提取总表中信息
            # 取出今天数据
            dd_i = codes.index(dd)
            high = high_p[dd_i]
            low = low_p[dd_i]
            if not high or not low or high == nan or low == nan:
                continue
            print("正在更新："+dd)
            cur.execute(f'''select * from Strategy_s where code="{dd}"''')
            dd_dict = dict(zip(Col_stg, cur.fetchone()))
            stock_tb = code_helper(dd)
            trd = dd_dict["trend"]
            hl = dd_dict["next_hl"]
            temp_hl = dd_dict["temp_hl"]
            temp_m = dd_dict['temp_m']
            from_hl = dd_dict["from_hl"]
            from_temp = dd_dict["from_temp"]
            use_space = dd_dict["use_space"]
            space_h = dd_dict["space_h"]
            space_l = dd_dict["space_l"]
            # 取出高点数据
            cur.execute(f'''select price from "{stock_tb}" where hl='H' order by date''')
            highs = [h[0] for h in cur.fetchall()]
            pre_high = highs[-1]
            pre2_high = highs[-2]
            # 取出低点数据
            cur.execute(f'''select price from "{stock_tb}" where hl='L' order by date''')
            lows = [l[0] for l in cur.fetchall()]
            pre_low = lows[-1]
            pre2_low = lows[-2]
            cur.execute(f'''select hl from "{stock_tb}" order by date''')
            first_hl = cur.fetchone()[0]
            if first_hl == "H":
                n1 = min(len(highs) - 1, len(lows))
                n2 = min(len(highs), len(lows))
                l2h = [(lows[i], highs[i + 1]) for i in range(n1)]
                h2l = [(highs[i], lows[i]) for i in range(n2)]
            else:
                n1 = min(len(highs), len(lows))
                n2 = min(len(highs), len(lows) - 1)
                l2h = [(lows[i], highs[i]) for i in range(n1)]
                h2l = [(highs[i], lows[i + 1]) for i in range(n2)]

            # 新增数据对策略影响
            hl_res = HLPoint.step_hl_s(hl, high, low, temp_hl, temp_m, from_hl, from_temp,
                                       pre_high, pre_low, use_space, space_h, space_l, l2h, h2l)
            if hl_res["is_high"]:
                t = w.tdaysoffset(-(from_temp + 1), stamp).Times[0].strftime("%Y-%m-%d")
                cur.execute(f"insert into '{stock_tb}' values (?,?,?,?)", (t, "H", temp_hl, stamp))
                pre2_high = pre_high
                pre_high = hl_res["pre_high"]
            elif hl_res["is_low"]:
                t = w.tdaysoffset(-(from_temp + 1), stamp).Times[0].strftime("%Y-%m-%d")
                cur.execute(f"insert into '{stock_tb}' values (?,?,?,?)", (t, "L", temp_hl, stamp))
                pre2_low = pre_low
                pre_low = hl_res["pre_low"]

            trdmax_res = Trend.step_trdmax_s(hl_res["hl"], low, high, hl_res["from_temp"],
                                             hl_res["from_hl"], hl_res["temp_hl"], trd)
            if trdmax_res[1]:
                self.chgList.append((dd, trdmax_res[0], trd))
                trd = trdmax_res[0]
            else:
                trd_res = Trend.step_trd_s(trd, hl_res["hl"],
                                       low, high, pre_low,
                                       pre_high, pre2_low,
                                       pre2_high)
                if trd_res != trd:
                    self.chgList.append((dd, trd_res, trd))
                    trd = trd_res

            try:
                cur.execute(f'''update Strategy_s set date="{stamp}", trend="{trd}",
                                        next_hl={hl_res["hl"]}, temp_hl={hl_res["temp_hl"]}, 
                                        temp_m={hl_res["temp_m"]},
                                        from_hl={hl_res["from_hl"]}, from_temp={hl_res[
                                        "from_temp"]}, 
                                        use_space={hl_res["use_space"]}, space_h={hl_res[
                                        "space_h"]},
                                        space_l={hl_res["space_l"]} where code="{dd}"''')
            except sqlite3.OperationalError as e:
                print(e)
                print(f'''Sqlite error: {dd} new info: trend:{trd}, next_hl:{hl_res['hl']}, 
                     temp_hl:{hl_res['temp_hl']}, temp_m:{hl_res['temp_m']}, from_hl:{hl_res[
                      'from_hl']}, from_temp:{hl_res['from_temp']}, use_space:{hl_res[
                      'use_space']}, space_h={hl_res['space_h']}, space_l={hl_res['space_l']}''')
        cur.close()
        conn.close()
        if len(codes) <= 1:
            pass
        else:
            res = self.sent()
            if res:
                mail_obj = SendEmail()
                mail_obj.buildHTML(res["chg"], res["up"],
                                   res["down"], res["consd"], res["img"], stampf)
                mail_obj.imageHTML(res["chg_img"])
                subject = ["趋势策略每日报告", "趋势策略变动报告-美股"][FREQ]
                mail_obj.setSend(subject, SENDER, RECEIVER, SENDER_KEY)
                print(stampf + f"邮件是否成功发送？{mail_obj.isSent}")


# 保证三大指数：上证综指000001.SH, 恒生指数HSI.HI，标普500 SPX.GI在列表内并置于列表开头
def indexTop(pre_list, fix):
    """
    对于三大指数在列表中位置的置顶变换
    :param pre_list: 原代码列表，可能包含或部分包含三大指数，排序不固定
    :param fix: 是否要求一定出现三大指数，如果是那么无论原列表是否包含三大指数都会置顶；反之仅仅置顶
    原包含的指数
    :return: 修改后的列表，特别注意在传参的时候至少浅复制列表而不能直接传形参
    """
    if fix:
        pre_list.append(sh)
        pre_list.append(hsi)
        pre_list.append(spx)
        # 保证存在并去重
        pre_list = list(set(pre_list))
        # 从列表中拿出后置于列表头部
        pre_list.remove(sh)
        pre_list.remove(hsi)
        pre_list.remove(spx)
        pre_list.insert(0, sh)
        pre_list.insert(1, hsi)
        pre_list.insert(2, spx)
        return pre_list
    else:
        chg = []
        for ii in [sh, hsi, spx]:
            if ii in pre_list:
                chg.append(pre_list.index(ii))
        return chg


if __name__ == '__main__':
    reset_params()
    set_triggers()
    monitor = Monitor()
    monitor.check_dir()
    monitor.init()
    # for s in ["2018-11-07", "2018-11-08", "2018-11-09", "2018-11-12", "2018-11-13", "2018-11-14",
    #           "2018-11-15", "2018-11-16", "2018-11-19", "2018-11-20", "2018-11-21", "2018-11-22",
    #           "2018-11-23", "2018-11-26", "2018-11-27", "2018-11-28", "2018-11-29", "2018-11-30"]:
    monitor.daily1()
    monitor.set_sche()
    # monitor.daily2()



















