"""跟进记录业务层：内容校验、附件保存。

附件规则（类型/大小/数量）与附件管理模块共用 helper/filehelper.py。
"""
import logging
import uuid
from pathlib import Path

from com.crm.common.config import PROJECT_ROOT
from com.crm.common.db import tx
from com.crm.common.exceptions import BizException
from com.crm.common.access import ensure_lead_file_access
from com.crm.followup import dao
from com.crm.helper.filehelper import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    MAX_FILES,
    file_suffix,
)
from com.crm.helper.texthelper import clip

logger = logging.getLogger(__name__)

UPLOAD_DIR = PROJECT_ROOT / "uploads" / "followup"


def list_follow_ups(lead_id):
    """查询某条商机的跟进记录。"""
    if int(lead_id) <= 0:
        raise BizException("商机ID无效", code=1000)
    return dao.list_by_lead(int(lead_id))


def add_follow_up(lead_id, content, files, user_id):
    """新增跟进记录，并保存上传的附件。"""
    lead_id = int(lead_id)
    content = (content or "").strip()

    if lead_id <= 0:
        raise BizException("商机ID无效", code=1000)
    if not content:
        raise BizException("跟进内容不能为空", code=1000)
    if len(content) > 2000:
        raise BizException("跟进内容不能超过 2000 字", code=1000)

    files = files or []
    if len(files) > MAX_FILES:
        raise BizException(f"一次最多上传 {MAX_FILES} 个附件", code=1000)

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
    # 主记录 + N 条附件记录放同一个事务：原来逐次自动提交，中途失败要靠
    # delete_follow_up 手工"反向回滚"；现在 rollback 一次兜底，磁盘文件仍需自行清理
    # （文件系统无法参与数据库事务）。数据库行已先落库再写盘，失败时事务回滚会
    # 撤销全部行，磁盘只可能有已写入的孤儿文件，逐个 unlink。
    saved_paths = []
    try:
        with tx():
            follow_up_id = dao.insert_follow_up(lead_id, content, user_id)
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
                    follow_up_id, lead_id, original_name, stored_name,
                    size, clip(upload.content_type, 120),
                )
    except Exception:
        # 事务已整体回滚数据库行；这里只清理已落盘的孤儿文件（best-effort），
        # 原始异常继续向上抛。
        for path in saved_paths:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        raise

    logger.info(
        "新增跟进 lead_id=%s follow_up_id=%s files=%s",
        lead_id, follow_up_id, len(prepared),
    )
    return {"id": follow_up_id}


def get_file(file_id, user):
    """返回附件元数据和磁盘路径；下载前做归属校验（越权修复，AR-D03）。

    校验放 service 而不是 api：文件归属信息（lead_id/created_by）来自 dao，
    service 是业务规则的归属层；api 只做参数分发。
    """
    # 先查元数据再确认磁盘文件存在，避免数据库有记录但文件被手工删除
    row = dao.get_file(file_id)
    if not row:
        raise BizException("附件不存在", code=1000)
    # 鉴权放在查磁盘之前：无权访问时不必暴露文件是否真的存在
    lead = dao.get_lead_owner(row["lead_id"])
    ensure_lead_file_access(user, lead.get("owner_id") if lead else None, row.get("created_by"))
    path = UPLOAD_DIR / row["stored_name"]
    if not path.exists():
        raise BizException("附件文件不存在", code=1000)
    return row, path
