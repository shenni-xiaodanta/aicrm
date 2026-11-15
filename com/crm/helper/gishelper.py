"""高德地理编码工具。

使用 .env 中的 GAODE_URL（接口地址）和 GAODE_KEY_CODE（Web 服务 key）。
所有函数失败时返回 None / (None, None)，不会向上抛异常。
"""
import logging
import os

import requests
from dotenv import load_dotenv
from typing import Optional, Tuple, Dict

logger = logging.getLogger(__name__)


def get_amap_location_precise(address: str, amap_key: str, city: Optional[str] = None) -> Optional[Tuple[float, float]]:
    """
    高德地理编码【高精度版】，可指定城市/省份缩小范围
    :param address: 详细地址
    :param amap_key: 你的高德Web服务key
    :param city: 城市名/citycode/adcode，也可传省份；为空则全国检索
    :return: (lng, lat) GCJ02 经纬度，失败返回None
    """
    url = os.getenv("GAODE_URL")
    params = {
        "key": amap_key,
        "address": address,
    }
    region = (city or "").strip()
    if region:
        # 锁定城市/省份，避免跨区域同名地址跑偏
        params["city"] = region
    try:
        resp = requests.get(url, params=params, timeout=12)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "1":
            print(f"接口失败 info={data.get('info')}, infocode={data.get('infocode')}")
            return None

        geocodes = data.get("geocodes", [])
        if not geocodes:
            print("无匹配地址")
            return None

        # 优先取level精度最高的结果（楼宇>街道>区县）
        best_item = max(geocodes, key=lambda x: {
            "building": 10,
            "street": 8,
            "district": 4,
            "city": 2
        }.get(x.get("level", ""), 0))

        loc_str = best_item.get("location")
        if not loc_str or "," not in loc_str:
            return None
        lng, lat = map(float, loc_str.split(","))
        return lng, lat

    except requests.exceptions.RequestException as e:
        print(f"网络异常：{e}")
        return None


def resolve_coords(longitude, latitude, address, province=None, city=None, amap_key=None):
    """原文有坐标就直接用；否则按地址做高德地理编码。失败返回 (None, None)。"""
    # (0, 0) 视为无效坐标：模型有时会用 0 表示“没有坐标”
    if longitude is not None and latitude is not None and not (longitude == 0 and latitude == 0):
        return longitude, latitude

    address = (address or "").strip()
    # 允许调用方显式传 key；否则回退到 .env 的 GAODE_KEY_CODE
    key = amap_key or os.getenv("GAODE_KEY_CODE", "")
    if not address or not key:
        return None, None

    # 优先城市，其次省份；都没有则不传 city，全国检索
    region = (city or "").strip() or (province or "").strip() or None
    try:
        location = get_amap_location_precise(address, key, city=region)
    except Exception as exc:
        # 地理编码失败只降级为空坐标，不阻断商机入库
        logger.warning("地理编码失败 address=%r region=%r: %s", address, region, exc)
        return None, None
    return (location[0], location[1]) if location else (None, None)


if __name__ == "__main__":
    load_dotenv(override=True)
    KEY = os.getenv("GAODE_KEY_CODE")
    addr = "南京市玄武区中山东路293号新安大厦"
    res = get_amap_location_precise(addr, KEY, city="南京市")
    if res:
        lng, lat = res
        print(f"高精度坐标 GCJ02：经度={lng}, 纬度={lat}")
