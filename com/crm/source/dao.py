"""采集源配置 DAO（数据访问层）。"""
from com.crm.common.basedao import execute, query_one

TABLE = "crm_crawl_source"


def get_source(province, city):
    """查询某个地级市已保存的采集源配置。"""
    return query_one(
        f"SELECT id, province, city, base_domain, list_url, "
        f"create_time, update_time FROM {TABLE} "
        "WHERE province = %s AND city = %s",
        (province, city),
    )


def save_source(province, city, base_domain, list_url):
    """按“省+市”新增或更新采集源配置。"""
    sql = (
        f"INSERT INTO {TABLE} (province, city, base_domain, list_url) "
        "VALUES (%s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE "
        "base_domain = VALUES(base_domain), list_url = VALUES(list_url)"
    )
    return execute(sql, (province, city, base_domain, list_url))
