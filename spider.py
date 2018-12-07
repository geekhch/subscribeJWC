import requests,time,logging,smtplib,traceback
from lxml import etree
from email.mime.text import MIMEText
from email.header import Header
from pymongo import MongoClient

MAIL = ['709531006@qq.com']
JWC = 'http://jwc.scu.edu.cn/'
DB = MongoClient('localhost')['jwc']
HOST = 'smtp.163.com'
MAIL_USER = '15682177109@163.com'
MAIL_PASS = 'SCU123scu'
LOG_FORMATTER = "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"


def GET(url):
    """GET请求"""
    response = requests.get(url)
    return response.content.decode('utf-8')

def get_logger():
    """获取logger"""
    fmt = logging.Formatter(LOG_FORMATTER, datefmt='%m-%d-%A %H:%M:%S')
    filestream = logging.FileHandler('jwc.log',encoding='utf-8')
    filestream.setFormatter(fmt)
    logger = logging.getLogger("jwc")
    logger.setLevel("INFO")
    logger.addHandler(filestream)
    return logger

class Spider:
    logger = get_logger()

    def __init__(self):
        """初始化数据库"""
        self.collection = DB.get_collection('information')
        if not self.collection.find_one({'_id':'information'}):
            self.collection.insert_one(
                {
                    '_id':'information',
                    'receivers':['709531006@qq.com'],
                    'record':[]
                }
            )


    def __parse_title(self):
        """解析网站主页，提取通知标题信息"""
        html = GET(JWC)
        selector = etree.HTML(html)
        data = selector.xpath('//ul[@class="list-llb-s"]/li')
        es = []
        for e in data:
            article = {
                'title': e.xpath('./@title')[0],
                'url': e.xpath('./a/@href')[0],
                'date': e.xpath('./a/em/text()')[0]
            }
            es.append(e)
        return es


    def __newArticleHelper(self, url):
        """下载url对应的通知内容"""
        html = GET(url)
        selector = etree.HTML(html)
        content = selector.xpath('//div[@class="list-a-content"]')
        content = etree.tostring(content[0],encoding='utf-8').decode('utf-8') # 节点转html原文本
        return content
        

    def __newArticle(self):
        """判断是否为最新文章，是的话则推送,并加入到记录"""
        record = self.collection.find_one({'_id':'information'},{'record':1,'_id':0})['record']
        
        generator = self.__parse_title()
        for e_info in generator:
            if not e_info['url'] in record:
                record.append(e_info['url'])
                # 控制缓存记录30条
                if len(record) > 30:
                    record.pop(0)
                content = self.__newArticleHelper(e_info['url'])
                yield [e_info, content]
        # 更新记录
        self.collection.update_one({'_id':'information'},{'$set':{'record':record}})


    def __mail(self, subject, message):
        """发送邮件"""
        sender = MAIL_USER
        receivers = self.collection.find_one({'_id':'information'},{'receivers':1,'_id':0})['receivers']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
        message = MIMEText(message, "HTML", 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')
        message['From'] =  "教务处通知"+"<MAIL_USER>"
        message['To'] = ";".join(receivers)
        try:
            smtpObj = smtplib.SMTP() 
            smtpObj.connect(HOST, 25)    # 25 为 SMTP 端口号
            smtpObj.login(MAIL_USER,MAIL_PASS)  
            smtpObj.sendmail(sender, receivers, message.as_string())
            self.logger.info("邮件发送成功")
        except smtplib.SMTPException as e:
            self.logger.warning(str(e))


    def publish(self):
        contents = self.__newArticle()
        for e_info,e_content in contents:
            e_content = '原文链接：'+ e_info['url'] + '\n' + e_content
            self.__mail(e_info['title'],e_content)


if __name__ == "__main__":
    spider = Spider()
    try:
        while True:
            spider.publish()
            time.sleep(1800)
    except Exception as e:
        spider.logger.warning(traceback.format_exc())



