-- 项目总结表（每个商机保存一份最新总结）
-- 执行：mysql -h 127.0.0.1 -P 3306 -u root -p < D:/workspace-pycharm/aicrm/com/crm/summary/summary.sql

SET NAMES utf8mb4;

USE `aicrm`;

CREATE TABLE IF NOT EXISTS `crm_summary` (
  `id`          bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `lead_id`     bigint unsigned NOT NULL COMMENT '商机ID',
  `tags`        json            NULL COMMENT '标签列表',
  `summary`     text            NULL COMMENT '摘要',
  `analysis`    text            NULL COMMENT '项目分析',
  `lessons`     text            NULL COMMENT '经验总结',
  `update_time` datetime        NOT NULL DEFAULT CURRENT_TIMESTAMP
                             ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_lead` (`lead_id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_general_ci
  COMMENT = '项目总结表';
