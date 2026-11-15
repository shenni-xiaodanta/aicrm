"""跟进记录接口（子路由，由 com.crm.main 注册）。"""
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse

from com.crm.common.response import ok
from com.crm.followup import service
from com.crm.user.auth import require_login

router = APIRouter(prefix="/followup", tags=["跟进记录"])


@router.get("/list")
def list_follow_ups(lead_id: int, _user=Depends(require_login)):
    """查询某条商机的跟进记录（时间倒序）。"""
    return ok(service.list_follow_ups(lead_id))


@router.post("/add")
def add_follow_up(
    lead_id: int = Form(...),
    content: str = Form(...),
    files: list[UploadFile] = File(default=[]),
    user=Depends(require_login),
):
    """新增跟进记录，可同时上传多个附件。"""
    return ok(service.add_follow_up(lead_id, content, files, user["id"]), "添加成功")


@router.get("/file/{file_id}")
def download_file(file_id: int, user=Depends(require_login)):
    """下载/查看跟进附件（校验归属：负责人 / 创建人 / admin）。"""
    row, path = service.get_file(file_id, user)
    return FileResponse(
        path,
        media_type=row["content_type"] or "application/octet-stream",
        filename=row["original_name"],
    )
