# -*- coding: utf-8 -*-
#! python3

import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.header import Header
from premailer import transform


# 常用邮箱的发件服务器地址，邮箱后缀：（发件服务器地址，是否SSL发信， 端口号）
host_dict = {'163.com': ('smtp.163.com', 0, 25),
             'winforcap.com': ('smtp.winforcap.com', 0, 25),
             'nedugroup.com': ('smtp.nedugroup.com', 0, 25),
             'sina.com': ('smtp.sina.com.cn', 0, 25),
             'sohu.com': ('smtp.sohu.com', 0, 25),
             '126.com': ('smtp.126.com', 0, 25),
             'qq.com': ('smtp.qq.com', 0, 25),
             'hotmail.com': ('smtp.live.com', 0, 587),
             'gmail.com': ('smtp.gmail.com', 1, 587),
             'foxmail.com': ('smtp.foxmail.com', 0, 25)}


class SendEmail:
    def __init__(self):
        self.root_msg = MIMEMultipart("root")
        self.content_msg = MIMEMultipart("body")
        self.isSent = False

    def setSend(self, subject, sender, receiver, pwd, sender_name="quant"):
        """
        发信基本设置和发信邮箱登录
        :param subject: 邮件标题
        :param sender: 发信邮箱
        :param receiver: 邮件接收者
        :param pwd: 发信邮箱登录密码
        :param sender_name: 发信邮箱显示名称
        :return:
        """
        self.root_msg['subject'] = subject
        self.root_msg['from'] = Header(sender)
        self.root_msg['to'] = ','.join(receiver)
        server = sender.split('@')[1]
        host, SSL, port = host_dict[server]
        if SSL:
            self.smtp = smtplib.SMTP_SSL(host, port)
        else:
            self.smtp = smtplib.SMTP(host, port)
        self.smtp.login(sender, pwd)
        self.smtp.sendmail(sender, receiver, self.root_msg.as_string())
        self.isSent = True

    def imageHTML(self, chg_img):
        for ii in range(len(chg_img)):
            img = open(chg_img[ii], 'rb')
            imgh = MIMEImage(img.read())
            img.close()
            imgh.add_header('Content-ID', f'<image{ii}>')
            self.root_msg.attach(imgh)

    def buildHTML(self, chg_html, up_html, down_html, consd_html, img_html, stampf):
        context = """
            <html>
                <head>
                    <meta charset='utf-8'>
                        <style type="text/css">
                            .title{font-weight:bold;font-size:16px;}
                            h2{text-align:center;font-family:宋体;
                               font-weight:bold;
                               font-size:18px}
                            p.date{text-align:right;}
                            caption{font-size:16px;}
                            .thbg0{background:#dc143c !important;}
                            .thbg{background:#0000cd !important;}
                            .thfont{font-family:微软雅黑;
                                    font-weight:bold;
                                    width: 160px;
                                    height:30px;
                                    font-size:15px;
                                    color:#fffff0}
                            .cell{background:#ffffff !important;
                                  font-family:宋体;
                                  text-align:center;
                                  width: 160px;
                                  height: 30px;}
                            .border{border-style: solid;
                                    border-width: 2px;
                                    border-color: #cccccc;}
                        </style>
                </head>
                <body>""" + f"""
                    <h2>BS趋势策略报告-{stampf}</h2>
                    <p>
                    <div align="center">
                        <table class="border">
                        <caption>趋势改变股票列表</caption>
                        {chg_html}
                    </table>
                    </div>
                    </p>
                    <p>
                    {img_html}
                    </p>
                    <p>
                    <div align="center">
                        <table class="border">
                        <caption>上涨趋势中的股票列表</caption>
                        {up_html}
                    </table>
                    </div>
                    </p>
                    <p>
                    <div align="center">
                        <table class="border">
                        <caption>下跌趋势中的股票列表</caption>
                        {down_html}
                    </table>
                    </div>
                    </p>
                    <p>
                    <div align="center">
                        <table class="border">
                        <caption>盘整趋势中的股票列表</caption>
                        {consd_html}
                        </table>
                    <div>
                    </p>
                </body>
            </html>"""
        context = transform(context)
        context = MIMEText(context, 'html', 'utf-8')
        self.content_msg.attach(context)
        self.root_msg.attach(self.content_msg)


if __name__ == "__main__":
    mail = SendEmail()
    chg_html ='''<tr><th class="thbg thfont">代码</th><th class="thbg thfont">代码</th>
    <th class="thbg thfont">简称</th><th class="thbg thfont">趋势</th></tr>'''
    # 675*360might be fit
    img_html = '''<b><div align="center"><img src="cid:image0" 
                alt="strategy trend picture"  width="695" height="373" 
                style="display:block;font-family:Arial;"></div></b>
                <b><div align="center"><img src="cid:image1" 
                alt="strategy trend picture"  width="695" height="373" 
                style="display:block;font-family:Arial;"></div></b>'''
    mail.buildHTML(chg_html, chg_html, chg_html, chg_html, img_html, "2018年10月13日")
    mail.imageHTML([r"C:\Users\zhangchangsheng\Desktop\graph_trend\BS_0003.HK.png",
                    r"C:\Users\zhangchangsheng\Desktop\graph_trend\BS_BABA.N.png"])
    mail.setSend("ptest", "quant@winforcap.com", "maggiefin@sina.com", "Leed@1234")

    print(mail.isSent)

