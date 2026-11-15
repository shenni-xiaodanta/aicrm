-- =====================================================================
-- 001_baseline.sql — B0 底座迁移（幂等，可重复执行）
-- 执行方式：由项目所有者手工执行（约定：AI 不直接操作数据库）
--   mysql -u<用户> -p aicrm < migrations/001_baseline.sql
-- 执行顺序：先跑本脚本，再部署本次新代码并重启服务
--   （旧代码不使用 created_by 列，先加列不会影响旧代码；反之会）
-- =====================================================================
USE aicrm;

-- ---------------------------------------------------------------------
-- 迁移记录表：后续所有脚本执行后在此登记，应用与人工都能核对版本
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schema_migrations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  filename VARCHAR(128) NOT NULL UNIQUE COMMENT '脚本文件名，如 001_baseline.sql',
  applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '执行时间',
  note VARCHAR(255) NULL COMMENT '本次迁移做了什么，方便回溯'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据库迁移执行记录';

-- ---------------------------------------------------------------------
-- B0-1 跟进主记录补 created_by（创建人），供附件下载鉴权用
-- 说明：用 INFORMATION_SCHEMA + 动态 SQL 保证幂等（MySQL 8 不支持
--       ADD COLUMN IF NOT EXISTS）；存量行 created_by 为 NULL，
--       应用层对 NULL 视为「历史数据，维持旧行为」，见 common/access.py
-- ---------------------------------------------------------------------
SET @ddl = (
  SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'crm_follow_up'
        AND COLUMN_NAME = 'created_by') = 0,
    'ALTER TABLE crm_follow_up ADD COLUMN created_by INT NULL COMMENT ''创建人 user_id（存量行为 NULL）'' AFTER content',
    'SELECT ''crm_follow_up.created_by 已存在，跳过'''
  )
);
PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------
-- B0-2 附件记录补 created_by，同上
-- ---------------------------------------------------------------------
SET @ddl = (
  SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'crm_attachment_record'
        AND COLUMN_NAME = 'created_by') = 0,
    'ALTER TABLE crm_attachment_record ADD COLUMN created_by INT NULL COMMENT ''创建人 user_id（存量行为 NULL）'' AFTER lead_id',
    'SELECT ''crm_attachment_record.created_by 已存在，跳过'''
  )
);
PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- ---------------------------------------------------------------------
-- 登记本脚本已执行（filename 唯一键保证重复执行不会插重）
-- ---------------------------------------------------------------------
INSERT IGNORE INTO schema_migrations (filename, note)
VALUES ('001_baseline.sql', 'B0：schema_migrations 建表；crm_follow_up / crm_attachment_record 补 created_by');
