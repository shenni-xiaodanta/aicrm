-- 概况聊天记录表
-- 执行：mysql -h 127.0.0.1 -P 3306 -u root -p < D:/workspace-pycharm/aicrm/com/crm/chat/chat.sql

SET NAMES utf8mb4;

USE `aicrm`;

CREATE TABLE IF NOT EXISTS `crm_chat_message` (
  `id`          bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `lead_id`     bigint unsigned NOT NULL COMMENT '商机ID',
  `user_id`     bigint unsigned NOT NULL COMMENT '用户ID',
  `role`        varchar(20)     NOT NULL COMMENT 'user/assistant',
  `content`     text            NOT NULL COMMENT '消息内容',
  `create_time` datetime        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_lead_user_time` (`lead_id`, `user_id`, `create_time`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_general_ci
  COMMENT = '概况聊天记录表';
