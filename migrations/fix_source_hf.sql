-- =====================================================================
-- fix_source_hf.sql — 恢复合肥采集源配置（数据修正，幂等）
-- 背景：2026-11-16 诊断发现 #1 号采集源标签是「安徽省/合肥市」，
--       但 list_url 已被覆盖成南京站（njggzy.nanjing.gov.cn），且该站
--       是 JS 渲染页，HTTP 抓取必然 0 条。本脚本把合肥的正确地址写回。
-- 执行方式：项目所有者手工执行
--   mysql -u<用户> -p aicrm < migrations/fix_source_hf.sql
-- =====================================================================
USE aicrm;

UPDATE crm_crawl_source
   SET list_url    = 'https://ggzyjy.hefei.gov.cn/jyxx/002002/002002001/2.html',
       base_domain = 'https://ggzyjy.hefei.gov.cn'
 WHERE id = 1;

-- 核对（期望：province=安徽省 city=合肥市，list_url 指向 ggzyjy.hefei.gov.cn）
SELECT id, province, city, list_url, base_domain
  FROM crm_crawl_source;
