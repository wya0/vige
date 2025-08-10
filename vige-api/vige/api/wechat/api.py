import hashlib
import uuid
import time
import xml.etree.ElementTree as ET
import logging

from fastapi import Request, Query, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from .. import router as app
from ...db import sm
from ..utils import config, settings, raise_bad_request
from ..jwt import get_user, user_required, wechat_required
from .wechat import wechat
from ..users.models import User

logger = logging.getLogger(__name__)


def check_signature(signature, timestamp, nonce):
    token = settings.wechat_event_token
    logger.debug(f'Checking signature with token: {token}')
    logger.debug(f'Checking signature: {signature}, {timestamp}, {nonce}, {token}')
    key = ''.join(sorted([timestamp, nonce, token]))
    sha1 = hashlib.sha1(key.encode('utf-8')).hexdigest()
    logger.debug(f'Computed SHA1: {sha1}, Given Signature: {signature}')
    return signature == sha1


@app.get('/wechat/orange/qr_code',
         summary="获取橙子二维码",
         description="获取用于绑定用户的二维码",
         tags=["💬 微信端接口"])
@user_required
async def get_orange_qr(current_user: User = Depends(get_user)):
    qr = wechat.create_qr_code(f'gpt_{current_user.mobile}')
    ticket = qr.get('ticket', None)
    if not ticket:
        logger.warning(f'Create qr code failed with error: {qr}')
        return dict(success=False, data={})

    return dict(
        success=True,                                   # 操作是否成功
        data={
            "qr_img": wechat.get_qr_img_url(ticket)     # 二维码图片的完整URL地址
        }
    )


@app.post('/wechat/orange/bind_user',
          summary="绑定GPT用户",
          description="通过openid绑定GPT用户",
          tags=["💬 微信端接口"])
@wechat_required
async def bind_gpt_user(request: Request):
    request_data = await request.json()
    mobile = request_data.get('mobile')
    if not mobile:
        raise_bad_request('手机号不能为空')
    openid = request_data.get('openid')
    if not openid:
        raise_bad_request('openid不能为空')

    with sm.transaction_scope() as db:
        user = db.query(User).filter(
            User.mobile == mobile,
        ).first()
        if not user:
            raise_bad_request('用户不存在')
        if not user.openid:
            user.openid = openid

    return dict(
        success=True,    # 操作是否成功
        data={}          # 空数据对象，绑定操作无需返回额外数据
    )


@app.get('/wechat/wx_configs',
         summary="获取微信JS-SDK配置",
         description="获取微信JS-SDK所需的配置信息",
         tags=["💬 微信端接口"])
async def wx_configs(url: str = Query(..., description="当前页面URL")):
    jsapi_ticket = wechat.jsapi_ticket
    if not jsapi_ticket:
        return dict(success=False, data={})
    jsapi_ticket = jsapi_ticket.decode('utf-8')
    app_id = config.WECHAT_APP_ID
    url = url.split('#', 1)[0]
    ts = int(time.time())
    nonce = uuid.uuid4().hex
    payload = f'jsapi_ticket={jsapi_ticket}&noncestr={nonce}&timestamp={ts}&' \
              f'url={url}'.encode('utf-8')
    sig = hashlib.sha1(payload).hexdigest()
    resp = dict(
        success=True,                   # 操作是否成功
        data={
            "appid": app_id,            # 微信应用ID，用于初始化JS-SDK
            "noncestr": nonce,          # 随机字符串，用于签名计算
            "timestamp": ts,            # 时间戳，签名计算的参数之一
            "signature": sig,           # JS-SDK配置签名，验证调用合法性
        }
    )
    return resp


@app.get('/wechat/events', response_class=PlainTextResponse)
async def wechat_server_validate(
    signature: str = Query(..., description="微信签名"),
    timestamp: str = Query(..., description="时间戳"),
    nonce: str = Query(..., description="随机数"),
    echostr: str = Query(None, description="随机字符串")
):
    if check_signature(signature, timestamp, nonce):
        logger.warning(f'-------- check success echostr: {echostr}')
        return echostr or ''
    else:
        return ''


@app.post('/wechat/events',
          response_class=PlainTextResponse,
          summary="微信事件推送",
          description="处理微信事件推送",
          tags=["💬 微信端接口"])
async def wechat_events(request: Request):
    data = await request.body()
    root = ET.fromstring(data)
    wechat_xml = {}
    for child in root:
        wechat_xml[child.tag] = child.text

    from_username = wechat_xml.get('FromUserName')
    scene = None
    event = (wechat_xml.get('Event') or '').lower().strip()
    event_key = wechat_xml.get('EventKey')
    if event == 'subscribe' and event_key and event_key.startswith('qrscene_'):
        scene = event_key.replace('qrscene_', '')
    elif event == 'scan':
        scene = event_key

    logger.info(f"wechat event scene={scene} from={from_username}")
    # TODO: handle scene
    return ''


