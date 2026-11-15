-- 线索采集源配置表
-- 执行：mysql -h 127.0.0.1 -P 3306 -u root -p < D:/workspace-pycharm/aicrm/com/crm/source/source.sql
-- 说明：按“省 + 市”唯一保存一套 base_domain / list_url，供地图页采集弹窗回填。

SET NAMES utf8mb4;

USE `aicrm`;

CREATE TABLE IF NOT EXISTS `crm_crawl_source` (
  `id`          bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `province`    varchar(50)   NOT NULL COMMENT '省/直辖市',
  `city`        varchar(50)   NOT NULL COMMENT '地级市',
  `base_domain` varchar(255)  NOT NULL DEFAULT '' COMMENT '站点根域名',
  `list_url`    varchar(2048) NOT NULL DEFAULT '' COMMENT '列表页 URL',
  `create_time` datetime      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime      NOT NULL DEFAULT CURRENT_TIMESTAMP
                             ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_province_city` (`province`, `city`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_general_ci
  COMMENT = '线索采集源配置表';
