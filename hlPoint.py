# -*- coding:utf-8 -*-
# ! python3
from constant import *
import numpy as np
from copy import copy



class HLPoint:
    def __init__(self, klist, code, thresh=THRESH_D):
        self.klist = klist
        self.code = code
        self.thresh = thresh
        self.hpi = []
        self.lpi = []
        self.confirm_p = []
        self.cursor = 0
        self.hl = None
        self.temp_max = 0
        self.temp_min = 0
        self.temp_h = 0
        self.temp_l = 0
        self.space_h = 0.0
        self.space_l = 0.0
        self.use_space = False

    def init_hl(self):
        flag = True
        jj = 0
        while flag:
            if self.klist[jj + 1].high >= self.klist[jj].high and \
                self.klist[jj + 1].high > self.klist[jj + 2].high:
                self.temp_h = jj
                self.hl = "h"
                self.temp_min = jj
                self.klist[jj].temp_h = jj
                self.klist[jj].hl = "h"
                self.klist[jj].temp_min = jj
                self.cursor = jj + 1
                flag = False
            elif self.klist[jj + 1].low <= self.klist[jj].low and \
                self.klist[jj + 1].low < self.klist[jj + 2].low:
                self.temp_l = jj
                self.hl = "l"
                self.temp_max = jj
                self.klist[jj].temp_l = jj
                self.klist[jj].hl = "l"
                self.klist[jj].temp_max = jj
                self.cursor = jj + 1
                flag = False
            else:
                jj += 1

    @staticmethod
    def step_hl_s(hl, high, low, temp_hl, temp_m,
                  from_hl, from_temp, pre_high,
                  pre_low, use_space, space_h,
                  space_l, l2h, h2l):

        is_high = False
        is_low = False

        if hl:
            if high > temp_hl:
                temp_hl = high
                temp_m = low
                from_hl += from_temp + 1
                from_temp = 0
            else:
                from_temp += 1
                if low < temp_m:
                    temp_m = low
                    if space_h and round((temp_m - temp_hl) / temp_hl, 2) < - space_h * AVG_BUFFER:
                        use_space = 1
                if (use_space or from_temp >= THRESH_D or temp_m < pre_low) and temp_m == low:
                    is_high = True
                    hl = 0
                    pre_high = temp_hl
                    temp_hl = temp_m
                    temp_m = high
                    from_hl = 0
                    from_temp = 0
                    use_space = 0
                    if len(l2h) > AVG_N:
                        space_l = round(np.mean(list(map(lambda x, y: (x - y) / y,
                                                      [k[1] for k in l2h[-AVG_N:]],
                                                      [k[0] for k in l2h[-AVG_N:]]))).item(), 3)
                        if space_l == np.nan:
                            space_l = 0.0
        else:
            if low < temp_hl:
                temp_hl = low
                temp_m = high
                from_hl += from_temp + 1
                from_temp = 0
            else:
                from_temp += 1
                if high > temp_m:
                    temp_m = high
                    if space_l and (temp_m - temp_hl) / temp_hl > space_l * AVG_BUFFER:
                        use_space = 1
                if (use_space or from_temp >= THRESH_D or temp_m > pre_high) and temp_m == high:
                    is_low = True
                    hl = 1
                    pre_low = temp_hl
                    temp_hl = temp_m
                    temp_m = low
                    from_hl = 0
                    from_temp = 0
                    use_space = 0
                    if len(h2l) > AVG_N:
                        space_h = round(np.mean(list(map(lambda x, y: (x - y)/ x,
                                                      [k[0] for k in h2l],
                                                      [k[1] for k in h2l]))).item(), 3)
                        if space_h == np.nan:
                            space_h = 0.0
        if hl and from_hl + from_temp >= WAIT_DTO30:
            lev_chg_signal = True
        else:
            lev_chg_signal = False
        return {"hl": hl, "temp_hl": temp_hl,
                "temp_m": temp_m, "from_hl": from_hl,
                "from_temp": from_temp, "use_space": use_space,
                "space_h": space_h, "space_l": space_l,
                "is_high": is_high, "is_low": is_low,
                "lev_chg_signal": lev_chg_signal,
                "pre_high": pre_high, "pre_low": pre_low}


    def step_hl(self, wait_thresh=WAIT_DTO30):
        if self.cursor < len(self.klist):
            self.klist[self.cursor].hpi = copy(self.hpi)
            self.klist[self.cursor].lpi = copy(self.lpi)
            self.klist[self.cursor].hl = self.hl
            self.klist[self.cursor].temp_l = self.temp_l
            self.klist[self.cursor].temp_h = self.temp_h
            self.klist[self.cursor].temp_min = self.temp_min
            self.klist[self.cursor].temp_max = self.temp_max
            if self.hl == "h":
                if self.klist[self.cursor].high > self.klist[self.temp_h].high:
                    self.temp_h = self.cursor
                    self.temp_min = self.cursor
                    self.klist[self.cursor].temp_h = self.temp_h
                    self.klist[self.cursor].temp_min = self.temp_min

                else:
                    self.klist[self.cursor].use_space = self.use_space
                    if self.klist[self.cursor].low < self.klist[self.temp_min].low:
                        self.temp_min = self.cursor
                        self.klist[self.cursor].temp_min = self.temp_min
                        if self.space_h and \
                                round((self.klist[self.temp_min].low -
                                       self.klist[self.temp_h].high) / self.klist[self.temp_h].high, 2) \
                                < -self.space_h * AVG_BUFFER:
                            self.use_space = True
                            self.klist[self.cursor].use_space = self.use_space
                    if (self.use_space or self.temp_min - self.temp_h >= self.thresh or
                            len(self.lpi) and self.klist[self.temp_min].low < self.klist[self.lpi[-1]].low) and\
                            self.temp_min == self.cursor:
                        self.hpi.append(self.temp_h)
                        self.klist[self.temp_h].hl_confirmed = self.cursor
                        self.klist[self.cursor].confirm_hl = self.temp_h
                        self.confirm_p.append(self.cursor)
                        self.hl = "l"
                        self.klist[self.cursor].hl = 'l'
                        self.temp_l = self.temp_min
                        self.klist[self.cursor].temp_l = self.temp_l
                        self.temp_max = self.cursor
                        self.klist[self.cursor].temp_max = self.temp_max
                        self.use_space = False
                        self.klist[self.cursor].hpi = copy(self.hpi)
                        l2h = self.l2h()
                        if len(l2h) >= AVG_N:
                            self.space_l = round(np.mean(list(map(lambda x, y: (self.klist[
                                                                                  x].high-self.klist[y].low)/self.klist[y].low,
                                               [k[1] for k in l2h[-AVG_N:]], [k[0] for k in
                                                                                   l2h[
                                                                                   -AVG_N:]]))).item(), 3)
                            if self.space_l == np.nan:
                                self.space_l = 0.0

            else:
                if self.klist[self.cursor].low < self.klist[self.temp_l].low:
                    self.temp_l = self.cursor
                    self.temp_max = self.cursor
                    self.klist[self.cursor].temp_l = self.temp_l
                    self.klist[self.cursor].temp_max = self.temp_max
                else:
                    self.klist[self.cursor].use_space = self.use_space
                    if self.klist[self.cursor].high > self.klist[self.temp_max].high:
                        self.temp_max = self.cursor
                        self.klist[self.cursor].temp_max = self.temp_max
                        if self.space_l and \
                                (self.klist[self.temp_max].high -
                                 self.klist[self.temp_l].low) / self.klist[self.temp_l].low > \
                                self.space_l*AVG_BUFFER:
                            self.use_space = True
                            self.klist[self.cursor].use_space = self.use_space
                    if (self.use_space or self.temp_max - self.temp_l >= self.thresh or
                        len(self.hpi) and self.klist[self.temp_max].high > self.klist[self.hpi[-1]].high) and\
                            self.temp_max == self.cursor:
                        self.lpi.append(self.temp_l)
                        self.klist[self.temp_l].hl_confirmed = self.cursor
                        self.klist[self.cursor].confirm_hl = self.temp_l
                        self.confirm_p.append(self.cursor)
                        self.hl = "h"
                        self.klist[self.cursor].hl = 'h'
                        self.temp_h = self.temp_max
                        self.klist[self.cursor].temp_h = self.temp_h
                        self.temp_min = self.cursor
                        self.klist[self.cursor].temp_min = self.temp_min
                        self.use_space = False
                        self.klist[self.cursor].lpi = copy(self.lpi)
                        h2l = self.h2l()
                        if len(h2l) >= AVG_N:
                            self.space_h = round(np.mean(list(map(lambda x, y: (self.klist[
                                                                                  x].high-self.klist[y].low) /
                                                                            self.klist[x].high,
                                               [k[0] for k in h2l[-AVG_N:]], [k[1] for k in h2l[
                                                                                            -AVG_N:]]))).item(), 3)
                            if self.space_h == np.nan:
                                self.space_h = 0.0
            if len(self.lpi) and self.hl == "h" and \
                    self.cursor - self.klist[self.cursor].lpi[-1] >= wait_thresh:
                lev_chg_signal = True
            else:
                lev_chg_signal = False
            self.cursor += 1
            return lev_chg_signal

    def l2h(self):
        l2h = []
        hpi = self.hpi
        lpi = self.lpi
        if len(hpi) and len(lpi):
            if lpi[0] > hpi[0]:
                hpi = hpi[1:]
            n = min(len(hpi), len(lpi))
            for i in range(n):
                l2h.append((lpi[i], hpi[i]))
        return l2h

    def h2l(self):
        h2l = []
        hpi = self.hpi
        lpi = self.lpi
        if len(hpi) and len(lpi):
            if hpi[0] > lpi[0]:
                lpi = lpi[1:]
            n = min(len(hpi), len(lpi))
            for i in range(n):
                h2l.append((hpi[i], lpi[i]))
        return h2l

    def get_hl(self):
        while self.cursor < len(self.klist):
            self.step_hl()


if __name__ == "__main__":
    from loadData import *
    klist=loadData_daily()
    hlp_env = HLPoint(klist, "600519.SH")
    hlp_env.init_hl()
    while hlp_env.cursor < len(hlp_env.klist):
        hlp_env.step_hl()
    print(f"high points index:{hlp_env.hpi}")
    print(f"low points index:{hlp_env.lpi}")