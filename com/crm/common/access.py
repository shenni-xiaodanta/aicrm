# -*- coding: utf-8 -*-
"""
附件/作业痕迹的访问校验

权限口径（2026-11-15 需求确认）：
- 商机本身全员共享——公告是公开情报，藏着没意义；
- 但跟进记录、报价单、资质材料是「作业痕迹」，必须按归属隔离，
  否则改个 file_id 就能把别人准备投标的报价单下载走。

可下载人 = 商机负责人 / 记录创建人 / admin，三类之外一律拒绝。

历史坑：接口原来只判断「是否登录」，任意登录用户遍历 file_id
就能下载全公司招投标文件——这不是设计取舍，是真漏洞（AR-D03）。
"""
from com.crm.common.exceptions import BizException


def ensure_lead_file_access(user, lead_owner_id, created_by):
    """下载跟进/附件文件前校验归属，无权时抛业务异常。

    参数：
    - user: require_login 返回的用户 dict（含 id / role）
    - lead_owner_id: 该文件所属商机的负责人 user_id，可为 None（未分配）
    - created_by: 该文件所在记录的创建人 user_id

    存量兜底：created_by 为 NULL 的历史记录没有创建人信息，无法归属，
    保持旧行为放行（否则升级当天大家下载不了自己一直用的文件）。
    新写入的记录都带 created_by，存量走完自然过渡；见 migrations/001_baseline.sql。
    """
    uid = int(user["id"])
    if user.get("role") == "admin":
        return
    if lead_owner_id and int(lead_owner_id) == uid:
        return
    if created_by is None:      # 存量数据：无创建人信息，维持旧行为
        return
    if int(created_by) == uid:
        return

    # 统一说「附件不存在」而不是「无权访问」：不区分「不存在」和「无权」，
    # 攻击者无法通过响应差异探测某个文件是否存在（404 语义）
    raise BizException("附件不存在", code=1000)
