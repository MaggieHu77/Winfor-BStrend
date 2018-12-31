# -*- coding: utf-8 -*-
# ! python3

"""
定义K线时间类，及其转换关系
"""
from constant import *


class Kti:
    O = (0, 0, -1)  # K线时间原点表示

    def __init__(self, n_30=N_30, *i):
        self.kti = i   # 如果*i没有赋值，那么为（）的空tuple
        self.n_30 = n_30
        if len(self.kti) == 2:
            self.kti += (N_5 - 1,)
        elif len(self.kti) == 1:
            self.kti += (n_30 - 1, N_5 - 1)
        elif len(self.kti) == 0:
            self.kti += self.O   # 时间原点

    def __bool__(self):
        """
        重定义bool值，除原点外都是True
        :return: bool
        """
        return bool(self.value())

    def __gt__(self, kti):
        """
        重定义">"比较运算符
        :param kti: 比较对象
        :return: bool
        """
        if not isinstance(kti, self.__class__):  # self代表本实例，self.__class__代表本类
            return False
        elif self.value() > kti.value():
            return True
        else:
            return False

    def __eq__(self, kti):
        """
        重定义"=="比较运算符
        :param kti: 比较对象
        :return: bool
        """
        if not isinstance(kti, self.__class__):
            return False
        elif self.value() == kti.value():
            return True
        else:
            return False

    def __lt__(self, kti):
        """
        重定义"<"比较运算符
        :param kti: 比较对象
        :return: bool
        """
        if not isinstance(kti, self.__class__):
            return False
        elif self.value() < kti.value():
            return True
        else:
            return False

    def __le__(self, kti):
        """
        重定义"<="比较运算符
        :param kti: 比较对象
        :return: bool
        """
        if self.__lt__(kti) or self.__eq__(kti):
            return True
        else:
            return False

    def __ge__(self, kti):
        """
        重定义">="比较运算符
        :param kti: 比较对象
        :return: bool
        """
        if self.__gt__(kti) or self.__eq__(kti):
            return True
        else:
            return False

    def __add__(self, other):
        """
        重定义"+"运算符
        :param other: RHS运算对象
        :return: Kti object
        """
        if isinstance(other, Kn):
            if other.lev == 1:
                delta = (other.n, 0, 0)
            elif other.lev == 2:
                delta = (0, other.n, 0)
            else:
                delta = (0, 0, other.n)
        elif isinstance(other, self.__class__):
            delta = other.scalar_sub(self.O)
        else:
            delta = (other[0], other[1], other[2] + 1)
        v = self.value(self.scalar_add(delta))
        kti = Kti(self.n_30, *self.inv_value(v))
        return kti

    def __radd__(self, other):
        """
        重定义"+"运算符
        :param other: LHS运算对象
        :return: Kpi object
        """
        return self.__add__(other)

    def __sub__(self, other):
        """
        重定义"-"运算符
        :param other: RHS运算对象
        :return: Kpi object, tuple
        """
        if isinstance(other, Kn):
            if other.lev == 1:
                delta = (other.n, 0, 0)  # 实例不能直接加减，必须用其value值进行运算后inverse
            elif other.lev == 2:
                delta = (0, other.n, 0)  # 实例与增量可以进行scalar加减，
                # 但是需要以value进行inverse来标准化形式
            else:
                delta = (0, 0, other.n)
            v = self.value(self.scalar_sub(delta))
            kti = Kti(self.n_30, *self.inv_value(v))
        elif isinstance(other, self.__class__):  # 两个实例相减，得到的不是实例而是value值，
            # 调用Kn.v_to_kn()的静态方法能够得到对应单位的差
            kti = (self.value(), other.value())
        else:
            kti = Kti(self.n_30, *other)  # 如果给的是tuple不是实例
            # 不是正确使用方法，但是将其当作是实例，返回的是value的差
            # 调用Kn.v_to_kn()的静态方法能够得到对应单位的差
            kti = (self.value(), kti.value())
        return kti

    def __rsub__(self, other):
        """
        重定义"-"运算符
        :param other: LHS运算对象
        :return: Kpi object, tuple
        """
        return self.__sub__(other)

    def scalar_add(self, other):
        """
        元素对元素位加法
        :param other: 对应元素
        :return: tuple
        """
        return (self.kti[0] + other[0],
                self.kti[1] + other[1],
                self.kti[2] + other[2])

    def scalar_sub(self, other):
        """
        元素对元素位减法
        :param other: 对应元素
        :return: tuple
        """
        return (self.kti[0] - other[0],
                self.kti[1] - other[1],
                self.kti[2] - other[2])

    def value(self, *kti):
        """
        Kpi object的值
        :param kti: tuple
        :return: int value
        """
        if not kti:
            kti = self.kti
        else:
            kti = kti[0]
        return kti[0] * self.n_30 * N_5 + \
               kti[1] * N_5 + kti[2] + 1

    @staticmethod
    def inv_value(self, v, n_30):
        """
        Kpi标准化表达形式的tuple kpi
        :param v: Kpi object的value
        :return: tuple kpi
        """
        from math import floor
        kti = (floor((v - 1) / n_30 / N_5),)
        kti += (floor(((v - 1) % (n_30 * N_5)) / N_5), )
        kti += (((v - 1) % (n_30 * N_5)) % N_5,)
        return kti


def get_kti_seq(seq, init_p, n_30, value):
    """
    helper function将自然序列排序的分钟级别数据转化为Kti实例index

    :param seq: 自然序列编号
    :param init_p: 设定第一个点的Kti格式编号
    :param n_30: 一个交易日中有n_30个30min数据
    :param value: 一个数据单位的Kti值，30min数据为N_5, 5min数据为1，日线数据为n_30*N_5
    :return:
    """
    o = Kti(n_30, init_p)
    o_v = o.value()
    seq_v = map(lambda x: o_v + x *value, seq)
    seq_kti = map(Kti.inv_value, seq_v)
    seq_kti = [Kti(n_30, kti) for kti in seq_kti]
    return seq_kti


class Kn:
    def __init__(self, n, lev):
        self.n = n
        self.lev = lev

    @staticmethod
    def v_to_kn(v, lev, n_30=N_30):
        from math import floor
        den = [n_30 * N_5, N_5, 1]
        return floor(v[0] / den[lev - 1]) - floor(v[1] / den[lev - 1])


# unit test
if __name__ == "__main__":
    t1 = Kti(8,2,5,2)
    t2 = Kti(8,5,1,0)
    print(t1<=t2)
    print(t1.value())
    print(t2.value())
    print(Kn.v_to_kn(t2-t1, 1))
    print(Kn.v_to_kn(t2 - t1, 2))
    print(Kn.v_to_kn(t2 - t1, 3))
    print((t2+t1).kti)
    dt=Kn(3,2)
    print((t1+dt).kti)