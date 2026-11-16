-- =====================================================================
-- VERIFY_003.sql — 003 软删迁移的自检（纯只读，可反复执行）
-- 用法：mysql -u<用户> -p aicrm < migrations/VERIFY_003.sql
-- 判读：每个结果集后面写了「期望」，不符合就说明迁移没跑对。
-- =====================================================================
USE aicrm;

-- ---------------------------------------------------------------------
-- 1) is_deleted / entry_url 列是否建好
--    期望 3 行：site.is_deleted、region.is_deleted（默认 0、非空）
--               site.entry_url（varchar(2048)、非空、默认空串）
-- ---------------------------------------------------------------------
SELECT TABLE_NAME       AS 表,
       COLUMN_NAME      AS 列,
       COLUMN_TYPE      AS 类型,
       IS_NULLABLE      AS 可空,
       COLUMN_DEFAULT   AS 默认值
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND (
    (TABLE_NAME IN ('crm_crawl_site', 'crm_crawl_region') AND COLUMN_NAME = 'is_deleted')
    OR (TABLE_NAME = 'crm_crawl_site' AND COLUMN_NAME = 'entry_url')
  )
ORDER BY TABLE_NAME, COLUMN_NAME;

-- ---------------------------------------------------------------------
-- 2) 唯一键是否已并入 is_deleted
--    期望：uk_site_code 两列（site_code, is_deleted）
--          uk_site_province_city 四列（site_id, province, city, is_deleted）
-- ---------------------------------------------------------------------
SELECT TABLE_NAME   AS 表,
       INDEX_NAME   AS 唯一键,
       SEQ_IN_INDEX AS 顺序,
       COLUMN_NAME  AS 列
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN ('crm_crawl_site', 'crm_crawl_region')
  AND INDEX_NAME IN ('uk_site_code', 'uk_site_province_city')
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;

-- ---------------------------------------------------------------------
-- 3) 迁移是否登记（期望 1 行）
-- ---------------------------------------------------------------------
SELECT filename, note, applied_at
FROM schema_migrations
WHERE filename = '003_soft_delete.sql';

-- ---------------------------------------------------------------------
-- 4) 现有数据盘点（期望 is_deleted 全为 0，两个 deleted 计数都是 0；
--    「缺入口地址」期望 0——有存量站点的话说明第 6 步回填没生效）
-- ---------------------------------------------------------------------
SELECT COUNT(*)                                        AS 站点总数,
       SUM(CASE WHEN is_deleted = 0 THEN 1 ELSE 0 END)  AS 正常站点,
       SUM(CASE WHEN is_deleted > 0 THEN 1 ELSE 0 END)  AS 已删站点,
       SUM(CASE WHEN is_deleted = 0 AND entry_url = ''
                THEN 1 ELSE 0 END)                      AS 缺入口地址
FROM crm_crawl_site;

SELECT COUNT(*)                                        AS 地区总数,
       SUM(CASE WHEN is_deleted = 0 THEN 1 ELSE 0 END)  AS 正常地区,
       SUM(CASE WHEN is_deleted > 0 THEN 1 ELSE 0 END)  AS 已删地区
FROM crm_crawl_region;

-- ---------------------------------------------------------------------
-- 5) 活跃行唯一性自检
--    期望：两个结果集都为空。非空说明存在「同编码/同省市多行都未删」的脏数据，
--    新唯一键装上后这类重复会让重新接入时定位到多行，需要先清理。
-- ---------------------------------------------------------------------
SELECT site_code, COUNT(*) AS 未删行数
FROM crm_crawl_site
WHERE is_deleted = 0
GROUP BY site_code
HAVING COUNT(*) > 1;

SELECT site_id, province, city, COUNT(*) AS 未删行数
FROM crm_crawl_region
WHERE is_deleted = 0
GROUP BY site_id, province, city
HAVING COUNT(*) > 1;
