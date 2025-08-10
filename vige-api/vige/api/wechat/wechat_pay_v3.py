import json
import logging
import os
from random import sample, choice
from string import ascii_letters, digits
import time
from ...config import config
import uuid

from wechatpayv3 import WeChatPay, WeChatPayType


# 微信支付商户号（直连模式）或服务商商户号（服务商模式，即sp_mchid)
MCHID = config.WECHAT_PAY_MCHID

# 商户证书私钥
current_path = os.path.abspath(os.path.dirname(__file__))
key_path = os.path.join(current_path, 'cert/apiclient_key.pem')
with open(key_path) as f:
    PRIVATE_KEY = f.read()

pub_key_path = os.path.join(current_path, 'cert/pub_key.pem')
if os.path.exists(pub_key_path):
    with open(pub_key_path) as f:
        PUBLIC_KEY = f.read()

# 商户证书序列号
CERT_SERIAL_NO = config.WECHAT_PAY_CERT_SERIAL_NO

# API v3密钥， https://pay.weixin.qq.com/wiki/doc/apiv3/wechatpay/wechatpay3_2.shtml
APIV3_KEY = config.WECHAT_PAY_API_V3_KEY

# APPID，应用ID或服务商模式下的sp_appid
APPID = config.WECHAT_APP_ID

# 回调地址，也可以在调用接口的时候覆盖
NOTIFY_URL = config.WECHAT_PAY_NOTIFY_URL

# 日志记录器，记录web请求和回调细节
logging.basicConfig(filename=os.path.join(os.getcwd(), 'demo.log'), level=logging.DEBUG, filemode='a', format='%(asctime)s - %(process)s - %(levelname)s: %(message)s')
LOGGER = logging.getLogger("demo")

# 微信支付平台证书缓存目录，减少证书下载调用次数，首次使用确保此目录为空目录.
# 初始调试时可不设置，调试通过后再设置，示例值:'./cert'
CERT_DIR = None

# 接入模式:False=直连商户模式，True=服务商模式
PARTNER_MODE = False

# 代理设置，None或者{"https": "http://10.10.1.10:1080"}，详细格式参见https://docs.python-requests.org/zh_CN/latest/user/advanced.html
PROXY = None


class WxPay(object):

    def __init__(self):
        # 初始化
        self.v3_pay = WeChatPay(
            wechatpay_type=WeChatPayType.NATIVE,
            mchid=MCHID,
            private_key=PRIVATE_KEY,
            cert_serial_no=CERT_SERIAL_NO,
            apiv3_key=APIV3_KEY,
            appid=APPID,
            notify_url=NOTIFY_URL,
            cert_dir=CERT_DIR,
            logger=LOGGER,
            partner_mode=PARTNER_MODE,
            proxy=PROXY,
            public_key=PUBLIC_KEY,
            public_key_id=config.WECHAT_PAY_PUB_KEY_ID
            )

    @property
    def nonce_str(self):
        char = ascii_letters + digits
        return "".join(choice(char) for _ in range(32))

    def get_jsapi_result(self, prepay_id):
        package = "prepay_id={0}".format(prepay_id)
        timestamp = str(int(time.time()))
        nonce_str = self.nonce_str
        sign = self.v3_pay.sign(data=[APPID, timestamp, nonce_str, package])
        return dict(package=package, appId=APPID, signType="RSA",
                    timeStamp=timestamp, nonceStr=nonce_str, sign=sign)


wxpay = WxPay()
