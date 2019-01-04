# Winfor-BStrend
<font face="微软雅黑" size=2>**写在前面**：如果您正在使用github浏览本markdown文件，本文件中的数学公式渲染可能不能正常显示。推荐使用Chrome浏览器，并在Chrome的应用商店，下载[MathJax Plugin for Github](https://chrome.google.com/webstore/detail/mathjax-plugin-for-github/ioemnmodlmafdkllaclgeombjnmnbima/related)插件。</font>

&emsp;&emsp;BStrend属于<b>*BS系列*</b>项目的分支，简化了主程序的一部分功能，并主要用于回测和在日K线的级别上对于股票趋势的更新和报告。本项目基于Python语言开发，要求版本在3.6及以上，打包的可执行文件适用于Windows操作系统。本项目的主要设计组件包括如下部分：
+ **策略设计**：核心策略算法为高低点算法和基于高低点之上测趋势算法。本项目中的`高低点`与``趋势``继承主程序的定义及算法，在之后部分（[1.1高低点](#11高低点)）会予以说明。
+ **数据来源**：本项目对于股票历史数据存在较频繁的读写和遍历。数据主要为股票在回测阶段的收盘价、最高价与最低价，通过Wind数据库的量化接口API导入。
+ **数据存储**：本项目并不直接存储原始股票历史数据，而是将回测后的主要结果（历史高低点，以及当前策略运行产生的中间运算结果）存储在`sqlite`这一python轻量级数据库中；并在之后的每日运行中通过读取数据库获取股票的策略历史运算记录，并结合当前最新数据（当日最高价、最低价及收盘价）进行运算结果的更新，将更新结果写入数据库覆盖之前结果。
+ **图像绘制**：本项目的图像可视化基于`matplotlib.pyplot`这一python二维科学绘图常用工具包，仅在股票回测结束和之后股票趋势发生更新的当日收盘后会更新图像，图像包含了股票截止目前的高低点信息、历史趋势类型。由于图像绘制较为耗时且占用内存较高，因此设置了只绘制部分回测图像的控制参数以节约时空成本。具体设置请见后续部分。
+ **任务调度**：本项目中的任务调度框架采用`APschedular`，主要任务为交易日定时工作及运行日志管理。以A股市场交易时间为基准，用户可设定在每日收盘后（应当考虑到港股收盘时间较晚和WIND数据库数据更新需要一定延迟时间），设定当日更新全体股票的时刻，调度会记录任务堆栈中的定时，并在指定时间触发任务执行的信号。
+ **自动发信**：用户可选择“每日发信”模式和仅当有目标股票发生趋势改变时发信两种模式。美股信息单独发信，A股和港股合并发信。发信内容会提示股票变动，以及基准市场指数的趋势及图像，当前所有股票的趋势类型。
<!-- TOC START min:1 max:6 link:true update:false -->
- [Winfor-BStrend](#winfor-bstrend)
  - [1.策略设计](#1策略设计)
    - [1.1高低点](#11高低点)
    - [1.2趋势](#12趋势)
    - [1.3高低点和趋势的初始化设定](#13高低点和趋势的初始化设定)
  - [2.用户导引](#2用户导引)
    - [2.1文件配置](#21文件配置)
    - [2.2参数释义](#22参数释义)
    - [2.3发信内容](#23发信内容)
  - [3.开发者说明](#3开发者说明)
    - [3.1调用关系](#31调用关系)
    - [3.2模块功能](#32模块功能)

<!-- TOC END -->



### 1.策略设计
#### 1.1高低点
&emsp;&emsp;需要明确的是，高点和低点是间隔交叉出现的。在文档及代码中，请注意以下表示高低点的用语指向同一意思表示：


|             高点             |  高点index |             低点             |  低点index |
|:----------------------------:|:----------:|:----------------------------:|:----------:|
| H,h, hpoint, Hpoint highpoint | hindex, hpi | L，l, lpoint, Lpoint lowpoint | lindex lpi |

**高点**
> i）前低点已确认的情况下，回调达到`THRESH_D`个交易区间单位时，确认此区间的最高点为当前级别高点  
ii）前低点已确认的情况下，回调幅度超过前`AVG_N`次回调的均值（可选`AVG_BUFFER`），确认当前区间最高点为当前级别高点  
iii）前低点已确认的情况下，回调跌破前低点，即确认当前区间最高点为当前级别高点。  

**低点**
> i）前高点已确认的情况下，上涨达到`THRESH_D`个交易区间单位时，确认此区间的最低点为当前级别低点  
ii）前低点已确认的情况下，上涨幅度超过前`AVG_N`次上涨的均值（可选`AVG_BUFFER`），确认当前区间最低点为当前级别低点  
iii）前低点已确认的情况下，上涨超过前高点，即确认当前区间最低点为当前级别低点。  
#### 1.2趋势
&emsp;&emsp;本项目中定义三种趋势类型：
* `up`上升趋势
* `down`下跌趋势
* `consd`盘整趋势

**上涨**
> *上涨趋势的确认*：
i）出现连续两个低点抬高和高点抬高  
 $h_i,l_i,h_{i+1},l_{i+1};h_{i+1}>h_{i}, l_{i+1}>l_{i} $  
 $l_i,h_i,l_{i+1},h_{i+1};l_{i+1}>l_{i},;h_{i+1}>h_{i}$  
 ii）当最高点距离前日线低点`TREND_REV`个交易日时，则确认为日线上涨趋势  
*上涨趋势的延续*：低点依次抬高  
*上涨趋势结束*：  
i）转入盘整趋势  
 $h_i,l_i,h_{i+1},l_{i+1};h_{i+1}>h_{i} \ and \ l_{i+1}<l_i$  
 ii）转入下跌趋势  
 $h_i,l_i,h_{i+1},l_{i+1};h_{i+1}<h_i \ and \ l_{i+1}<l_i$  

 **下跌**
 > *下跌趋势的确认*：  
 i）出现连续两个低点降低和高点降低  
  $h_i,l_i,h_{i+1},l_{i+1};h_{i+1}<h_{i} \ and\ l_{i+1}<l_{i} $  
  $l_i,h_i,l_{i+1},h_{i+1};l_{i+1}<l_{i}\ and\ h_{i+1}<h_{i}$  
  ii）当最低点距离前日线低点`TREND_REV`个交易日时，则确认为日线下跌趋势  
 *下跌趋势的延续*：高点依次降低  
 *下跌趋势结束*：  
 i）转入盘整趋势  
  $h_i,l_i,h_{i+1},l_{i+1};h_{i+1}<l_{i},l_{i+1}>l_i$  
  ii）转入上涨趋势  
  $h_i,l_i,h_{i+1},l_{i+1};h_{i+1}>h_i,l_{i+1}>l_i$  

  **盘整**
  > *盘整趋势的确认*：  
  > 由以上上涨趋势和下跌趋势确认转入盘整趋势的  
  在序列最初高低点较少时，无法被归类于上涨或下跌趋势的，暂时归类为盘整趋势  
  *盘整趋势的结束*：满足上涨或下跌趋势的确认定义，结束盘整趋势而转入上涨或下跌趋势。  

#### 1.3高低点和趋势的初始化设定
&emsp;&emsp;在回测时，需要解决在遍历数据列表之前对于高低点和趋势的初始化问你。由于策略算法基于迭代规则，因此初值是必要的。初始化的原则是尽可能耗费较少的数据选择出合适的初值。幸运的是，当回测时期较长的时候，初值对于之后策略表现（主要是判断准确度）的影响会渐渐衰减。  
<b>*高低点的初始化设定*</b>
&emsp;&emsp;从序列首开始遍历日线数据，如果找到第一个分型类型是底分型，那么设该底K线为待判定低点，转而进入低点判定分支；如果第一个分型是顶分型，那么设定该顶K线为待判定高点，转而进入高点判定分支。关于分型的具体定义如下：
> *顶分型*：  
$K_{i-1}.h\le K_i.h\ and\ K_i.h\ge K_{i+1}.h \ and \ not \ K_{i-1}.h=K_i.h=K_{i+1}.h:称K_i$为该顶分型的顶
*底分型*：  
$K_{i-1}.l\ge K_i.l\ and\ K_i.l\le K_{i+1}.l\ and \ not \ K_{i-1}.l=K_i.l=K_{i+1}.l:称K_i$为该底分型的底

<b>*趋势的初始化设定*</b>  
&emsp;&emsp;趋势判别在回测算法中需要在遍历数据列表判定完回测区间内所有高低点后进行。趋势初始化需要至少确认4个高点或低点，枚举所有组合可能：
- $l_0, h_0, l_1, h_1; l_1>l_0\Rightarrow$`up`
- $l_0, h_0, l_1, h_1; l_1<l_0\Rightarrow$`consd`
- $h_0, l_0, h_1, l_1; h_0<h_1\Rightarrow$`down`
- $h_0, l_0, h_1, l_1; h_0>h_1\Rightarrow$`consd`
此外在第4个高点或者低点被确认之前的K线趋势都设置为确实类`None`。

### 2.用户导引
#### 2.1文件配置
&emsp;&emsp;用户使用本程序，可直接运行`monitor_s.exe`可执行程序，不需要本地python环境，但是以下支持文件务必完成配置。
- 下载`monitor_s.exe`到本地任意路径 ./directory/BStrend。
- 在同一文件夹下，新建`WindPy.pth`文件，并在文件中写入本机Wind安装地址，例如`C:\Wind\Wind.NET.Client\WindNET\x64`
- 进入Wind界面，在量化接口中修复python插件
- 在`.txt`文件中，第一列写入需要进行回测的Wind股票代码
- 下载config.conf到./directory/BStrend，直接在文件中修改对应的参数，注意注释中的解释和格式要求，并保存。参数具体含义请参考之后具体释义
#### 2.2参数释义
&emsp;&emsp;参数的格式和具体含义可以参照`config.conf`文件中的注释行和例子进行设定，包含所有开放给用户自定义的参数。这里进行详细的说明：
+ `begin_date`：格式'yyyy-mm-dd'，回测开始的日期，不一定要求当天是交易日。在日线趋势策略中，不会用到分钟级别的数据，因此对于日期没有较强的要求。
+ `end_date`：格式'yyyy-mm-dd'，回测结束时间，实际在本项目运行时不会被使用。因为本项目默认回测是用于为之后的每日更新状态提供中间运算结果，因此在调用回测部分是，回测结果默认是策略运行当日。
+ `paint`：控制回测多只股票时的绘图参数。根据希望输出的图像，接受以下格式的参数：
  a.`''`空字符串表示不在回测中绘制任何股票的图像  
  b.`'n'`表示仅绘制和输出前n只股票的图像  
  c.`'m:n'`表示绘制和输出第m只到第n只股票的图像  
  d.`'XXXXXX.SZ;XXXXXX.SH'`用`;`分隔具体的股票代码，输出对应股票代码的图像，当然该代码必须出现在加入回测的`.txt`文件中  
+ `thresh_d`：int类型，表示日线高低点结构确认的最小间隔。一般设置为13.
+ `avg_n`：int类型，在高低点确认的第ii)条判定条件中，取前`avg_n`次上涨或回撤的幅度做参考。如果当前尚未出现`avg_n`次上涨或回撤，那么这个判定条件不起作用。默认值取3。
+ `avg_buffer`：int或float类型，在`avg_n`次上涨或回调的均值基础上做一定的调整，以此结果作为当前高点或低点判定的参考。例如，当前待判定低点，待判定低点的价位为$l_0$，从待判定低点到当前区间内的最高价为$h$，设定`avg_n`=3，前3次上涨的幅度（指从低点到紧接着的高点的涨幅大小）分别为$u_1,u_2,u_3$，那么如果$\frac{h-l_0}{l_0}>\frac{u_1+u_2+u_3}{3}*$`avg_buffer`，即可确认当前待判定低点为低点。默认`avg_buffer`为1，即不对均值做调整。
+ `trend_rev`：int类型，适用上涨/下跌趋势的确认第ii)条准则。例如，当前处于下跌或盘整趋势，并且最近一个确认的高低点类型为低点，那么在被确认的低点当天至当前的区间内最高点的时间超过`trend_rev`个交易日，即可判定上涨趋势成立。反之，如果当前处于上涨或盘整阶段，并且最近一个确认的高低点类型为高点，那么在被确认高点当天至当前的区间内最低点当天的时间间隔超过`trend_rev`个交易日，即可判定下跌趋势成立。
+ `sender`：完整邮箱地址字符串，注意发信邮箱当前支持的邮箱地址后缀包括 163.com | winforcap.com | nedugroup.com | sina.com | sohu.com | 126.com | qq.com | hotmail.com | gmail.com | foxmail.com
+ `sender_key`：发信邮箱的密码字符串
+ `receiver`：接受邮件的收信人邮箱地址，多个邮件地址用;进行分隔
+ `freq`：int类型，发送邮件的频率设定。设定为1则仅在运行当天出现至少一只股票趋势变化时发送邮件，否则不发送邮件；设定为0则在运行当天不管是否出现趋势变化都会发送邮件。
+ `set_t`：当天运行策略，或发送邮件的时间（策略运行需要一定时间，预计实际邮件发送时间会比设定的时间稍晚几分钟）。
+ `code_file`：文件地址字符串（绝对路径），指定待回测股票文件的绝对路径，目前仅设定接受`.txt`文件类型
+ `work`：文件夹地址字符串，即管理该项目工作内容的文件夹地址，建议将输入文件、输出图像文件和数据库文件都设为该文件夹下的子文件（夹）。
+ `database`：数据库地址字符串（绝对路径），注意==如果更换了待回测股票内容，应当同时修改数据库名称，否则将会覆之前股票样本的运行结果记录==。本项目默认一个数据库对应管理一个股票样本池，不能够同时管理多个股票样本池（除了合并其为一个）。如果需要分开管理不同股票样本池，可以多次运行策略，并在每次运行策略前，更改`config.conf`文件，并注意运行结果的隔离。从数据安全的角度，<font color="red">并不建议这样做</font>。
+ `graph`：文件夹地址字符串（绝对路径），回测图像，及运行中产生的趋势变化后所重绘的更新图像文件存放文件夹地址。

#### 2.3发信内容
&emsp;&emsp;A股和港股的变动信息合并发信，用户将会收到邮件标题为“*趋势策略变动报告-A股、港股*”的邮件，内容包括
+ 趋势改变股票列表，eg.
![趋势改变股票列表](img/trend_chg_table.JPG)
+ 基准市场指数回测以来趋势变动图，eg.
![上证综指趋势变化图](img/mkt1_graph.JPG)
+ 发生趋势改变的股票的趋势变动图
+ 所有处在上涨趋势中的股票列表，eg.
![上涨趋势中股票列表](img/up_table.JPG)
+ 所有处在下跌趋势中的股票列表
+ 所有处在盘整趋势中的股票列表

&emsp;&emsp;美股的变动信息单独发信，用户将会收到邮件标题为“*趋势策略变动报告-美股*”的邮件。其内容和结构同上。

### 3.开发者说明
&emsp;&emsp;本项目开发基于Python3.6及以上版本，Project包含10个python文件和一个`config.conf`文件。main函数入口为`monitor_s.py`文件。运行Project需要载入以下packages:  <font face="Times New Rome">WindPy | apschedular | sqlite3 | os | logging | datetime | numpy | locale | pandas | matplotlib | time| dateutil | copy | re | smtplib | email | premailer<font>。

#### 3.1调用关系
&emsp;&emsp;项目内完整调用关系如下：
```python
reset_params() (constant)
set_triggers() (monitor_s)
Monitor.__init__(self) (Monitor in monitor_s)
    Monitor.runIn(self) (Monitor in monitor_s)
        indexTop(pre_list, fix) (monitor_s)
Monitor.check_dir(self) (Monitor in monitor_s)
Monitor.init(self) (Monitor in monitor_s)
    create_Strategy(tup_list, conn) (sqlite_s)
    code_helper(codename, rev=False) (sqlite_s)
    runbacktest(begin=BEGIN_DATE, codename="600519.SH", dir=GRAPH, end=END_DATE, paint=True, star=False) (graph)
        loadData_daily(begin_date=BEGIN_DATE, stockname='600519.SH', end_date=END_DATE) (loadData)
            loaddataError.__init__(self, msg) (loaddataError in loadData)
            Kti.__init__(self, n_30=N_30, *i) (Kti in defindex)
            K.__init__(self, high, low, close, i, lev, time, dhl="") (K in K)
        HLPoint.__init__(self, klist, code, thresh=THRESH_D) (HLPoint in hlPoint)
        HLPoint.init_hl(self) (HLPoint in hlPoint)
        HLPoint.get_hl(self) (HLPoint in hlPoint)
            HLPoint.step_hl(self, wait_thresh=WAIT_DTO30) (HLPoint in hlPoint)
                HLPoint.l2h(self) (HLPoint in hlPoint)
                HLPoint.h2l(self) (HLPoint in hlPoint)
        Trend.__init__(self, hlp_env) (Trend in trend)
        Trend.get_trend(self) (Trend in trend)
            Trend.init_trd(self) (Trend in trend)
                TrendError.__init__(self, msg="Undecidable trend; Need more high or low points to decide trend") (TrendError in trend)
            Trend.step_trdmax(self) (Trend in trend)
            Trend.step_trd(self) (Trend in trend)
        BSgraph.__init__(self, hlist, llist, data, note, codename) (BSgraph in graph)
        BSgraph.strategy_info(self, lasthl, space_h, space_l) (BSgraph in graph)
        BSgraph.performance(self, trdchg, dir="", star=False) (BSgraph in graph)
    create_Stock(tup_list, conn, codename) (sqlite_s)
        code_helper(codename, rev=False) (sqlite_s)
Monitor.daily1(self) (Monitor in monitor_s)
    code_helper(codename, rev=False) (sqlite_s)
    HLPoint.step_hl_s(hl, high, low, temp_hl, temp_m, from_hl, from_temp, pre_high, pre_low, use_space, space_h, space_l, l2h, h2l) (HLPoint in hlPoint)
    Trend.step_trdmax_s(hl, low, high, from_temp, from_hl, temp_hl, trd) (Trend in trend)
    Trend.step_trd_s(trd, hl, low, high, pre_low, pre_high, pre2_low, pre2_high) (Trend in trend)
    Monitor.sent(self) (Monitor in monitor_s)
        indexTop(pre_list, fix) (monitor_s)
        runbacktest(begin=BEGIN_DATE, codename="600519.SH", dir=GRAPH, end=END_DATE, paint=True, star=False) (graph)
            loadData_daily(begin_date=BEGIN_DATE, stockname='600519.SH', end_date=END_DATE) (loadData)
                loaddataError.__init__(self, msg) (loaddataError in loadData)
                Kti.__init__(self, n_30=N_30, *i) (Kti in defindex)
                K.__init__(self, high, low, close, i, lev, time, dhl="") (K in K)
            HLPoint.__init__(self, klist, code, thresh=THRESH_D) (HLPoint in hlPoint)
            HLPoint.init_hl(self) (HLPoint in hlPoint)
            HLPoint.get_hl(self) (HLPoint in hlPoint)
                HLPoint.step_hl(self, wait_thresh=WAIT_DTO30) (HLPoint in hlPoint)
                    HLPoint.l2h(self) (HLPoint in hlPoint)
                    HLPoint.h2l(self) (HLPoint in hlPoint)
            Trend.__init__(self, hlp_env) (Trend in trend)
            Trend.get_trend(self) (Trend in trend)
                Trend.init_trd(self) (Trend in trend)
                    TrendError.__init__(self, msg="Undecidable trend; Need more high or low points to decide trend") (TrendError in trend)
                Trend.step_trdmax(self) (Trend in trend)
                Trend.step_trd(self) (Trend in trend)
            BSgraph.__init__(self, hlist, llist, data, note, codename) (BSgraph in graph)
            BSgraph.strategy_info(self, lasthl, space_h, space_l) (BSgraph in graph)
            BSgraph.performance(self, trdchg, dir="", star=False) (BSgraph in graph)
    SendEmail.__init__(self) (SendEmail in email_s)
    SendEmail.buildHTML(self, chg_html, up_html, down_html, consd_html, img_html, stampf) (SendEmail in email_s)
    SendEmail.imageHTML(self, chg_img) (SendEmail in email_s)
    SendEmail.setSend(self, subject, sender, receiver, pwd, sender_name="quant") (SendEmail in email_s)
    Monitor.daily2(self) (Monitor in monitor_s)
        code_helper(codename, rev=False) (sqlite_s)
        HLPoint.step_hl_s(hl, high, low, temp_hl, temp_m, from_hl, from_temp, pre_high, pre_low, use_space, space_h, space_l, l2h, h2l) (HLPoint in hlPoint)
        Trend.step_trdmax_s(hl, low, high, from_temp, from_hl, temp_hl, trd) (Trend in trend)
        Trend.step_trd_s(trd, hl, low, high, pre_low, pre_high, pre2_low, pre2_high) (Trend in trend)
        Monitor.sent(self) (Monitor in monitor_s)
            indexTop(pre_list, fix) (monitor_s)
            runbacktest(begin=BEGIN_DATE, codename="600519.SH", dir=GRAPH, end=END_DATE, paint=True, star=False) (graph)
                loadData_daily(begin_date=BEGIN_DATE, stockname='600519.SH', end_date=END_DATE) (loadData)
                    loaddataError.__init__(self, msg) (loaddataError in loadData)
                    Kti.__init__(self, n_30=N_30, *i) (Kti in defindex)
                    K.__init__(self, high, low, close, i, lev, time, dhl="") (K in K)
                HLPoint.__init__(self, klist, code, thresh=THRESH_D) (HLPoint in hlPoint)
                HLPoint.init_hl(self) (HLPoint in hlPoint)
                HLPoint.get_hl(self) (HLPoint in hlPoint)
                    HLPoint.step_hl(self, wait_thresh=WAIT_DTO30) (HLPoint in hlPoint)
                        HLPoint.l2h(self) (HLPoint in hlPoint)
                        HLPoint.h2l(self) (HLPoint in hlPoint)
                Trend.__init__(self, hlp_env) (Trend in trend)
                Trend.get_trend(self) (Trend in trend)
                    Trend.init_trd(self) (Trend in trend)
                        TrendError.__init__(self, msg="Undecidable trend; Need more high or low points to decide trend") (TrendError in trend)
                    Trend.step_trdmax(self) (Trend in trend)
                    Trend.step_trd(self) (Trend in trend)
                BSgraph.__init__(self, hlist, llist, data, note, codename) (BSgraph in graph)
                BSgraph.strategy_info(self, lasthl, space_h, space_l) (BSgraph in graph)
                BSgraph.performance(self, trdchg, dir="", star=False) (BSgraph in graph)
        SendEmail.__init__(self) (SendEmail in email_s)
        SendEmail.buildHTML(self, chg_html, up_html, down_html, consd_html, img_html, stampf) (SendEmail in email_s)
        SendEmail.imageHTML(self, chg_img) (SendEmail in email_s)
        SendEmail.setSend(self, subject, sender, receiver, pwd, sender_name="quant") (SendEmail in email_s)
Monitor.set_sche(self) (Monitor in monitor_s)
```
具体函数的功能（本markdown文件待完善）请见源代码内的注释，以下主要介绍每个module的实现功能。
#### 3.2模块功能
