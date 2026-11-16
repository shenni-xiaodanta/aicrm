"""采集模块路由：地区列表 / 发起采集 / 任务进度 / 站点配方。"""
import json

from fastapi import APIRouter, Depends, Form

from com.crm.common.exceptions import BizException
from com.crm.common.response import fail, ok
from com.crm.crawl import service
from com.crm.user.auth import require_admin, require_login

router = APIRouter(prefix="/crawl", tags=["crawl"])


@router.get("/regions")
def list_regions(_user=Depends(require_login)):
    """地区采集点列表（含所属站点摘要），采集弹窗下拉数据源。"""
    return ok(service.list_regions())


@router.get("/tasks")
def list_tasks(limit: int = 50, _user=Depends(require_login)):
    """最近采集任务列表（含进度与失败明细），任务页数据源。"""
    return ok(service.list_tasks(limit))


@router.get("/task/{task_id}")
def get_task(task_id: int, _user=Depends(require_login)):
    """单个任务快照，前端发起采集后按它轮询进度。"""
    return ok(service.get_task(task_id))


@router.post("/start")
def start_crawl(region_id: int = Form(...), user=Depends(require_login)):
    """发起一次地区采集：立即返回 task_id，抓取在后台线程执行。"""
    try:
        return ok(service.start_crawl(region_id, user["id"]), "采集任务已启动")
    except BizException as exc:
        return fail(exc.msg, code=exc.code)
    except Exception:
        service.logger.exception("发起采集失败 region_id=%s", region_id)
        return fail("服务器异常：发起采集失败", code=1000)


@router.post("/probe")
def probe_site(
    list_url: str = Form(...),
    site_code: str = Form(None),
    site_name: str = Form(None),
    province: str = Form(None),
    city: str = Form(None),
    _user=Depends(require_admin),
):
    """探测任意列表页 URL，LLM 生成解析配方并入库。

    流程：下载入口页 → 模型读骨架出选择器/翻页模板 → 真页面回验
    （列表/正文/翻页）→ 新建或覆盖站点模板 → 按需登记地区采集点。
    会同步等待模型与数次真实请求（约 30~60 秒），失败返回可读原因。
    """
    try:
        return ok(
            service.probe_site(
                list_url,
                site_code=site_code,
                site_name=site_name,
                province=province,
                city=city,
            ),
            "探测成功，站点模板已保存",
        )
    except BizException as exc:
        return fail(exc.msg, code=exc.code)
    except Exception:
        service.logger.exception("站点探测失败 list_url=%s", list_url)
        return fail("服务器异常：站点探测失败", code=1000)


# ---------------------------------------------------------------------
# 站点配方：读取全员可见，修改仅 admin（配方是全站共用的解析规则，
# 改错一个选择器会影响所有地区的采集结果）
# ---------------------------------------------------------------------
@router.get("/sites")
def list_sites(_user=Depends(require_login)):
    return ok(service.list_sites())


@router.put("/sites/{site_id}")
def update_site(
    site_id: int,
    selectors: str = Form(None),
    pagination: str = Form(None),
    charset: str = Form(None),
    render_mode: str = Form(None),
    request_interval: float = Form(None),
    max_retry: int = Form(None),
    max_pages: int = Form(None),
    enabled: int = Form(None),
    _user=Depends(require_admin),
):
    """更新站点配方。selectors/pagination 传 JSON 字符串，此处校验可解析。"""
    fields = {}
    for name, raw in (("selectors", selectors), ("pagination", pagination)):
        if raw:
            try:
                fields[name] = json.loads(raw)
            except (TypeError, ValueError):
                return fail(f"{name} 不是合法的 JSON", code=1000)
    if charset is not None:
        fields["charset"] = charset.strip()
    if render_mode is not None:
        fields["render_mode"] = render_mode.strip()
    for name, value in (("request_interval", request_interval),
                        ("max_retry", max_retry), ("max_pages", max_pages)):
        if value is not None:
            fields[name] = value
    if enabled is not None:
        fields["enabled"] = 1 if enabled else 0

    try:
        return ok(service.update_site(site_id, fields), "站点配方已更新")
    except BizException as exc:
        return fail(exc.msg, code=exc.code)
    except Exception:
        service.logger.exception("更新站点配方失败 site_id=%s", site_id)
        return fail("服务器异常：更新站点配方失败", code=1000)
