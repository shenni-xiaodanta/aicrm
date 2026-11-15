-- =====================================================================
-- VERIFY_B0.sql — B0 迁移与代码上线后的验证（只读，随时可跑）
-- 期望输出见每段注释
-- =====================================================================
USE aicrm;

-- 1) schema_migrations 存在且已登记 001
--    期望：1 行，filename = 001_baseline.sql
SELECT * FROM schema_migrations ORDER BY id;

-- 2) created_by 列已在两张表上
--    期望：各返回 1 行，NULLABLE = YES
SELECT TABLE_NAME, COLUMN_NAME, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND ((TABLE_NAME = 'crm_follow_up' AND COLUMN_NAME = 'created_by')
    OR (TABLE_NAME = 'crm_attachment_record' AND COLUMN_NAME = 'created_by'));

-- 3) 新代码写入后的抽查（跑过一次「新增跟进/附件」之后再执行）
--    期望：recent 行的 created_by 不再是 NULL，等于当前登录用户的 id
--    注意：UNION 两侧各自带 ORDER BY/LIMIT 时必须加括号，
--    否则 MySQL 把 LIMIT 后的 UNION 当语法错误（错误 1064）
(SELECT 'follow_up' AS src, id, created_by, create_time
  FROM crm_follow_up ORDER BY id DESC LIMIT 3)
UNION ALL
(SELECT 'attachment' AS src, id, created_by, create_time
  FROM crm_attachment_record ORDER BY id DESC LIMIT 3);

-- 4) 越权修复的行为核对（代码层面，供人工回归）：
--    a. 用户 A 登录，下载用户 B 上传的附件 file_id → 应返回 code=1000「附件不存在」
--    b. 商机负责人下载自己商机下的附件 → 应正常返回文件流
--    c. admin 下载任意附件 → 应正常返回文件流
--    d. 响应头应出现 X-Request-ID，log/aicrm.log 的行中带 [12位id]
