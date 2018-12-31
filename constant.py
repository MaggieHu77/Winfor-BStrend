# -*- coding: utf-8 -*-
# ! python3

"""
定义默认的重要参数，此处定义参数皆可用户自定义
"""
# 日线结构高低点间隔
THRESH_D = 13
# 30min结构高低点
THRESH_30 = 16
# 5min结构高低点
THRESH_5 = 18
# 以前N次回调或反弹幅度均值为判定高低点的限制
AVG_N = 3
# 前N次回调或反弹幅度均值调和参数
AVG_BUFFER = 1
# 空间趋势转换最小间隔
TREND_REV = 65
# 日线上买点最高涨幅限制
MAX_UPFLOAT = 0.05
# 日线转入30min级别最小等待时间
WAIT_DTO30 = 55
# 30min级别转入5min级别最小等待时间
WAIT_30TO5 = 65
# 适用止盈点的浮盈最低要求
THRESH_PROFIT = 0.15
# 满足最低浮盈后止损时收益
THRESH_STOPPROFIT = 0.05
# 每日30minK线个数
N_30 = 8
# 每30min含5minK线个数
N_5 = 6
# K线级别
K_LEV_DICT = {1: "daily", 2: "30min", 3: "5min"}
# 交易类型
BUYSELL_TYPE = {"B1-0": ("B", 1, 0, "30min第一买点"),
              "B1-1": ("B", 1, 1, "日线上第一买点"),
              "B2-0": ("B", 2, 0, "30min第二买点"),
              "B2-1": ("B", 2, 1, "日线上第二买点"),
              "B3-0": ("B", 3, 0, "30min第三买点"),
              "B3-1": ("B", 3, 1, "日线上第三买点"),
              "S1": ("S", 1, "跌破日线前低点卖出"),
              "S2": ("S", 2, "按照买点的止损点卖出"),
              "S3": ("S", 3, "浮盈止盈点卖出"),
              "S4": ("S", 4, "跌破30min级别前低点卖出"),
              "S5": ("S", 5, "跌破5min级别前低点卖出")}
BEGIN_DATE = '20150930'
END_DATE = '20180930'
# 初始资金，单位（百元）
INIT_FUND = 10000
BUY1_PCT = 0.4
BUY2_PCT = 0.6
MIN30_STR = [" 10:00:00", " 10:30:00", " 11:00:00", " 11:30:00",
             " 13:30:00", " 14:00:00", " 14:30:00", " 15:00:00"]
MIN5_STR = [[" 09:35:00", " 09:40:00", " 09:45:00", " 09:50:00", " 09:55:00", " 10:00:00"],
            [" 10:05:00", " 10:10:00", " 10:15:00", " 10:20:00", " 10:25:00", " 10:30:00"],
            [" 10:35:00", " 10:40:00", " 10:45:00", " 10:50:00", " 10:55:00", " 11:00:00"],
            [" 11:05:00", " 11:10:00", " 11:15:00", " 11:20:00", " 11:25:00", " 11:30:00"],
            [" 13:05:00", " 13:10:00", " 13:15:00", " 13:20:00", " 13:25:00", " 13:30:00"],
            [" 13:35:00", " 13:40:00", " 13:45:00", " 13:50:00", " 13:55:00", " 14:00:00"],
            [" 14:05:00", " 14:10:00", " 14:15:00", " 14:20:00", " 14:25:00", " 14:30:00"],
            [" 14:35:00", " 14:40:00", " 14:45:00", " 14:50:00", " 14:55:00", " 15:00:00"]]
# 降级别操作中首次取出30min K线的个数， 30d
LEN_K30 = 240
# 降级别操作中首次取出5min K线的个数, 10d
LEN_K5 = 480
# 发信邮箱
SENDER = ""
# 发信邮箱密码
SENDER_KEY = ""
# 收信邮箱
RECEIVER = ""
# 文件地址
CODE_FILE = ""
# 工作文件夹
WORK = ""
# 数据库地址
DATABASE = ""
GRAPH = ""
FREQ = 1
PAINT = ""
SET_T = ""



def reset_params():
    from configparser import ConfigParser
    import inspect
    parser = ConfigParser()
    parser.read("config.conf", encoding="utf-8-sig")
    secs = parser.sections()
    for sec in secs:
        opts = parser.options(sec)
        for opt in opts:
            v = parser.get(sec, opt)
            exec(f"{opt.upper()}={v}", inspect.currentframe().f_back.f_locals)
            # is_int = v.isdigit()
            # if is_int:
            #     exec(f"{opt.upper()}={v}")
            # else:
            #     exec(f"{opt.upper()}='{v}'")

if __name__ == "__main__":
    reset_params()
    print(CODE_FILE)



