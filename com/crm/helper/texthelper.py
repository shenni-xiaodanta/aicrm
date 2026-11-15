"""文本与 JSON 工具函数。"""
import json


def clip(value, length):
    """裁剪字符串，避免超过数据库列宽。"""
    return (value or "").strip()[:length]


def json_list(items):
    """字符串列表序列化为 JSON 数组。"""
    return json.dumps(
        [str(item).strip() for item in items if str(item).strip()],
        ensure_ascii=False,
    )
