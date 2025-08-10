import uuid
from fastapi import UploadFile, File
from ...db import sm
from .. import router as app
from ..jwt import login_required, get_user
from ..utils import abort_json
from .forms import ImageForm, AudioForm, ALLOWED_IMAGE_EXTENSIONS
from .models import MediaModel
from ...config import config


@app.post('/media')
@login_required
async def upload_image(image: UploadFile = File(...)):
    ext = image.filename.split('.')[-1]
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise abort_json(400, '图片格式错误')
    key = uuid.uuid4().hex
    secure_filename = f"image_{key}.{ext}"
    filepath = config.UPLOADS_DEFAULT_DEST
    # 保存文件
    with open(f"{filepath}/{secure_filename}", "wb") as buffer:
        buffer.write(await image.read())

    with sm.transaction_scope() as sa:
        m = MediaModel.create(sa, profile={})
        m.filename = secure_filename
        m.save_thumbnail(secure_filename)
        sa.commit()
        data = m.dump()
    return dict(
        success=True,
        data=data,
    )



