import base64
import json
import logging
import re
import time
import requests
from Crypto.Cipher import AES

from urllib.parse import urlencode
from mimeparse import parse_mime_type

from ..utils import config
from ...app_factory import get_redis_client

logger = logging.getLogger(__name__)

WX_URI_PREFIX = 'https://api.weixin.qq.com'
WECHAT_OAUTH_URL = 'https://open.weixin.qq.com/connect/oauth2/authorize?' \
                   'appid={app_id}&redirect_uri={redirect_uri}&' \
                   'response_type=code&scope=snsapi_userinfo&' \
                   'state={state}#wechat_redirect'
ACCESS_TOKEN_KEY = 'ACCESS_TOKEN_KEY'
JSAPI_TICKET_KEY = 'JSAPI_TICKET_KEY'


def b64encode(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('utf-8')


class WeChatError(Exception):

    @property
    def errcode(self):
        if self.args:
            return self.args[0].get('errcode', 0)
        return 0

    @property
    def errmsg(self):
        if self.args:
            return self.args[0].get('errmsg', 'Wechat error')
        return None


class WeChatHTTPError(WeChatError):
    pass


class WeChatAPIError(WeChatError):
    pass


class Wechat:

    @property
    def app_id(self):
        return config.WECHAT_APP_ID

    @property
    def app_secret(self):
        return config.WECHAT_APP_SECRET

    @property
    def access_token(self):
        redis_client = get_redis_client()
        token = redis_client.get(ACCESS_TOKEN_KEY)
        if not token:
            from .tasks import refresh_wx_token
            refresh_wx_token()
        return token

    @property
    def jsapi_ticket(self):
        redis_client = get_redis_client()
        ticket = redis_client.get(JSAPI_TICKET_KEY)
        if not ticket:
            from .tasks import refresh_jsapi_ticket
            refresh_jsapi_ticket()
        return ticket

    @property
    def oauth_url(self):
        redirect_uri = f"{config.EXTERNAL_URL}/v1/wechat/oauth"
        url = WECHAT_OAUTH_URL.format(**dict(
            app_id=self.app_id,
            redirect_uri=redirect_uri,
            state=str(time.time())
        ))
        return url

    def _do_request(self, method, uri, params,
                    _prefix=WX_URI_PREFIX, data=None, **kwargs):
        url = _prefix + uri
        logger.info("WX API request: %s %s", method, url)
        logger.debug("WX API request: %s %s %r %r", method, url, params, kwargs)
        if data:
            data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        resp = requests.request(
            method, url, params=params, data=data,
            headers={'Content-Type': 'application/json', 'encoding': 'utf-8'},
            **kwargs)
        if resp.status_code != 200:
            logger.error("Wechat server returned: %r", resp.status_code)
            err = {'errcode': resp.status_code,
                   'errmsg': "HTTP Error: {} {}".format(resp.status_code,
                                                        resp.url)}
            raise WeChatHTTPError(err)
        ctype = resp.headers.get('Content-Type')
        try:
            mtype, stype, c_params = parse_mime_type(ctype)
        except:
            # Hot fix: (个别图片下载请求返回的 content-type 是 "image")
            logger.error("WechatAPI: can't parse mime type:{}".format(ctype))
            mtype, stype, c_params = (ctype, None, None)
        if (mtype, stype) in (('text', 'plain'), ('application', 'json')):
            data = resp.json()
            err_code = data.get('errcode', 0)
            if err_code != 0:
                logger.error(
                    "WechatAPI: Application error: %s, %s", err_code,
                    data.get('errmsg', ''))
                if err_code in (40001, 41001, 40014, 42001):
                    redis_client = get_redis_client()
                    redis_client.delete('WECHAT_ACCESS_TOKEN')
                    from .tasks import refresh_wx_token
                    refresh_wx_token()
                raise WeChatAPIError(data)
        else:
            content = b64encode(resp.content)
            try:
                filename = re.search(
                    'attachment; filename="(.+?)"',
                    resp.headers.get('CONTENT-DISPOSITION', '')).group(1)
            except AttributeError:
                filename = ''
            # Hot fix: (个别图片下载请求返回的 content-type 是 "image")
            try:
                ext = resp.headers['CONTENT-TYPE'].split('/')[1]
            except:
                logger.error(
                    "WechatAPI: can't parse ext: {}".format(resp.headers))
                ext = filename.split('.')[1]
            if ext.lower() == 'jpg':
                ext = 'jpeg'
            data = {
                'filename': filename,
                # XXX: use `stype` here?
                'ext': ext,
                'content': content,
            }
        return data

    def get(self, uri, params, **kwargs):
        return self._do_request('get', uri, params, **kwargs)

    def post(self, uri, params, **kwargs):
        return self._do_request('post', uri, params, **kwargs)

    def get_oauth_access_token(self, code):
        resp = self.get('/sns/oauth2/access_token', dict(
            appid=self.app_id,
            secret=self.app_secret,
            code=code,
            grant_type='authorization_code'
        ))
        return resp

    def refresh_oauth_access_token(self, refresh_token):
        resp = self.get('/sns/oauth2/refresh_token', dict(
            appid=self.app_id,
            grant_type='refresh_token',
            refresh_token=refresh_token,
        ))
        return resp

    def get_user_info(self, access_token, openid):
        resp = self.get('/sns/userinfo', dict(
            access_token=access_token,
            openid=openid,
            lang='zh_CN'
        ))
        return resp

    def create_qr_code(self, scene, action='QR_STR_SCENE', expires=600):
        """
        Create Wechat QR code, see: https://mp.weixin.qq.com/wiki?t=resource/res_main&id=mp1443433542
        """

        scene_key = 'scene_id' if isinstance(scene, int) else 'scene_str'

        resp = self.post(
            f'/cgi-bin/qrcode/create', dict(access_token=self.access_token),
            data=dict(
                expire_seconds=expires, action_name=action,
                action_info=dict(
                    scene={scene_key: scene}
                )
            ))
        return resp

    def send_text_message(self, openid, text):
        message = {'touser': openid,
                   'msgtype': 'text',
                   'text': {'content': text}
                   }
        self.post(
            '/cgi-bin/message/custom/send',
            dict(access_token=self.access_token),
            data=message)

    @staticmethod
    def get_qr_img_url(ticket):
        ticket = urlencode(dict(ticket=ticket))
        return f'https://mp.weixin.qq.com/cgi-bin/showqrcode?{ticket}'

    """
       小程序相关
       """

    # 发送模板消息
    def send_mp_subscribe_message(self, openid, template, data):
        message = {'touser': openid,
                   'template_id': template,
                   'data': data
                   }
        self.post(
            '/cgi-bin/message/subscribe/send',
            dict(access_token=self.access_token),
            data=message)

    # 微信小程序 code 获取 session_key
    def code_to_session_key(self, code):
        app_id = self.app_id
        app_secret = self.app_secret
        resp = self.get('/sns/jscode2session', dict(
            appid=app_id,
            secret=app_secret,
            js_code=code,
            grant_type='authorization_code'
        ))
        logger.warning(f'WeChatAPI: code_to_session_key resp: {resp}')
        return resp

    # 微信小程序解密用户信息
    def decrypt_user_info(self, session_key, encrypted_data, iv):
        app_id = self.app_id
        session_key = base64.b64decode(session_key)
        encrypted_data = base64.b64decode(encrypted_data)
        iv = base64.b64decode(iv)

        cipher = AES.new(session_key, AES.MODE_CBC, iv)

        decrypted = json.loads(
            self._unpad(cipher.decrypt(encrypted_data)).decode())

        if decrypted['watermark']['appid'] != app_id:
            raise WeChatError('Invalid Buffer')
        # return phone number only
        return decrypted['phoneNumber']

    # 微信小程序解码函数
    def _unpad(self, s):
        return s[:-ord(s[len(s) - 1:])]


wechat = Wechat()
