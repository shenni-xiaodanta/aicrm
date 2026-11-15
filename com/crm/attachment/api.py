"""附件管理接口（子路由，由 com.crm.main 注册）。"""
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse

from com.crm.attachment import service
from com.crm.common.response import ok
from com.crm.user.auth import require_login

router = APIRouter(prefix="/attachment", tags=["附件管理"])


@router.get("/list")
def list_attachments(lead_id: int, _user=Depends(require_login)):
    """查询某条商机的附件记录（时间倒序）。"""
    return ok(service.list_attachments(lead_id))


@router.post("/add")
def add_attachment(
    lead_id: int = Form(...),
    category: str = Form(...),
    description: str = Form(""),
    files: list[UploadFile] = File(default=[]),
    user=Depends(require_login),
):
    """新增附件记录，可带说明文字和多个附件。"""
    return ok(
        service.add_attachment(lead_id, category, description, files, user["id"]),
        "提交成功",
    )


@router.get("/file/{file_id}")
def download_file(file_id: int, user=Depends(require_login)):
    """下载/查看附件（校验归属：负责人 / 创建人 / admin）。"""
    row, path = service.get_file(file_id, user)
    return FileResponse(
        path,
        media_type=row["content_type"] or "application/octet-stream",
        filename=row["original_name"],
    )
