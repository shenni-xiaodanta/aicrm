-- =====================================================================
-- 003_soft_delete.sql — 站点 / 地区软删（幂等，可重复执行）
-- 执行方式：由项目所有者手工执行（约定：AI 不直接操作数据库）
--   mysql -u<用户> -p aicrm < migrations/003_soft_delete.sql
-- 执行顺序：先跑本脚本，再部署本批代码（否则删除按钮会报 SQL 错误）
-- ---------------------------------------------------------------------
-- 背景：
--   1) 「停用站点/地区」这一层概念取消——站点失效的唯一处理方式是删除
--      （网址没了就删，临时故障等恢复后重新探测即可，失败记录留在任务表）。
--   2) 但站点 / 地区不能硬删：crm_crawl_task 靠 region_id / site_id
--      JOIN 出省市与站点名，硬删会让历史任务 JOIN 断掉、直接从列表消失。
--   3) 因此统一软删：is_deleted = 0 表示正常，删除时写 is_deleted = 本行 id。
--   4) 顺带给站点补 entry_url：记住探测时的入口页，给已有站点「添加地区」
--      时用它当入口地址（用户只填省市，不该被要求知道网址）。
-- ---------------------------------------------------------------------
-- 为什么必须同时调整唯一键：
--   site_code 原本全局唯一。删掉「中国政府采购网」后想重新探测同一个站，
--   已删的旧行仍占着 ccgp_gov_cn → 插不进去。把 is_deleted 并入唯一键后，
--   活跃行（is_deleted = 0）仍然唯一，已删行各自持有自己的 id、互不冲突，
--   历史行再也不会挡住重新接入。
--   地区唯一键 (site_id, province, city) 同理：删过的省市要能重新登记。
-- ---------------------------------------------------------------------
-- 幂等实现：MySQL 的 ADD COLUMN / DROP INDEX 没有 IF [NOT] EXISTS，
-- 这里用 information_schema 判断 + 动态 SQL，重复执行不会报 1060 / 1091。
-- =====================================================================
USE aicrm;

-- ---------------------------------------------------------------------
-- 1) crm_crawl_site：加 is_deleted 列（0=正常，非0=删除时的行 id）
-- ---------------------------------------------------------------------
SET @sql = IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'crm_crawl_site'
      AND COLUMN_NAME = 'is_deleted') = 0,
  'ALTER TABLE `crm_crawl_site` ADD COLUMN `is_deleted` bigint unsigned NOT NULL DEFAULT 0 AFTER `enabled`',
  'SELECT ''crm_crawl_site.is_deleted 已存在，跳过'' AS skip_msg'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------
-- 2) crm_crawl_site：唯一键 uk_site_code 改为 (site_code, is_deleted)
-- ---------------------------------------------------------------------
SET @sql = IF(
  (SELECT COUNT(*) FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'crm_crawl_site'
      AND INDEX_NAME = 'uk_site_code'
      AND COLUMN_NAME = 'is_deleted') > 0,
  'SELECT ''uk_site_code 已包含 is_deleted，跳过'' AS skip_msg',
  'ALTER TABLE `crm_crawl_site` DROP INDEX `uk_site_code`, ADD UNIQUE KEY `uk_site_code` (`site_code`, `is_deleted`)'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------
-- 3) crm_crawl_region：加 is_deleted 列
-- ---------------------------------------------------------------------
SET @sql = IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'crm_crawl_region'
      AND COLUMN_NAME = 'is_deleted') = 0,
  'ALTER TABLE `crm_crawl_region` ADD COLUMN `is_deleted` bigint unsigned NOT NULL DEFAULT 0 AFTER `last_crawl_at`',
  'SELECT ''crm_crawl_region.is_deleted 已存在，跳过'' AS skip_msg'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------
-- 4) crm_crawl_region：唯一键 uk_site_province_city 改为含 is_deleted
-- ---------------------------------------------------------------------
SET @sql = IF(
  (SELECT COUNT(*) FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'crm_crawl_region'
      AND INDEX_NAME = 'uk_site_province_city'
      AND COLUMN_NAME = 'is_deleted') > 0,
  'SELECT ''uk_site_province_city 已包含 is_deleted，跳过'' AS skip_msg',
  'ALTER TABLE `crm_crawl_region` DROP INDEX `uk_site_province_city`, ADD UNIQUE KEY `uk_site_province_city` (`site_id`, `province`, `city`, `is_deleted`)'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------
-- 5) crm_crawl_site：加 entry_url（探测时的入口页，地区登记要复用它）
--    为什么需要：给已有站点「添加地区」时用户只填省市，入口地址必须由系统
--    自己知道。从翻页模板反推是错的——ccgp 第 1 页是 index.htm，模板拼出来
--    的 index_1.htm 并不存在；而探测时的入口页是真实打开过的那一页。
-- ---------------------------------------------------------------------
SET @sql = IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'crm_crawl_site'
      AND COLUMN_NAME = 'entry_url') = 0,
  'ALTER TABLE `crm_crawl_site` ADD COLUMN `entry_url` varchar(2048) NOT NULL DEFAULT '''' AFTER `site_name`',
  'SELECT ''crm_crawl_site.entry_url 已存在，跳过'' AS skip_msg'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------
-- 6) 回填存量站点的 entry_url：取该站点下最早的活跃地区的入口地址
--    （存量站点没有记录探测入口，就地复用已登记地区的 list_url，
--      它就是当年真实打开过的入口页；已有值的不覆盖）
-- ---------------------------------------------------------------------
UPDATE `crm_crawl_site` s
JOIN (
  SELECT site_id, MIN(id) AS rid
  FROM `crm_crawl_region`
  WHERE is_deleted = 0
  GROUP BY site_id
) pick ON pick.site_id = s.id
JOIN `crm_crawl_region` r ON r.id = pick.rid
SET s.entry_url = r.list_url
WHERE s.entry_url = '';

-- ---------------------------------------------------------------------
-- 7) 登记迁移（filename 唯一键保证重复执行不会插重）
-- ---------------------------------------------------------------------
INSERT IGNORE INTO schema_migrations (filename, note)
VALUES ('003_soft_delete.sql',
        '站点/地区加 is_deleted 软删列，唯一键并入 is_deleted（删过的编码/省市可重新接入）；站点加 entry_url 记住探测入口页');
