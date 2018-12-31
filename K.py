# -*- coding: utf-8 -*-
# ! python3

"""
定义K线类父类模板
"""


class K:
    def __init__(self, high, low, close, i, lev, time, dhl=""):
        """
         创建K线实例
        #:param code: str股票代码
        :param high: float最高价
        :param low: float最低价
        :param close: float收盘价
        :param i: Kti序号标记
        :param lev: intK线级别
        :param time: str时间戳
        """
        #self.code = code
        self.high = high
        self.low = low
        self.close = close
        self.i = i
        self.lev = lev
        self.t = time
        self.hl = dhl  # 日线级别当前待判定高点还是低点
        self.hpi = []  # 本级别已出现的高点序号
        self.lpi = []  # 本级别已出现的低点序号
        self.temp_l = None
        self.temp_h = None
        self.temp_min = None
        self.temp_max = None
        self.use_space = False  # 是否满足空间高低点判定条件
        self.bs_info = None
        self.trd = None
        self.pre_trd = None
        self.hl_confirmed = None
        self.confirm_hl = None

    def add_hpi(self, hpi):
        self.hpi = hpi

    def add_lpi(self, lpi):
        self.lpi = lpi

    def trade_info(self, trd_idx, typ, price, volume, stop_p):
        """
        记录交易信息
        :param trd_idx: 交易操作序号
        :param typ: 交易类型
        :param price: 成交价格
        :param volume: 交易量（手）
        :param stop_p: 可能的止损止盈价位
        :return:
        """
        self.bs_info = {"trd_idx": trd_idx, "type": typ, "price": price,
                         "volume": volume, "stop_p": stop_p, "lev": self.lev}






