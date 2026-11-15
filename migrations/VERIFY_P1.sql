-- =====================================================================
-- VERIFY_P1.sql — P1 迁移验证（只读，随时可跑）
-- 期望输出见每段注释
-- =====================================================================
USE aicrm;

-- 1) 三张表都已建立
--    期望：返回 3 行
SHOW TABLES LIKE 'crm_crawl_%';

-- 2) 迁移已登记
--    期望：能看到 002_crawl_tables.sql（以及之前的 001_baseline.sql）
SELECT * FROM schema_migrations ORDER BY id;

-- 3) ah_ggzy 站点模板
--    期望：1 行；selectors_valid=1；pagination 里 start_page=2；
--    url_template 末尾是 {page}.html；detail_content 含两个容器
SELECT id, site_code, site_name,
       JSON_VALID(selectors)  AS selectors_valid,
       JSON_VALID(pagination) AS pagination_valid,
       JSON_UNQUOTE(JSON_EXTRACT(pagination, '$.start_page'))   AS start_page,
       JSON_UNQUOTE(JSON_EXTRACT(pagination, '$.url_template')) AS url_template,
       JSON_EXTRACT(selectors, '$.detail_content')              AS detail_content,
       enabled
  FROM crm_crawl_site;

-- 4) 合肥地区行
--    期望：1 行，site_id 指向 ah_ggzy，list_url 指向 ggzyjy.hefei.gov.cn
SELECT r.id, r.site_id, s.site_code, r.province, r.city, r.list_url, r.enabled
  FROM crm_crawl_region r
  JOIN crm_crawl_site s ON s.id = r.site_id;

-- 5) 旧表未动（对照）
--    期望：合肥行还在，list_url 与第 4 段一致
SELECT id, province, city, list_url FROM crm_crawl_source;
