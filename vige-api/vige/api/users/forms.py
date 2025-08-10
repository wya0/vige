from typing import Optional
from fastapi import Depends
from pydantic import BaseModel, field_validator, ValidationError
from sqlalchemy.orm import Session
from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from ...app_factory import auth_dep
from ..bo_user.models import BoUser
from ..utils import config
from ...db import sm
from ..forms import BaseFilterForm


class UserFilterForm(BaseFilterForm):
    keyword: Optional[str] = None


class UserSendCodeForm(BaseModel):
    mobile: str

    @field_validator('mobile')
    def validate_mobile(cls, v, values):
        if not v:
            raise ValueError('手机号为必填项')
        # 验证手机号
        if not v.isdigit():
            raise ValueError('手机号格式错误')
        if len(v) != 11:
            raise ValueError('手机号格式错误')
        return v


class UserLoginForm(BaseModel):
    mobile: str
    code: str

    @field_validator('mobile')
    def validate_mobile(cls, v, values):
        if not v:
            raise ValueError('手机号为必填项')
        # 验证手机号
        if not v.isdigit():
            raise ValueError('手机号格式错误')
        if len(v) != 11:
            raise ValueError('手机号格式错误')
        return v

    @field_validator('code')
    def validate_code(cls, v, values):
        if not v:
            raise ValueError('验证码为必填项')
        if not v.isdigit():
            raise ValueError('验证码格式错误')
        if len(v) != 6:
            raise ValueError('验证码格式错误')
        return v