-- =====================================================================
-- 002_crawl_tables.sql — P1 采集架构迁移（幂等，可重复执行）
-- 执行方式：由项目所有者手工执行（约定：AI 不直接操作数据库）
--   mysql -u<用户> -p aicrm < migrations/002_crawl_tables.sql
-- 执行顺序：先跑本脚本，再部署 P1 新代码
-- 内容：
--   1) 建 crm_crawl_site / crm_crawl_region / crm_crawl_task 三张表
--   2) 存量迁移：把 crm_crawl_source 里的合肥行升级成
--      ah_ggzy 站点模板 + 合肥地区采集点（旧表保留不删）
-- 设计依据：『aicrm P1采集架构·表结构设计.md』（已评审确认）
-- =====================================================================
USE aicrm;

-- ---------------------------------------------------------------------
-- 1) 站点模板表：一套解析配方（选择器/翻页/编码/限速/渲染模式）
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `crm_crawl_site` (
  `id`               bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `site_code`        varchar(50)   NOT NULL COMMENT '站点编码，如 ah_ggzy / js_njggzy',
  `site_name`        varchar(100)  NOT NULL COMMENT '站点名称，如 安徽公共资源交易（合肥模板）',
  `selectors`        json          NOT NULL COMMENT '解析选择器：list_item/list_link/title_attr/list_date/detail_content(数组，按序尝试)',
  `pagination`       json          NOT NULL COMMENT '翻页规则：mode=page_param + url_template({page}占位) + start_page + step',
  `charset`          varchar(30)   NOT NULL DEFAULT 'utf-8' COMMENT '站点编码；空串=用 apparent_encoding 自动猜',
  `render_mode`      varchar(20)   NOT NULL DEFAULT 'http' COMMENT '渲染模式：http=直接请求；browser=无头浏览器（本期未实现，选它直接报暂不支持）',
  `request_interval` decimal(4,1)  NOT NULL DEFAULT 3.0 COMMENT '同站两次请求基准间隔（秒），实际 ±1 秒随机',
  `max_retry`        tinyint unsigned NOT NULL DEFAULT 2 COMMENT '单页请求失败重试次数',
  `max_pages`        smallint unsigned NOT NULL DEFAULT 10 COMMENT '单次采集翻页上限',
  `enabled`          tinyint(1)    NOT NULL DEFAULT 1 COMMENT '是否启用；连续探测失败会自动置 0',
  `probed_at`        datetime      NULL COMMENT '最近一次 LLM 探测/回验成功时间',
  `create_time`      datetime      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time`      datetime      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_site_code` (`site_code`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci
  COMMENT = '采集站点模板表（一套解析配方服务 N 个地区）';

-- ---------------------------------------------------------------------
-- 2) 地区采集点表：一城一行，指向列表页入口
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `crm_crawl_region` (
  `id`            bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `site_id`       bigint unsigned NOT NULL COMMENT '所属站点模板 crm_crawl_site.id',
  `province`      varchar(50)   NOT NULL COMMENT '省/直辖市',
  `city`          varchar(50)   NOT NULL COMMENT '地级市',
  `list_url`      varchar(2048) NOT NULL COMMENT '该市的列表页入口 URL（不带页码，页码由站点配方 url_template 拼）',
  `enabled`       tinyint(1)    NOT NULL DEFAULT 1 COMMENT '是否参与采集',
  `last_task_id`  bigint unsigned NULL COMMENT '最近一次采集任务 id（冗余，列表页直显）',
  `last_crawl_at` datetime      NULL COMMENT '最近一次采集完成时间',
  `create_time`   datetime      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time`   datetime      NOT NULL DEFAULT CURRENT_TIMESTAMP
                              ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_site_province_city` (`site_id`, `province`, `city`),
  KEY `idx_site_enabled` (`site_id`, `enabled`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci
  COMMENT = '采集地区表（每城一行，指向入口 URL）';

-- ---------------------------------------------------------------------
-- 3) 采集任务表：一行 = 一次地区采集
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `crm_crawl_task` (
  `id`            bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `region_id`     bigint unsigned NOT NULL COMMENT '采集地区 crm_crawl_region.id',
  `site_id`       bigint unsigned NOT NULL COMMENT '冗余站点 id，供单站锁查询（同站同时只允许一个运行中任务）',
  `triggered_by`  bigint unsigned NULL COMMENT '发起人 crm_user.id；NULL=系统定时触发（下期）',
  `status`        varchar(20) NOT NULL DEFAULT 'running'
                  COMMENT 'running / success / partial / failed / canceled',
  `pages_crawled` smallint unsigned NOT NULL DEFAULT 0 COMMENT '已翻页数',
  `total_items`   smallint unsigned NOT NULL DEFAULT 0 COMMENT '本次扫到的公告总数',
  `new_count`     smallint unsigned NOT NULL DEFAULT 0 COMMENT '新增入库数',
  `dup_count`     smallint unsigned NOT NULL DEFAULT 0 COMMENT '重复跳过数',
  `fail_count`    smallint unsigned NOT NULL DEFAULT 0 COMMENT '失败数',
  `fail_detail`   json NULL COMMENT '失败明细 [{url, title, reason}]，成功为 NULL',
  `stop_reason`   varchar(30) NULL COMMENT '停止原因：no_new=连续5条重复 / max_pages=翻页上限 / error=异常 / manual=手动取消',
  `started_at`    datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  `finished_at`   datetime NULL COMMENT '结束时间',
  `create_time`   datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time`   datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
                  ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_region_status` (`region_id`, `status`),
  KEY `idx_site_status` (`site_id`, `status`),
  KEY `idx_started` (`started_at`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci
  COMMENT = '采集任务表（每次点采集一行，后台执行、前端轮询进度）';

-- ---------------------------------------------------------------------
-- 4) 存量迁移：合肥行 → ah_ggzy 站点 + 合肥地区
--    选择器/翻页用 2026-11 实测验证过的合肥配方；
--    翻页 url_template 由源行 list_url 把末尾页码换成 {page} 占位得出
--    （合肥怪癖：第 1 页 404，最新内容在第 2 页起 → start_page=2）
-- ---------------------------------------------------------------------
-- 4.1 站点模板（存在则跳过，幂等）
INSERT INTO `crm_crawl_site`
  (`site_code`, `site_name`, `selectors`, `pagination`,
   `charset`, `render_mode`, `request_interval`, `max_retry`, `max_pages`, `enabled`)
SELECT
  'ah_ggzy',
  '安徽公共资源交易（合肥模板）',
  JSON_OBJECT(
    'list_item',      'ul.ewb-right-item > li.ewb-right-list.clearfix',
    'list_link',      'a.l',
    'title_attr',     'title',
    'list_date',      'span.ewb-right-date.r',
    'detail_content', JSON_ARRAY('div.ewb-info-bd', 'div.ewb-article')
  ),
  JSON_OBJECT(
    'mode',         'page_param',
    'url_template', REPLACE(src.list_url, '2.html', '{page}.html'),
    'start_page',   2,
    'step',         1
  ),
  'utf-8', 'http', 3.0, 2, 10, 1
FROM `crm_crawl_source` src
WHERE src.city = '合肥市'
  AND NOT EXISTS (SELECT 1 FROM `crm_crawl_site` WHERE `site_code` = 'ah_ggzy');

-- 4.2 合肥地区行（存在则跳过，幂等）
INSERT INTO `crm_crawl_region` (`site_id`, `province`, `city`, `list_url`, `enabled`)
SELECT s.id, src.province, src.city, src.list_url, 1
FROM `crm_crawl_site` s
JOIN `crm_crawl_source` src ON src.city = '合肥市'
WHERE s.site_code = 'ah_ggzy'
  AND NOT EXISTS (
    SELECT 1 FROM `crm_crawl_region` r
     WHERE r.site_id = s.id AND r.province = src.province AND r.city = src.city
  );

-- ---------------------------------------------------------------------
-- 5) 登记迁移（filename 唯一键保证重复执行不会插重）
-- ---------------------------------------------------------------------
INSERT IGNORE INTO schema_migrations (filename, note)
VALUES ('002_crawl_tables.sql', 'P1：建 crm_crawl_site/region/task 三表；合肥源行迁移为 ah_ggzy 站点+合肥地区');
