from __future__ import unicode_literals

import json
import time
import string
import logging
import hashlib
import requests
import urllib.parse
import os
from Crypto.PublicKey import RSA
import random
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64

from ..utils import config
from .wechat_pay_base import WechatError, Map

from lxml import etree


__all__ = ("WechatPayError", "WechatPay")

logger = logging.getLogger(__name__)

FAIL = "FAIL"
SUCCESS = "SUCCESS"


class WechatPayError(WechatError):

    def __init__(self, msg):
        super(WechatPayError, self).__init__(msg)


class WechatPay(object):
    PAY_HOST = "https://api.mch.weixin.qq.com"

    def __init__(self, key=None, cert=None):
        self.app_id = config.WECHAT_APP_ID
        self.mch_id = config.WECHAT_PAY_MCHID
        self.mch_key = config.WECHAT_PAY_API_V3_KEY
        self.notify_url = config.WECHAT_PAY_NOTIFY_URL
        self.serial_no = config.WECHAT_PAY_CERT_SERIAL_NO
        # 证书相关
        self.key = key
        self.cert = cert
        self.header = None
        self.sess = requests.Session()

    @classmethod
    def init_wechat_pay(cls, use_cert=False, is_refund=False):
        key_file_path = None
        cert_file_path = None

        # 这两个证书涉及到退款操作，可以先没有
        if use_cert:
            current_path = os.path.abspath(os.path.dirname(__file__))
            key_file_path = os.path.join(
                current_path,
                'server-cert/5FA40B5492D791363B4722463716D0AC.pem')
            cert_file_path = os.path.join(
                current_path,
                'server-cert/637988473E8290BBA204E837905BD319.pem'
            )
            # logger.warning('key file path: {}'.format(key_file_path))
            # logger.warning('cert file path: {}'.format(cert_file_path))

        refund_pay = cls(
            key=key_file_path,
            cert=cert_file_path
        )
        return refund_pay

    @property
    def remote_addr(self):
        # TODO: 在FastAPI中，remote_addr需要通过Request对象获取
        # 这里暂时返回空字符串，在具体使用时通过参数传入
        return ""

    @property
    def nonce_str(self):
        char = string.ascii_letters + string.digits
        return "".join(random.choice(char) for _ in range(32))

    def sign(self, raw):
        logger.warning('开始签名：{}'.format(raw))
        raw = [(k, str(raw[k]) if isinstance(raw[k], int) else raw[k])
               for k in sorted(raw.keys())]
        s = "&".join("=".join(kv) for kv in raw if kv[1])
        s += "&key={0}".format(self.mch_key)
        result = hashlib.md5(s.encode("utf-8")).hexdigest().upper()
        logger.warning('签名结果：{}, s: {}'.format(result, s))
        return result

    def jsapi_sign(self, raw):
        """
        签名串一共有四行，每一行为一个参数。行尾以\n（换行符，ASCII编码值为0x0A）结束，包括最后一行。
        如果参数本身以\n结束，也需要附加一个\n
        例子：
        echo -n -e \"wx8888888888888888\n1414561699\n5K8264ILTKCH16CQ2502SI8ZNMTM67VS\nprepay_id=wx201410272009395522657a690389285100\n" \
        | openssl dgst -sha256 -sign apiclient_key.pem \
        | openssl base64 -A
        uOVRnA4qG/MNnYzdQxJanN+zU+lTgIcnU9BxGw5dKjK+VdEUz2FeIoC+D5sB/LN+nGzX3hfZg6r5wT1pl2ZobmIc6p0ldN7J6yDgUzbX8Uk3sD4a4eZVPTBvqNDoUqcYMlZ9uuDdCvNv4TM3c1WzsXUrExwVkI1XO5jCNbgDJ25nkT/c1gIFvqoogl7MdSFGc4W4xZsqCItnqbypR3RuGIlR9h9vlRsy7zJR9PBI83X8alLDIfR1ukt1P7tMnmogZ0cuDY8cZsd8ZlCgLadmvej58SLsIkVxFJ8XyUgx9FmutKSYTmYtWBZ0+tNvfGmbXU7cob8H/4nLBiCwIUFluw==
        """
        # use python to sign
        logger.warning('开始签名：{}'.format(raw))
        for k, v in raw.items():
            if isinstance(v, int):
                raw[k] = str(v)
        s = "\n".join(raw.values()) + "\n"
        print(s, '--------- sssssssss')
        s = s.encode('utf-8')
        current_path = os.path.abspath(os.path.dirname(__file__))
        key_path = os.path.join(current_path, 'cert/apiclient_key.pem')
        with open(key_path, 'r') as f:
            # 这里要注意的秘钥只能有三行
            # -----BEGIN PRIVATE KEY-----
            # ******************秘钥只能在一行，不能换行*****************
            # -----END PRIVATE KEY-----
            private_key = f.read()
            f.close()
            pkey = RSA.importKey(private_key)
            h = SHA256.new(s)
            signature = PKCS1_v1_5.new(pkey).sign(h)
            sign = base64.b64encode(signature).decode()
            return sign

    def check(self, data):
        sign = data.pop("sign")
        return sign == self.sign(data)

    def to_xml(self, raw):
        s = ""
        for k, v in raw.items():
            s += "<{0}>{1}</{0}>".format(k, v)
        s = "<xml>{0}</xml>".format(s)
        return s.encode("utf-8")

    def to_dict(self, content):
        raw = {}
        root = etree.fromstring(content.encode("utf-8"),
                                parser=etree.XMLParser(resolve_entities=False))
        for child in root:
            raw[child.tag] = child.text
        return raw

    def _fetch(self, url, data, use_cert=False, appid=True, is_native=False, headers=None):
        if appid:
            data.setdefault("appid", self.app_id)
        if not is_native:
            data.setdefault("mch_id", self.mch_id)
            data.setdefault("nonce_str", self.nonce_str)
            data.setdefault("sign", self.sign(data))
        else:
            # https://pay.weixin.qq.com/wiki/doc/apiv3/apis/chapter3_4_1.shtml
            data.setdefault("mchid", self.mch_id)

        logger.warning('is native: {}, headers: {}, data: {}'.format(is_native, headers, json.dumps(data)))
        if use_cert:
            resp = self.sess.post(url, data=self.to_xml(data), cert=(self.cert, self.key), headers=headers)
        else:
            resp = self.sess.post(url, data=json.dumps(data) if is_native else self.to_xml(data), headers=headers)

        content = resp.content.decode("utf-8")
        logger.warning('WECHAT_PAY_RESULT: {}, body: {}'.format(
            content, self.to_xml(data)))
        if "return_code" in content:
            data = Map(self.to_dict(content))
            if data.return_code == FAIL:
                raise WechatPayError(data.return_msg)
            if "result_code" in content and data.result_code == FAIL:
                raise WechatPayError(data.err_code_des)
            return data
        return content

    def reply(self, msg, ok=True):
        code = SUCCESS if ok else FAIL
        return self.to_xml(dict(return_code=code, return_msg=msg))

    def unified_order(self, **data):
        """
        统一下单
        out_trade_no、body、total_fee、trade_type必填
        app_id, mchid, nonce_str自动填写
        spbill_create_ip 在flask框架下可以自动填写, 非flask框架需要主动传入此参数
        """
        url = self.PAY_HOST + "/pay/unifiedorder"

        # 必填参数
        if "out_trade_no" not in data:
            raise WechatPayError("缺少统一支付接口必填参数out_trade_no")
        if "body" not in data:
            raise WechatPayError("缺少统一支付接口必填参数body")
        if "total_fee" not in data:
            raise WechatPayError("缺少统一支付接口必填参数total_fee")
        if "trade_type" not in data:
            raise WechatPayError("缺少统一支付接口必填参数trade_type")

        # 关联参数
        if data["trade_type"] == "JSAPI" and "openid" not in data:
            raise WechatPayError("trade_type为JSAPI时，openid为必填参数")
        if data["trade_type"] == "NATIVE" and "product_id" not in data:
            raise WechatPayError("trade_type为NATIVE时，product_id为必填参数")
        data.setdefault("notify_url", self.notify_url)
        if "spbill_create_ip" not in data:
            data.setdefault("spbill_create_ip", self.remote_addr)

        raw = self._fetch(url, data)
        return raw

    def jsapi(self, **kwargs):
        """
        生成给JavaScript调用的数据
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=7_7&index=6
        """
        kwargs.setdefault("trade_type", "JSAPI")
        raw = self.unified_order(**kwargs)
        package = "prepay_id={0}".format(raw["prepay_id"])
        timestamp = str(int(time.time()))
        nonce_str = self.nonce_str
        raw = dict(appId=self.app_id, timeStamp=timestamp,
                   nonceStr=nonce_str, package=package, signType="MD5")
        logger.warning('---- jsapi sign: {}'.format(raw))
        sign = self.sign(raw)
        return dict(package=package, appId=self.app_id, signType="MD5",
                    timeStamp=timestamp, nonceStr=nonce_str, sign=sign)

    def get_jsapi_result(self, prepay_id):
        package = "prepay_id={0}".format(prepay_id)
        timestamp = str(int(time.time()))
        nonce_str = self.nonce_str
        raw = dict(appId=self.app_id, timeStamp=timestamp,
                   nonceStr=nonce_str, package=package)
        sign = self.jsapi_sign(raw)
        return dict(package=package, appId=self.app_id, signType="RSA",
                    timeStamp=timestamp, nonceStr=nonce_str, sign=sign)

    def fetch_native_sign(self):
        logger.warning('开始签名')

    def order_query(self, **data):
        """
        订单查询
        out_trade_no, transaction_id至少填一个
        appid, mchid, nonce_str不需要填入
        """
        url = self.PAY_HOST + "/v3/pay/transactions"

        if "out_trade_no" not in data and "transaction_id" not in data:
            raise WechatPayError("订单查询接口中，out_trade_no、transaction_id至少填一个")

        if "out_trade_no" in data:
            url = url + "/out-trade-no/" + data["out_trade_no"]
        elif "transaction_id" in data:
            url = url + "/id/" + data["transaction_id"]

        url = url + "?mchid=" + self.mch_id

        logger.warning('订单查询接口中，url: {}'.format(url))
        auth = self.get_auth(None, url, method='GET')
        headers = {'Authorization': auth, 'Content-Type': 'application/json'}
        logger.warning('headers: {}'.format(headers))
        resp = self.sess.get(url, headers=headers)
        content = resp.content.decode("utf-8")
        logger.warning('WECHAT_ORDER_QUERY_RESULT: {}, body: {}'.format(
            content, self.to_xml(data)))
        if "return_code" in content:
            data = Map(self.to_dict(content))
            if data.return_code == FAIL:
                raise WechatPayError(data.return_msg)
            if "result_code" in content and data.result_code == FAIL:
                raise WechatPayError(data.err_code_des)
            return data
        return content

    def close_order(self, out_trade_no, **data):
        """
        关闭订单
        out_trade_no必填
        appid, mchid, nonce_str不需要填入
        """
        url = self.PAY_HOST + "/pay/closeorder"

        data.setdefault("out_trade_no", out_trade_no)

        return self._fetch(url, data)

    def refund(self, **data):
        """
        申请退款
        out_trade_no、transaction_id至少填一个且
        out_refund_no、total_fee、refund_fee、op_user_id为必填参数
        appid、mchid、nonce_str不需要填入
        """
        url = self.PAY_HOST + "/secapi/pay/refund"
        if not self.key or not self.cert:
            raise WechatError("退款申请接口需要双向证书")
        if "out_trade_no" not in data and "transaction_id" not in data:
            raise WechatPayError("退款申请接口中，out_trade_no、transaction_id至少填一个")
        if "out_refund_no" not in data:
            raise WechatPayError("退款申请接口中，缺少必填参数out_refund_no");
        if "total_fee" not in data:
            raise WechatPayError("退款申请接口中，缺少必填参数total_fee");
        if "refund_fee" not in data:
            raise WechatPayError("退款申请接口中，缺少必填参数refund_fee");

        return self._fetch(url, data, True)

    def refund_query(self, **data):
        """
        查询退款
        提交退款申请后，通过调用该接口查询退款状态。退款有一定延时，
        用零钱支付的退款20分钟内到账，银行卡支付的退款3个工作日后重新查询退款状态。
        out_refund_no、out_trade_no、transaction_id、refund_id四个参数必填一个
        appid、mchid、nonce_str不需要填入
        """
        url = self.PAY_HOST + "/pay/refundquery"
        if "out_refund_no" not in data and "out_trade_no" not in data \
                and "transaction_id" not in data and "refund_id" not in data:
            raise WechatPayError("退款查询接口中，out_refund_no、out_trade_no、transaction_id、refund_id四个参数必填一个")

        return self._fetch(url, data)

    def download_bill(self, bill_date, bill_type="ALL", **data):
        """
        下载对账单
        bill_date、bill_type为必填参数
        appid、mchid、nonce_str不需要填入
        """
        url = self.PAY_HOST + "/pay/downloadbill"
        data.setdefault("bill_date", bill_date)
        data.setdefault("bill_type", bill_type)

        if "bill_date" not in data:
            raise WechatPayError("对账单接口中，缺少必填参数bill_date")

        return self._fetch(url, data)

    def pay_individual(self, **data):
        """
        企业付款到零钱
        """
        url = "https://api.mch.weixin.qq.com/mmpaymkttransfers/promotion/transfers"
        if not self.key or not self.cert:
            raise WechatPayError("企业接口需要双向证书")
        if "partner_trade_no" not in data:
            raise WechatPayError("企业付款接口中, 缺少必要的参数partner_trade_no")
        if "openid" not in data:
            raise WechatPayError("企业付款接口中，缺少必填参数openid")
        if "amount" not in data:
            raise WechatPayError("企业付款接口中，缺少必填参数amount")
        if "desc" not in data:
            raise WechatPayError("企业付款接口中，缺少必填参数desc")
        data.setdefault('check_name', 'NO_CHECK')
        return self._fetch_pay(url, data, True)

    def pay_individual_to_card(self, **data):
        """企业付款到银行卡"""
        url = 'https://api.mch.weixin.qq.com/mmpaysptrans/pay_bank'
        if not self.key or not self.cert:
            raise WechatPayError("企业接口需要双向证书")
        if "partner_trade_no" not in data:
            raise WechatPayError("企业付款接口中, 缺少必要的参数partner_trade_no")
        if "enc_bank_no" not in data:
            raise WechatPayError("企业付款接口中，缺少必填参数enc_bank_no")
        if "enc_true_name" not in data:
            raise WechatPayError("企业付款接口中，缺少必填参数enc_true_name")
        if "bank_code" not in data:
            raise WechatPayError("企业付款接口中，缺少必填参数bank_code")
        if "amount" not in data:
            raise WechatPayError("企业付款接口中，缺少必填参数amount")
        return self._fetch(url, data, True, False)

    def pay_individual_bank_query(self, **data):
        """企业付款到银行卡查询"""
        url = "https://api.mch.weixin.qq.com/mmpaysptrans/query_bank"
        if not self.key or not self.cert:
            raise WechatPayError("企业接口需要双向证书'")
        if "partner_trade_no" not in data:
            raise WechatPayError("企业付款接口中, 缺少必要的参数partner_trade_no")
        return self._fetch(url, data, True, False)

    def pay_individual_query(self, **data):
        """企业付款到零钱查询"""
        url = "https://api.mch.weixin.qq.com/mmpaymkttransfers/gettransferinfo"
        if not self.key or not self.cert:
            raise WechatPayError("企业接口需要双向证书'")
        if "partner_trade_no" not in data:
            raise WechatPayError("企业付款接口中, 缺少必要的参数partner_trade_no")
        return self._fetch(url, data, True)

    def _fetch_pay(self, url, data, use_cert=False):
        data.setdefault("mch_appid", self.app_id)
        data.setdefault("mchid", self.mch_id)
        data.setdefault("nonce_str", self.nonce_str)
        data.setdefault("sign", self.sign(data))
        if use_cert:
            resp = self.sess.post(url, data=self.to_xml(data), cert=(self.cert, self.key))
        else:
            resp = self.sess.post(url, data=self.to_xml(data))
        content = resp.content.decode("utf-8")
        if "return_code" in content:
            data = Map(self.to_dict(content))
            if data.return_code == FAIL:
                raise WechatPayError(data.return_msg)
            if "result_code" in content and data.result_code == FAIL:
                raise WechatPayError(data.err_code_des)
            return data
        return content


    # 生成欲签名字符串
    def sign_str(self, method, url_path, timestamp, nonce_str, request_body):
        if not request_body:
            request_body = ''
        return '%s\n%s\n%s\n%s\n%s\n' % (method, url_path, timestamp, nonce_str, request_body)

    # 生成随机字符串
    @property
    def nonce_str(self):
        char = string.ascii_letters + string.digits
        return "".join(random.choice(char) for _ in range(32))

    # 生成签名
    def native_sign(self, sign_str):
        current_path = os.path.abspath(os.path.dirname(__file__))
        key_path = os.path.join(current_path, 'cert/apiclient_key.pem')
        with open(key_path, 'r') as f:
            # 这里要注意的秘钥只能有三行
            # -----BEGIN PRIVATE KEY-----
            # ******************秘钥只能在一行，不能换行*****************
            # -----END PRIVATE KEY-----
            private_key = f.read()
            f.close()
            pkey = RSA.importKey(private_key)
            h = SHA256.new(sign_str.encode('utf-8'))
            signature = PKCS1_v1_5.new(pkey).sign(h)
            sign = base64.b64encode(signature).decode()
            return sign


    # 生成 Authorization
    def authorization(self, method, url_path, timestamp, body=None):
        # 加密子串
        nonce_str = self.nonce_str
        signstr = self.sign_str(method=method, url_path=url_path,
                                timestamp=timestamp, nonce_str=nonce_str,
                                request_body=body)
        logger.warning('signstr: {}'.format(signstr))
        # 加密后子串
        s = self.native_sign(signstr)
        authorization = 'WECHATPAY2-SHA256-RSA2048 ' \
                        'mchid="{mchid}",' \
                        'nonce_str="{nonce_str}",' \
                        'signature="{sign}",' \
                        'timestamp="{timestamp}",' \
                        'serial_no="{serial_no}"'. \
            format(mchid=self.mch_id,
                   nonce_str=nonce_str,
                   sign=s,
                   timestamp=timestamp,
                   serial_no=self.serial_no
                   )

        logger.warning('authorization: {}, sign: {}'.format(authorization, s))
        return authorization

    def get_auth(self, body, url_path, method='POST'):
        if body:
            body.setdefault("appid", self.app_id)
            body.setdefault("mchid", self.mch_id)
            body = json.dumps(body)
        timestamp = str(int(time.time()))
        logger.warning('timestamp: {}, method: {}, url: {}, body: {}'.format(timestamp, method, url_path, body))
        return self.authorization(method, url_path, timestamp, body)


class WechatNativePay(WechatPay):

    def create_order(self, **data):
        data.setdefault("notify_url", self.notify_url)
        pay_type = data.get('pay_type', '')
        if pay_type == 'wechat':
            self.jsapi(**data)
            return
        is_h5_pay = pay_type == 'h5'
        # https://pay.weixin.qq.com/wiki/doc/apiv3/apis/chapter3_4_1.shtml
        if "amount" not in data:
            raise WechatPayError("缺少支付金额和币种")
        if 'description' not in data:
            raise WechatPayError('缺少商品描述')
        logger.warning('开始下单：{}'.format(data))

        url_path = '/v3/pay/transactions/'

        need_app_id = False
        is_native = True
        if is_h5_pay:
            url_path = url_path + 'h5'
            need_app_id = True
            ip_address = self.remote_addr
            user_agent = self.header.get('User-Agent')
            if 'iPhone' in user_agent or 'iPad' in user_agent:
                # 当前设备是 iOS
                device_type = 'iOS'
            elif 'Android' in user_agent:
                # 当前设备是 Android
                device_type = 'Android'
            else:
                # 其他设备
                device_type = 'Wap'
            data.setdefault(
                'scene_info', {
                    "payer_client_ip": ip_address,
                    "h5_info": {
                        "type": device_type
                    }
                }
            )
        elif pay_type == 'jsapi':
            url_path = url_path + 'jsapi'
            need_app_id = True
            is_native = True
        else:
            url_path = url_path + 'native'

        data.pop('pay_type', None)

        # 获取签名
        auth = self.get_auth(data, url_path)
        headers = {'Authorization': auth, 'Content-Type': 'application/json'}
        url = self.PAY_HOST + url_path
        raw = self._fetch(url, data, appid=need_app_id, is_native=is_native, headers=headers)
        return raw

    def query_native_order(self, **data):

        if "out_trade_no" not in data and "transaction_id" not in data:
            raise WechatPayError(
                "订单查询接口中，out_trade_no、transaction_id至少填一个")
        url_path = '/v3/pay/transactions/out-trade-no/{}?mchid={}'.format(
            data.get('out_trade_no'), self.mch_id)
        # 获取签名
        auth = self.get_auth(None, url_path, 'GET')
        headers = {'Authorization': auth, 'Content-Type': 'application/json'}
        url = self.PAY_HOST + url_path
        resp = self.sess.get(url, headers=headers)
        content = resp.content.decode("utf-8")
        logger.warning('WECHAT_PAY_RESULT: {}, body: {}'.format(
            content, self.to_xml(data)))
        if "return_code" in content:
            data = Map(self.to_dict(content))
            if data.return_code == FAIL:
                raise WechatPayError(data.return_msg)
            if "result_code" in content and data.result_code == FAIL:
                raise WechatPayError(data.err_code_des)
            return data
        return content

    def decrypt_callback_resource(self, resource):
        nonce = resource.get('nonce')
        associated_data = resource.get('associated_data')
        ciphertext = resource.get('ciphertext')
        if not (nonce and associated_data and ciphertext):
            return None
        key_bytes = str.encode(self.mch_key)  # APIv3_key(商户平台设置)
        nonce_bytes = str.encode(nonce)
        ad_bytes = str.encode(associated_data)
        data = base64.b64decode(ciphertext)
        aesgcm = AESGCM(key_bytes)
        plaintext = aesgcm.decrypt(nonce_bytes, data, ad_bytes)
        plaintext_str = bytes.decode(plaintext)

        return eval(plaintext_str)

