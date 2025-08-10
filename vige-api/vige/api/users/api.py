import logging
from fastapi import Depends, Request, Response, HTTPException
from async_fastapi_jwt_auth import AuthJWT
from fastapi.responses import RedirectResponse
from jinja2 import Template
from sqlalchemy.orm import Session
from ...app_factory import auth_dep

from ...db import sm
from .. import router as app
from ..decorators import validates, validates_args
from ..jwt import get_user, user_required
from ..wechat import wechat
from .forms import BaseFilterForm, UserSendCodeForm, UserLoginForm
from .models import User
from ...config import config
from ..bo_user.verify_code import code_verification

logger = logging.getLogger(__name__)


@app.get('/web/users/me')
@user_required
async def web_user_me(user: User = Depends(get_user)):
    return dict(success=True, user=user.dump())


@app.post('/web/send_code')
@user_required
async def send_validation_code(form: UserSendCodeForm,
                               db: Session = Depends(sm.get_db)):
    mobile = form.mobile
    user = db.query(User).filter_by(mobile=mobile).first()
    if user and user.disabled_at:
        raise HTTPException(status_code=400, detail='用户已禁用')
    User.send_login_verification_code(mobile)
    return dict(success=True)


@app.post('/web/login')
@user_required
async def app_login(form: UserLoginForm,
                    db: Session = Depends(sm.get_db),
                    authorize: AuthJWT = Depends(auth_dep)):
    mobile = form.mobile
    code = form.code
    if not code_verification.is_code_valid(mobile):
        return dict(success=False, code=400, message='验证码已过期，请重新获取')
    if not code_verification.verify(mobile, code, True):
        raise HTTPException(status_code=400, detail='验证码错误')
    user = db.query(User).filter_by(mobile=mobile).first()
    user_info = None
    user_id = None
    if not user:
        with sm.transaction_scope() as sa:
            user = User.create(sa, profile={}, mobile=mobile)
            user.source = 'pc'
            user_id = user.id
            sa.commit()
            user_info = user.auth_dump()
    else:
        user_id = user.id
        user_info = user.auth_dump()
        with sm.transaction_scope() as sa:
            user.source = 'pc'
            sa.commit()
        if user.disabled_at:
            raise HTTPException(status_code=400, detail='用户已禁用')
    user_info['utype'] = 'web'
    # 返回token
    token = await authorize.create_access_token(
        user_id,
        user_claims=user_info)
    await authorize.set_access_cookies(
        token, max_age=config.AUTHJWT_ACCESS_TOKEN_EXPIRES)

    return dict(success=True)


@app.post('/web/logout')
@user_required
async def web_logout(authorize: AuthJWT = Depends(auth_dep)):
    resp = dict(success=True)
    await authorize.jwt_required()
    await authorize.unset_jwt_cookies()
    return resp


