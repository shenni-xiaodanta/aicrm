-- CRM 用户表
-- 执行：mysql -h 127.0.0.1 -P 3306 -u root -p < D:/workspace-pycharm/aicrm/com/crm/user/user.sql
-- 说明：密码由注册接口用 PBKDF2 哈希后写入，不能直接用 SQL 插入明文密码。
--       第一个注册的用户自动成为 admin，其余为 user。

SET NAMES utf8mb4;

USE `aicrm`;

CREATE TABLE IF NOT EXISTS `crm_user` (
  `id`            bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `username`      varchar(32)  NOT NULL COMMENT '用户名',
  `password_hash` varchar(200) NOT NULL COMMENT '密码哈希(PBKDF2)',
  `nickname`      varchar(50)  NOT NULL DEFAULT '' COMMENT '昵称',
  `role`          varchar(20)  NOT NULL DEFAULT 'user' COMMENT '角色:admin/user',
  `status`        tinyint      NOT NULL DEFAULT 1 COMMENT '状态:1启用 0禁用',
  `create_time`   datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time`   datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP
                            ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_general_ci
  COMMENT = 'CRM用户表';
