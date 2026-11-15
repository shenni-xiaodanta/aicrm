"""采集源配置业务层。"""
import logging

from com.crm.common.exceptions import BizException
from com.crm.helper.texthelper import clip
from com.crm.helper.urlhelper import is_origin, normalize_source
from com.crm.source import dao

logger = logging.getLogger(__name__)


def get_source(province, city):
    """查询已保存的采集源配置。"""
    province = (province or "").strip()
    city = (city or "").strip()
    if not province or not city:
        raise BizException("省市不能为空", code=1000)
    return dao.get_source(province, city)


def save_source(province, city, base_domain, list_url):
    """保存采集源配置（按省+市覆盖）。"""
    province = (province or "").strip()
    city = (city or "").strip()
    # 用户常把完整列表页填进 base_domain、把域名填进 list_url，
    # 这里先自动交换，再做严格校验。
    base_domain, list_url = normalize_source(base_domain, list_url)

    if not province or not city:
        raise BizException("省市不能为空", code=1000)
    if not is_origin(base_domain):
        raise BizException(
            "base_domain 只能填站点根域名，例如 https://ggzy.hefei.gov.cn",
            code=1000,
        )
    if is_origin(list_url):
        raise BizException("list_url 需要填完整列表页地址，不能只填域名", code=1000)
    if not list_url.startswith(("http://", "https://")):
        raise BizException("list_url 必须以 http:// 或 https:// 开头", code=1000)

    dao.save_source(
        province, city, clip(base_domain, 255), clip(list_url, 2048)
    )
    logger.info("保存采集源 %s/%s", province, city)
    return dao.get_source(province, city)
