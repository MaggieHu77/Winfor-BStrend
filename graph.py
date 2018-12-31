# -*- coding:utf-8 -*-
# ! python3

from hlPoint import HLPoint
from trend import Trend, TrendError
from pandas import DataFrame, DatetimeIndex, to_datetime
import matplotlib.pyplot as plt
import numpy as np
from time import strftime, localtime, time
from datetime import date
from dateutil.relativedelta import relativedelta
from matplotlib.dates import AutoDateLocator, DateFormatter
import locale
from loadData import loaddataError, loadData_daily as ldd
from WindPy import w
from constant import *


class BSgraph(object):
    def __init__(self, hlist, llist, data, note, codename):
        """
        策略绘图对象的创建函数

        :param hlist: 高点index list
        :param llist: 低点index list
        :param data: 策略运行后的K线数据
        """
        self.hlist = hlist
        self.llist = llist
        self.data = data
        self.gdir = None  # 作图地址
        self.note = note
        self.codename = codename

    def performance(self,
                    trdchg,
                    dir="",
                    star=False):
        """
        绘图展现回测期内的高低点和趋势变化

        :param codename: 回测股票代码或名称
        :param dir: 图像存放文件夹地址
        :return: 返回图像文件.jpg
        """
        main_df = DataFrame(columns=['date', 'high', 'low', 'close', 'trd'])
        for kk in range(len(self.data)):
            main_df.loc[kk] = [self.data[kk].t, self.data[kk].high,
                               self.data[kk].low, self.data[kk].close, self.data[kk].trd]
        # 以时间为索引
        main_df.index = DatetimeIndex(to_datetime(main_df['date']))
        # 确保升序排列
        main_df.sort_index(ascending=True, inplace=True)

        # 绘图设置部分
        plt.figure(facecolor="white", frameon=True, figsize=(28,15), dpi=200)
        plt.suptitle(self.codename + u"择时策略：高低点及趋势", size=33)
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        # 提取上升趋势
        up = np.ma.masked_where(
            main_df['trd'].values != 'up', main_df['close'].values
        )
        # 提取下降趋势
        down = np.ma.masked_where(
            main_df['trd'].values != 'down', main_df['close'].values
        )
        # 提取盘整趋势
        consd = np.ma.masked_where(
            main_df['trd'].values != 'consd', main_df['close'].values
        )
        # 提取不能判定趋势部分
        na = np.ma.masked_where(
            main_df['trd'].values, main_df['close'].values
        )

        # 画出各个趋势部分的线
        upline, = plt.plot(
            main_df.index, up, color='red', linestyle='-', label='up'
        )
        downline, = plt.plot(
            main_df.index, down, color='green', linestyle='-', label='down'
        )
        consdline, = plt.plot(
            main_df.index, consd, color='orange', linestyle='-', label='consolidation'
        )
        naline, = plt.plot(
            main_df.index, na, color='grey', linestyle='-', label='unknown'
        )
        # 需要补齐趋势类型之间的空隙
        color_dict = {'up': "red", "down": "green", "consd": "orange", "None": "grey"}
        for ii in trdchg:
            plt.plot(main_df.index[ii-1:ii+1], main_df['close'][ii-1:ii+1],
                     color=color_dict[str(main_df['trd'][ii-1])], linestyle='-')
        # 设置时间标注距离高低点的距离
        scale_text = round(
            (main_df['close'].max() - main_df['close'].min()) / 15, 2
        )
        # 高点时间标注
        for hh in range(len(self.hlist)):
            plt.text(
                main_df.index[self.hlist[hh]],
                main_df.ix[self.hlist[hh], 'high'] + scale_text,
                main_df.index[self.hlist[hh]].strftime('%m-%d'),
                fontsize=14
            )
        # 低点时间标注
        for ll in range(len(self.llist)):
            plt.text(
                main_df.index[self.llist[ll]],
                main_df.ix[self.llist[ll], 'low'] - scale_text,
                main_df.index[self.llist[ll]].strftime('%m-%d'),
                fontsize=14
            )
        # 高低点记号标注
        high_p, = plt.plot(
            main_df.index[self.hlist], main_df.ix[self.hlist, 'high'], 'r^', markersize=12
        )
        low_p, = plt.plot(
            main_df.index[self.llist], main_df.ix[self.llist, 'low'], 'gv', markersize=12
        )
        if star:
            star_p, = plt.plot(
                main_df.index[-1], main_df.ix[-1, 'close'], 'r*', markersize=13
            )
            plt.text(
                main_df.index[-1], main_df.ix[-1, 'close'] + 0.5*scale_text, '现价:'+str(main_df.ix[
                                                              -1, 'close']), fontsize=14
            )
        # 图例
        plt.legend(
            (
                upline,
                downline,
                consdline,
                naline,
                high_p,
                low_p,
            ),
            (
                "up",
                "down",
                "consolidation",
                "unknown",
                "high point",
                "low point",
            ),
            loc="upper left",
            shadow=False,
            frameon=False,
            fontsize=16,
            facecolor="none",
        )
        # 网格线选项
        plt.grid(True, 'major')
        # x-axis
        plt.xlabel(u"时间", fontsize=18)
        plt.ylabel(u"价格", fontsize=18)
        # 坐标轴时间格式
        ax1 = plt.gca()
        ax1.xaxis.set_major_locator(AutoDateLocator())
        ax1.xaxis.set_major_formatter(DateFormatter("%Y-%m"))
        ax1.xaxis.set_tick_params(labelsize=14)
        ax1.yaxis.set_tick_params(labelsize=14)
        self.gdir = f"{dir}/BS_{self.codename}.png"
        # 保存图像
        plt.savefig(self.gdir)
        plt.close()
        return self.gdir

    def strategy_info(self, lasthl, space_h, space_l):
        """
        返回股票在总表中的观测信息
        :param lasthl: 最后一个高点或者低点的index
        :return: Strategy_s表中对应信息tuple
        """
        if not w.isconnected():
            w.start()
        name = w.wss(self.codename, "sec_name").Data[0][0]
        info = (self.data[-1].t, self.codename, name, self.data[-1].trd,
                self.note[0], [self.data[self.note[1]].low,
                               self.data[self.note[1]].high][self.note[0]],
                [self.data[self.note[2]].high, self.data[self.note[2]].low][self.note[0]],
                self.note[1]-lasthl, len(self.data)-self.note[1]-1, self.data[-1].use_space,
                space_h, space_l)
        return info


# 运行参数设置函数
def runbacktest(
        begin=BEGIN_DATE,
        codename="600519.SH",
        dir=GRAPH,
        end=END_DATE,
        paint=True,
        star=False
):
    """
    设置策略环境参数，并运行部分回测策略
    :param begin: 回测开始时间
    :param codename: 回测股票代码或名称
    :param thresh: 日线高低点间隔交易日长度
    :param dir: 作图目录地址
    :param end: 回测结束时间，默认当前
    :param bounceThresh: 严格下跌过程中反弹超过bounceThresh交易日确认上涨，默认为65天
    :param paint: bool值，是否画图，默认为True
    :param star: bool值，最后一个标记星星，默认为False
    :return: 返回策略环境对象整体和图像地址
    """
    print(f"BS日线策略：正在回测{codename}...")
    try:
        klist = ldd(begin, codename, end)
    except loaddataError as e:
        print(f"\t{e}")
    print(f"\t{codename}获取日K线数{len(klist)}")
    # 设置策略运行参数环境
    hlp_env = HLPoint(klist, codename)
    hlp_env.init_hl()
    hlp_env.get_hl()
    try:
        trd_env = Trend(hlp_env)
        trd_env.get_trend()
    except TrendError as e:
        print(e)
        return
    note = [[1, hlp_env.temp_h, hlp_env.temp_min],
            [0, hlp_env.temp_l, hlp_env.temp_max]][hlp_env.hl == "l"]
    locale.setlocale(locale.LC_CTYPE, "chinese")
    # 设置画图环境参数
    graph_obj = BSgraph(
        hlist=hlp_env.hpi,
        llist=hlp_env.lpi,
        data=hlp_env.klist,
        codename=codename,
        note=note
    )
    strategy_info = graph_obj.strategy_info(max(hlp_env.hpi[-1],
                                                hlp_env.lpi[-1]),
                                            hlp_env.space_h,
                                            hlp_env.space_l)
    print(f"\t{codename}当前趋势{trd_env.trdnow}")
    stock_info = []
    for hh in hlp_env.hpi:
        stock_info.append((hlp_env.klist[hh].t, "H",
                           hlp_env.klist[hh].high,
                           hlp_env.klist[hlp_env.klist[hh].hl_confirmed].t))
    for ll in hlp_env.lpi:
        stock_info.append((hlp_env.klist[ll].t, "L",
                           hlp_env.klist[ll].low,
                           hlp_env.klist[hlp_env.klist[ll].hl_confirmed].t))
    stock_info.sort()
    # 该股票在总表中的信息
    if paint:

        # 绘图并获取图像地址
        gdir = graph_obj.performance(
            trdchg=trd_env.trdchg,
            dir=dir,
            star=star,
        )
        return strategy_info, stock_info, gdir
    else:
        return strategy_info, stock_info


if __name__ == "__main__":
    runbacktest(begin="2015-09-30", codename="CSCO.O",
                dir="C:/Users/zhangchangsheng/Desktop/graph_trend",
                end='2018-12-03')





