-- 商机跟进记录与附件表
-- 执行：mysql -h 127.0.0.1 -P 3306 -u root -p < D:/workspace-pycharm/aicrm/com/crm/followup/followup.sql

SET NAMES utf8mb4;

USE `aicrm`;

CREATE TABLE IF NOT EXISTS `crm_follow_up` (
  `id`          bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `lead_id`     bigint unsigned NOT NULL COMMENT '商机ID',
  `content`     text            NOT NULL COMMENT '跟进内容',
  `create_time` datetime        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_lead_time` (`lead_id`, `create_time`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_general_ci
  COMMENT = '商机跟进记录表';

CREATE TABLE IF NOT EXISTS `crm_follow_up_file` (
  `id`           bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `follow_up_id` bigint unsigned NOT NULL COMMENT '跟进记录ID',
  `lead_id`      bigint unsigned NOT NULL COMMENT '商机ID',
  `original_name` varchar(255)   NOT NULL COMMENT '原始文件名',
  `stored_name`  varchar(100)    NOT NULL COMMENT '存储文件名',
  `file_size`    int unsigned    NOT NULL DEFAULT 0 COMMENT '文件字节数',
  `content_type` varchar(120)    NOT NULL DEFAULT '' COMMENT 'MIME 类型',
  `create_time`  datetime        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_follow_up` (`follow_up_id`),
  KEY `idx_lead` (`lead_id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_general_ci
  COMMENT = '商机跟进附件表';
