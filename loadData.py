# -*- coding:utf-8 -*-
# ! python3

from WindPy import w
from datetime import date as dd
from K import K
from constant import *
from defindex import Kti
from numpy import nan
from defindex import get_kti_seq


class loaddataError(Exception):
    def __init__(self, msg):
        self.errorinfo = msg

    def __str__(self):
        return self.errorinfo


def loadData_daily(begin_date=BEGIN_DATE, stockname='600519.SH',
                   end_date=END_DATE):
    if not w.isconnected():
        w.start()

    res = w.wsd(stockname, "high, low, close, trade_status", begin_date, end_date,
                'priceadj=F', showblank=0)
    is_index = w.wss(stockname, 'windtype').Data[0][0] == "股票指数"
    K_list = []
    if res.ErrorCode != 0:
        #print(stockname + " load daily K info Error: wsd - " +
         #     str(res.ErrorCode))
        # 这里抛出定义的异常，能够在调动的上层捕捉，以防程序异常停止
        raise loaddataError(stockname + 'load data from Wind error: ' +
                            res.ErrorCode)

    for jj in range(len(res.Data[0])):
        if not is_index and res.Data[3][jj] == "停牌一天":
            continue
        if jj >= 1:
            res.Data[0][jj] = (res.Data[0][jj] or res.Data[0][jj - 1])
            res.Data[1][jj] = (res.Data[1][jj] or res.Data[1][jj - 1])
            res.Data[2][jj] = (res.Data[2][jj] or res.Data[2][jj - 1])
        if not res.Data[0][jj] or not \
                res.Data[1][jj] or not res.Data[2][jj]:
            continue
        temp_time = res.Times[jj].strftime("%Y-%m-%d")
        k = K(time=temp_time, high=round(res.Data[0][jj], 2),
              low=round(res.Data[1][jj], 2), close=round(res.Data[2][jj], 2),
              i=Kti(8, jj, 7, 5), lev=1)
        K_list.append(k)
    return K_list









