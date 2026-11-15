-- CRM 商机表
-- 执行：mysql -h 127.0.0.1 -P 3306 -u root -p < D:/workspace-pycharm/aicrm/com/crm/shangji/shangji.sql
-- 注意：common/pool.py 在 import 时会预建连接，必须先执行本脚本再启动服务。

SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS `aicrm`
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

USE `aicrm`;

DROP TABLE IF EXISTS `crm_shangji`;
CREATE TABLE `crm_shangji`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `customer` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '客户/采购单位/招标人',
  `industry` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '行业',
  `needs` json NULL COMMENT '需求/采购内容',
  `budget` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '预算/最高限价',
  `objections` json NULL COMMENT '资格限制/风险',
  `intent_level` varchar(2) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '中' COMMENT '意向等级:高/中/低',
  `next_action` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '下一步动作',
  `project_address` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '项目地址',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '省/直辖市',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '地级市',
  `owner_id` bigint UNSIGNED NOT NULL DEFAULT 0 COMMENT '负责人ID',
  `contact` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '联系方式',
  `project_summary` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '项目概述',
  `longitude` double NULL DEFAULT NULL COMMENT '经度 GCJ-02',
  `latitude` double NULL DEFAULT NULL COMMENT '纬度 GCJ-02',
  `source_title` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '公告标题',
  `source_url` varchar(2048) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '详情页 URL',
  `source_url_md5` char(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'URL 的 MD5，去重键',
  `publish_date` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '公告日期',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_source_url_md5`(`source_url_md5` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 41 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'CRM商机线索表' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
