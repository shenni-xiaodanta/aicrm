"""附件管理业务层：类型校验、说明文字、多附件保存。

附件规则与跟进模块共用 helper/filehelper.py。
CATEGORIES 对应招投标、立项页签的固定文件类型。
"""
import logging
import uuid
from pathlib import Path

from com.crm.attachment import dao
from com.crm.common.config import PROJECT_ROOT
from com.crm.common.exceptions import BizException
from com.crm.helper.filehelper import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    MAX_FILES,
    file_suffix,
)
from com.crm.helper.texthelper import clip

logger = logging.getLogger(__name__)

UPLOAD_DIR = PROJECT_ROOT / "uploads" / "attachment"
CATEGORIES = {"招标文件", "投标文件", "投标结果", "方案", "报价", "合同"}


def list_attachments(lead_id):
    """查询某条商机的附件记录。"""
    if int(lead_id) <= 0:
        raise BizException("商机ID无效", code=1000)
    return dao.list_by_lead(int(lead_id))


def add_attachment(lead_id, category, description, files):
    """新增一条附件记录，可带说明文字和多个附件。"""
    lead_id = int(lead_id)
    category = (category or "").strip()
    description = (description or "").strip()

    if lead_id <= 0:
        raise BizException("商机ID无效", code=1000)
    if category not in CATEGORIES:
        raise BizException("附件类型无效", code=1000)
    if len(description) > 2000:
        raise BizException("说明文字不能超过 2000 字", code=1000)

    files = files or []
    if len(files) > MAX_FILES:
        raise BizException(f"一次最多上传 {MAX_FILES} 个附件", code=1000)
    if not description and not files:
        raise BizException("请填写说明或选择附件", code=1000)

    # 先整体校验，避免保存一半才发现文件不合法。
    # Path(...).name 去掉文件名中的路径，防止 ../../ 路径穿越。
    prepared = []
    for upload in files:
        original_name = clip(Path(upload.filename or "").name, 255)
        suffix = file_suffix(original_name)
        if suffix not in ALLOWED_EXTENSIONS:
            raise BizException(f"不支持的附件类型：{original_name}", code=1000)
        if (upload.size or 0) > MAX_FILE_SIZE:
            raise BizException(f"附件超过 10MB：{original_name}", code=1000)
        prepared.append((upload, original_name, suffix))

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    record_id = dao.insert_record(lead_id, category, description)
    saved_paths = []
    try:
        for upload, original_name, suffix in prepared:
            # 磁盘文件名用 UUID，原始文件名只存数据库用于展示/下载
            stored_name = f"{uuid.uuid4().hex}{suffix}"
            path = UPLOAD_DIR / stored_name
            saved_paths.append(path)
            size = 0
            with path.open("wb") as out:
                # upload.size 来自请求头，不可信；按实际字节数再次校验 10MB 上限
                while True:
                    chunk = upload.file.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > MAX_FILE_SIZE:
                        raise BizException(
                            f"附件超过 10MB：{original_name}", code=1000
                        )
                    out.write(chunk)
            dao.insert_file(
                record_id, lead_id, original_name, stored_name,
                size, clip(upload.content_type, 120),
            )
    except Exception:
        # 任意文件或数据库写入失败：删除已落盘文件和父记录，避免留下半截数据。
        # 所有删除都是 best-effort，原始异常继续向上抛。
        for path in saved_paths:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        dao.delete_record(record_id)
        raise

    logger.info(
        "新增附件 lead_id=%s record_id=%s category=%s files=%s",
        lead_id, record_id, category, len(prepared),
    )
    return {"id": record_id}


def get_file(file_id):
    """返回附件文件元数据和磁盘路径。"""
    # 先查元数据再确认磁盘文件存在，避免数据库有记录但文件被手工删除
    row = dao.get_file(file_id)
    if not row:
        raise BizException("附件不存在", code=1000)
    path = UPLOAD_DIR / row["stored_name"]
    if not path.exists():
        raise BizException("附件文件不存在", code=1000)
    return row, path
