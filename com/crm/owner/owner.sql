-- 商机负责人与变更记录
-- 执行：mysql -h 127.0.0.1 -P 3306 -u root -p < D:/workspace-pycharm/aicrm/com/crm/owner/owner.sql
-- 注意：先执行 shangji_rename_table.sql，把 crm_xiansuo 改名为 crm_shangji。
--       如果 crm_shangji 已经有 owner_id 列，请跳过第一条 ALTER。

SET NAMES utf8mb4;

USE `aicrm`;

ALTER TABLE `crm_shangji`
  ADD COLUMN `owner_id` bigint unsigned NOT NULL DEFAULT 0 COMMENT '负责人ID' AFTER `city`;

CREATE TABLE IF NOT EXISTS `crm_owner_change` (
  `id`           bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `lead_id`      bigint unsigned NOT NULL COMMENT '商机ID',
  `old_owner_id` bigint unsigned NOT NULL DEFAULT 0 COMMENT '原负责人ID',
  `new_owner_id` bigint unsigned NOT NULL COMMENT '新负责人ID',
  `note`         varchar(500)    NOT NULL DEFAULT '' COMMENT '变更说明',
  `operator_id`  bigint unsigned NOT NULL DEFAULT 0 COMMENT '操作人ID',
  `create_time`  datetime        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '变更时间',
  PRIMARY KEY (`id`),
  KEY `idx_lead_time` (`lead_id`, `create_time`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_general_ci
  COMMENT = '商机负责人变更记录表';
