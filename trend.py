# -*- coding:utf-8 -*-
# ! python3

from constant import *


class TrendError(Exception):
    def __init__(self, msg="Undecidable trend; Need more high or low points to decide trend"):
        self.errorinfo = msg

    def __str__(self):
        return self.errorinfo


class Trend:
    def __init__(self, hlp_env):
        self.hlp_env = hlp_env
        self.cursor = 0
        self.trdchg = []
        self.trdnow = None

    def init_trd(self):
        if len(self.hlp_env.hpi) + len(self.hlp_env.lpi) < 4:
            raise TrendError(f"TrendError:{self.hlp_env.code}高低点个数不足，无法继续策略已被忽略")
        else:
            if self.hlp_env.hpi[0] > self.hlp_env.lpi[0]:
                if self.hlp_env.klist[self.hlp_env.lpi[1]].low > self.hlp_env.klist[self.hlp_env.lpi[0]].low:
                    self.cursor = self.hlp_env.klist[self.hlp_env.lpi[1]].hl_confirmed
                    self.hlp_env.klist[self.cursor].trd = 'up'
                    self.trdchg.append(self.cursor)
                    self.trdnow = 'up'
                else:
                    self.cursor = self.hlp_env.klist[self.hlp_env.lpi[1]].hl_confirmed
                    self.hlp_env.klist[self.cursor].trd = 'consd'
                    self.trdchg.append(self.cursor)
                    self.trdnow = 'consd'

            else:
                if self.hlp_env.klist[self.hlp_env.hpi[1]].high < self.hlp_env.klist[self.hlp_env.hpi[0]].high:
                    self.cursor = self.hlp_env.klist[self.hlp_env.hpi[1]].hl_confirmed
                    self.hlp_env.klist[self.cursor].trd = 'down'
                    self.trdchg.append(self.cursor)
                    self.trdnow = 'down'
                else:
                    self.cursor = self.hlp_env.klist[self.hlp_env.hpi[1]].hl_confirmed
                    self.hlp_env.klist[self.cursor].trd = 'consd'
                    self.trdchg.append(self.cursor)
                    self.trdnow = 'consd'
            self.cursor += 1

    @staticmethod
    def step_trdmax_s(hl, low, high, from_temp, from_hl, temp_hl, trd):
        flag = False
        if not hl and trd != 'down':
            if from_temp + from_hl >= TREND_REV:
                if low <= temp_hl:
                    trd = 'down'
                    flag = True
        elif hl and trd != 'up':
            if from_temp + from_hl >= TREND_REV:
                if high >= temp_hl:
                    trd = 'up'
                    flag = True
        return trd, flag

    def step_trdmax(self):
        flag = False
        if self.hlp_env.klist[self.cursor].hl == 'l' and self.trdnow != 'down':
            pre_h = self.hlp_env.klist[self.cursor].hpi[-1]
            if self.cursor - pre_h >= TREND_REV:
                interval = [ii.low for ii in self.hlp_env.klist[pre_h: (self.cursor + 1)]]
                if self.cursor == interval.index(min(interval)) + pre_h:
                    self.hlp_env.klist[self.cursor].pre_trd = self.trdnow
                    self.trdnow = 'down'
                    self.trdchg.append(self.cursor)
                    self.hlp_env.klist[self.cursor].trd = 'down'
                    flag = True
                    self.cursor += 1
        elif self.hlp_env.klist[self.cursor].hl == 'h' and self.trdnow != 'up':
            pre_l = self.hlp_env.klist[self.cursor].lpi[-1]
            if self.cursor - pre_l >= TREND_REV:
                interval = [ii.high for ii in self.hlp_env.klist[pre_l: (self.cursor + 1)]]
                if self.cursor == interval.index(max(interval)) + pre_l:
                    self.hlp_env.klist[self.cursor].pre_trd = self.trdnow
                    self.trdnow = 'up'
                    self.trdchg.append(self.cursor)
                    self.hlp_env.klist[self.cursor].trd = 'up'
                    flag = True
                    self.cursor += 1
        return flag


    @staticmethod
    def step_trd_s(trd, hl, low, high, pre_low, pre_high, pre2_low, pre2_high):
        if trd == "up" and hl:
            if low < pre_low:
                trd = "consd"
        elif trd =="up" and not hl:
            if low < pre_low:
                if pre_high < pre2_high:
                    trd = 'down'
                else:
                    trd = "consd"
        elif trd == 'down' and not hl:
            if high > pre_high:
                trd = 'consd'
        elif trd == 'down' and hl:
            if high > pre_high:
                if pre_low > pre2_low:
                    trd = 'up'
                else:
                    trd = 'consd'
        elif trd == 'consd' and hl:
            if pre_low > pre2_low:
                if high > pre_high:
                    trd = "up"
        elif trd == 'consd' and not hl:
            if pre_high < pre2_high:
                if low < pre_low:
                    trd = 'down'
        return trd

    def step_trd(self):
        if self.trdnow =='up' and self.hlp_env.klist[self.cursor].hl == 'h':
            if self.hlp_env.klist[self.cursor].low < self.hlp_env.klist[self.hlp_env.klist[self.cursor].lpi[-1]].low:
                self.trdchg.append(self.cursor)
                self.hlp_env.klist[self.cursor].trd = 'consd'
                self.hlp_env.klist[self.cursor].pre_trd = self.trdnow
                self.trdnow = 'consd'
            else:
                self.hlp_env.klist[self.cursor].trd = self.trdnow
                self.hlp_env.klist[self.cursor].pre_trd = self.hlp_env.klist[self.cursor - 1].pre_trd
        elif self.trdnow == 'up' and self.hlp_env.klist[self.cursor].hl == 'l':
            if self.hlp_env.klist[self.cursor].low < self.hlp_env.klist[self.hlp_env.klist[self.cursor].lpi[-1]].low:
                if self.hlp_env.klist[self.hlp_env.klist[self.cursor].hpi[-1]].high < \
                    self.hlp_env.klist[self.hlp_env.klist[self.cursor].hpi[-2]].high:
                    self.hlp_env.klist[self.cursor].trd = 'down'
                    self.hlp_env.klist[self.cursor].pre_trd = self.trdnow
                    self.trdchg.append(self.cursor)
                    self.trdnow = 'down'
                else:
                    self.hlp_env.klist[self.cursor].trd = 'consd'
                    self.trdchg.append(self.cursor)
                    self.hlp_env.klist[self.cursor].pre_trd = self.trdnow
                    self.trdnow = 'consd'
            else:
                self.hlp_env.klist[self.cursor].trd = self.trdnow
                self.hlp_env.klist[self.cursor].pre_trd = self.hlp_env.klist[self.cursor - 1].pre_trd
        elif self.trdnow == 'down' and self.hlp_env.klist[self.cursor].hl == 'l':
            if self.hlp_env.klist[self.cursor].high > self.hlp_env.klist[self.hlp_env.klist[self.cursor].hpi[-1]].high:
                self.trdchg.append(self.cursor)
                self.hlp_env.klist[self.cursor].trd = 'consd'
                self.hlp_env.klist[self.cursor].pre_trd = self.trdnow
                self.trdnow = 'consd'
            else:
                self.hlp_env.klist[self.cursor].trd = self.trdnow
                self.hlp_env.klist[self.cursor].pre_trd = self.hlp_env.klist[self.cursor - 1].pre_trd
        elif self.trdnow == 'down' and self.hlp_env.klist[self.cursor].hl == 'h':
            if self.hlp_env.klist[self.cursor].high > self.hlp_env.klist[self.hlp_env.klist[self.cursor].hpi[-1]].high:
                if self.hlp_env.klist[self.hlp_env.klist[self.cursor].lpi[-1]].low > \
                    self.hlp_env.klist[self.hlp_env.klist[self.cursor].lpi[-2]].low:
                    self.hlp_env.klist[self.cursor].trd = 'up'
                    self.hlp_env.klist[self.cursor].pre_trd = self.trdnow
                    self.trdnow = 'up'
                    self.trdchg.append(self.cursor)
                else:
                    self.hlp_env.klist[self.cursor].trd = 'consd'
                    self.trdchg.append(self.cursor)
                    self.hlp_env.klist[self.cursor].pre_trd = self.trdnow
                    self.trdnow = 'consd'
            else:
                self.hlp_env.klist[self.cursor].trd = self.trdnow
                self.hlp_env.klist[self.cursor].pre_trd = self.hlp_env.klist[self.cursor - 1].pre_trd
        elif self.trdnow == 'consd' and self.hlp_env.klist[self.cursor].hl == 'h':
            if self.hlp_env.klist[self.hlp_env.klist[self.cursor].lpi[-1]].low > \
                self.hlp_env.klist[self.hlp_env.klist[self.cursor].lpi[-2]].low:
                if self.hlp_env.klist[self.cursor].high > \
                    self.hlp_env.klist[self.hlp_env.klist[self.cursor].hpi[-1]].high:
                    self.hlp_env.klist[self.cursor].trd = 'up'
                    self.trdchg.append(self.cursor)
                    self.hlp_env.klist[self.cursor].pre_trd = self.trdnow
                    self.trdnow = 'up'
                else:
                    self.hlp_env.klist[self.cursor].trd = self.trdnow
                    self.hlp_env.klist[self.cursor].pre_trd = self.hlp_env.klist[self.cursor - 1].pre_trd
            else:
                self.hlp_env.klist[self.cursor].trd = self.trdnow
                self.hlp_env.klist[self.cursor].pre_trd = self.hlp_env.klist[self.cursor - 1].pre_trd
        elif self.trdnow == 'consd' and self.hlp_env.klist[self.cursor].hl == 'l':
            if self.hlp_env.klist[self.hlp_env.klist[self.cursor].hpi[-1]].high < \
                self.hlp_env.klist[self.hlp_env.klist[self.cursor].hpi[-2]].high:
                if self.hlp_env.klist[self.cursor].low < \
                    self.hlp_env.klist[self.hlp_env.klist[self.cursor].lpi[-1]].low:
                    self.hlp_env.klist[self.cursor].trd = 'down'
                    self.trdchg.append(self.cursor)
                    self.hlp_env.klist[self.cursor].pre_trd = self.trdnow
                    self.trdnow = 'down'
                else:
                    self.hlp_env.klist[self.cursor].trd = self.trdnow
                    self.hlp_env.klist[self.cursor].pre_trd = self.hlp_env.klist[self.cursor - 1].pre_trd
            else:
                self.hlp_env.klist[self.cursor].trd = self.trdnow
                self.hlp_env.klist[self.cursor].pre_trd = self.hlp_env.klist[self.cursor - 1].pre_trd
        self.cursor += 1

    def get_trend(self):
        self.init_trd()
        while self.cursor < len(self.hlp_env.klist):
            res = self.step_trdmax()
            if not res:
                self.step_trd()


