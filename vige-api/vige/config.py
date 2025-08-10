from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Tuple, List
from pathlib import Path
import os


class Settings(BaseSettings):
    ENV: str = 'local'
    DEBUG: bool = True
    SECRET_KEY: str = 'secret_key'

    WECHAT_URL_PREFIX: str = ''

    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_DATABASE_URI: str = 'postgresql://@/vige'
    SQLALCHEMY_COMMIT_ON_TEARDOWN: bool = False
    SQLALCHEMY_ECHO: bool = False

    SECURITY_PASSWORD_HASH: str = 'bcrypt'
    SECURITY_PASSWORD_SALT: str = 'pass'
    SECURITY_SEND_PASSWORD_CHANGE_EMAIL: bool = False
    SECURITY_HASHING_SCHEMES: List[str] = ['bcrypt', 'hex_md5']
    SECURITY_CONFIRMABLE: bool = True
    SECURITY_TRACKABLE: bool = True
    SECURITY_TOKEN_AUTHENTICATION_HEADER: str = 'Authorization'
    WTF_CSRF_ENABLED: bool = False

    BO_AUTH_PASSWORD_HASH: str = 'pbkdf2:sha256'
    BO_AUTH_PASSWORD_SALT_LENGTH: int = 8
    BO_AUTH_2FA_EXPIRES: int = 300
    VERIFY_CODE_TTL: int = 300

    AUTHJWT_SECRET_KEY: str = 'jwt_secret_key'
    AUTHJWT_ACCESS_TOKEN_EXPIRES: int = 3600 * 24 * 7
    AUTHJWT_TOKEN_LOCATION: List[str] = ['cookies', 'headers']
    AUTHJWT_COOKIE_SECURE: bool = True
    AUTHJWT_COOKIE_CSRF_PROTECT: bool = True
    AUTHJWT_COOKIE_SAMESITE: str = 'strict'
    AUTHJWT_ACCESS_COOKIE_KEY: str = 'vige_auth_cookie'
    AUTHJWT_ACCESS_CSRF_COOKIE_KEY: str = 'vige_auth_csrf_cookie'

    DEFAULT_TIMEZONE: str = 'Asia/Shanghai'

    PREFERRED_URL_SCHEME: str = 'http'
    EXTERNAL_URL: str = 'http://192.168.1.5:8000'

    HUEY_NAME: str = 'vige.huey'
    REDIS_HOST: str = '127.0.0.1'
    REDIS_PORT: int = 6379
    REDIS_DB: int = 10

    UPLOADS_DEFAULT_DEST: str = './instance'
    DEFAULT_THUMBNAIL_SIZE: Tuple[int, int] = (400, 400)

    SENSITIVE_KEYWORDS: Tuple[str, ...] = (
        'client_name',
        'client_mobile',
        'client_plate',
    )

    LOGGING_MAIL_SERVER: Tuple[str, int] = ('localhost', 10025)
    LOGGING_MAIL_FROM: str = 'reply@local.lan'
    LOGGING_MAIL_TO_LIST: List[str] = ['test@local.lan']

    AI_GENERATE_WORD_LIMIT: int = 10
    USER_GENERATE_WORD_MAX_COUNT: int = 50
    USER_EXCLUDE_WORD_MAX_COUNT: int = 500

    WECHAT_APP_ID: str = ''
    WECHAT_APP_SECRET: str = ''
    WECHAT_PAY_DEBUG: bool = True
    WECHAT_DEBUG_PAY_PRICE: int = 1  # 调试支付金额，单位分
    WECHAT_PAY_MCHID: str = ''  # 商户号
    WECHAT_PAY_API_V3_KEY: str = ''
    WECHAT_PAY_CERT_SERIAL_NO: str = ''
    WECHAT_PAY_PUB_KEY_ID: str = ''
    WECHAT_PAY_NOTIFY_URL: str = ''

    CACHE_TYPE: str = 'simple'
    CACHE_NO_NULL_WARNING: bool = True
    CACHE_DEFAULT_TIMEOUT: int = 300

    # SIO_NAME: str = 'vige.socketio'
    # SIO_ASYNC_MODE: str = Field(
    #     'eventlet' if 'run_sio' in sys.argv else 'threading')

    # ali config
    ALY_SMS_DOMAIN: str = 'dysmsapi.aliyuncs.com'
    ALY_SMS_SIGN_NAME: str = 'vige'
    ALY_ACCESS_KEY_ID_PLACEHOLDER: str = ''
    ALY_ACCESS_KEY_SECRET_PLACEHOLDER: str = ''
    MESSAGE_SEND_ENABLED: bool = False

    BABEL_DEFAULT_LOCALE: str = 'zh'
    BABEL_SUPPORTED_LOCALES: List[str] = ['zh', 'en']

    GPT_TOKEN: str = ''
    GPT_PROXY: str = ''
    GPT_IMAGE_RESIZE_FACTOR: int = 1
    GPT_MODAL_NAME: str = 'gpt-4o-mini'
    GPT_ADVANCED_MODAL_NAME: str = 'gpt-4o'
    GPT_MAX_WINDOW_CONTEXT: int = 128000
    GPT_MAX_OUTPUT_TOKENS: int = 1000

    GEMINI_API_KEY: str = ''

    ZHIPU_API_KEY: str = ''


script_dir = os.path.dirname(__file__)  # 获取脚本所在目录
env_file_path = os.path.join(script_dir, 'local_config.env')
config = Settings(_env_file=env_file_path)
