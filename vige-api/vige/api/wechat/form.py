from pydantic import BaseModel, Field
from typing import Optional


class WechatDecryptForm(BaseModel):
    """微信解密表单"""
    iv: str = Field(..., description="微信加密向量", min_length=1)
    encryptedData: str = Field(..., description="微信加密数据", min_length=1)
    code: str = Field(..., description="微信code", min_length=1)
    bind_id: Optional[str] = Field(None, description="绑定用户ID")

    class Config:
        json_schema_extra = {
            "example": {
                "iv": "iv_example",
                "encryptedData": "encrypted_data_example", 
                "code": "wx_code_example",
                "bind_id": "123"
            }
        }
