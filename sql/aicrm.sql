/*
 Navicat Premium Dump SQL

 Source Server         : 127.0.0.1
 Source Server Type    : MySQL
 Source Server Version : 80046 (8.0.46)
 Source Host           : localhost:3306
 Source Schema         : aicrm

 Target Server Type    : MySQL
 Target Server Version : 80046 (8.0.46)
 File Encoding         : 65001

 Date: 13/11/2026 09:57:04
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for crm_attachment_file
-- ----------------------------
DROP TABLE IF EXISTS `crm_attachment_file`;
CREATE TABLE `crm_attachment_file`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `record_id` bigint UNSIGNED NOT NULL COMMENT '附件记录ID',
  `lead_id` bigint UNSIGNED NOT NULL COMMENT '线索ID',
  `original_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '原始文件名',
  `stored_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '存储文件名',
  `file_size` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '文件字节数',
  `content_type` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT 'MIME 类型',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_record`(`record_id` ASC) USING BTREE,
  INDEX `idx_lead`(`lead_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '线索附件文件表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of crm_attachment_file
-- ----------------------------
INSERT INTO `crm_attachment_file` VALUES (1, 1, 46, '聚类.pptx', '987779ccc3e0453992d1e37cc2bd08dd.pptx', 4744688, 'application/vnd.openxmlformats-officedocument.presentationml.presentation', '2026-11-12 22:49:43');
INSERT INTO `crm_attachment_file` VALUES (2, 2, 46, '报价单第一版.xlsx', 'a0e51114825c4bcd88021744a191aee7.xlsx', 6599, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '2026-11-12 22:50:38');
INSERT INTO `crm_attachment_file` VALUES (3, 3, 46, '报价单第二版.xlsx', 'bbe85a81149e431eab8d250a9cc3f3cf.xlsx', 6599, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '2026-11-12 22:50:57');
INSERT INTO `crm_attachment_file` VALUES (4, 5, 46, '1、安徽智飞龙科马除臭技术方案.pdf', '3bd69b8ee5ed4d04a12df7e3bfb4a2eb.pdf', 4913298, 'application/pdf', '2026-11-12 22:52:04');
INSERT INTO `crm_attachment_file` VALUES (5, 6, 46, '活性炭吸附VOC穿透曲线的研究.pdf', 'a5607ba73588449bba6dd364a2112823.pdf', 324542, 'application/pdf', '2026-11-13 09:32:36');
INSERT INTO `crm_attachment_file` VALUES (6, 7, 46, '工业废气处理工艺设计方案.pdf', '944cbbb8d5db4c18b583dbf859432385.pdf', 382822, 'application/pdf', '2026-11-13 09:33:07');

-- ----------------------------
-- Table structure for crm_attachment_record
-- ----------------------------
DROP TABLE IF EXISTS `crm_attachment_record`;
CREATE TABLE `crm_attachment_record`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `lead_id` bigint UNSIGNED NOT NULL COMMENT '线索ID',
  `category` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '招标文件/投标文件/投标结果/方案/报价/合同',
  `description` varchar(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '说明文字',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_lead_time`(`lead_id` ASC, `create_time` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '线索附件记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of crm_attachment_record
-- ----------------------------
INSERT INTO `crm_attachment_record` VALUES (1, 46, '投标文件', '已经审批过了的投标文件', '2026-11-12 22:49:43');
INSERT INTO `crm_attachment_record` VALUES (2, 46, '报价', '第一版报价', '2026-11-12 22:50:38');
INSERT INTO `crm_attachment_record` VALUES (3, 46, '报价', '第二版报价', '2026-11-12 22:50:57');
INSERT INTO `crm_attachment_record` VALUES (4, 46, '方案', '最终版方案', '2026-11-12 22:51:42');
INSERT INTO `crm_attachment_record` VALUES (5, 46, '方案', '最终版方案', '2026-11-12 22:52:04');
INSERT INTO `crm_attachment_record` VALUES (6, 46, '投标文件', '收集的客户原项目老需求，供写技术标部分参考', '2026-11-13 09:32:36');
INSERT INTO `crm_attachment_record` VALUES (7, 46, '方案', '初步修改为第二版', '2026-11-13 09:33:07');

-- ----------------------------
-- Table structure for crm_chat_message
-- ----------------------------
DROP TABLE IF EXISTS `crm_chat_message`;
CREATE TABLE `crm_chat_message`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `lead_id` bigint UNSIGNED NOT NULL COMMENT '线索ID',
  `user_id` bigint UNSIGNED NOT NULL COMMENT '用户ID',
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'user/assistant',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '消息内容',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_lead_user_time`(`lead_id` ASC, `user_id` ASC, `create_time` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 21 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '项目概况聊天记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of crm_chat_message
-- ----------------------------
INSERT INTO `crm_chat_message` VALUES (1, 46, 1, 'user', '这个项目余预算多少钱？', '2026-11-12 23:18:31');
INSERT INTO `crm_chat_message` VALUES (2, 46, 1, 'assistant', '项目预算及最高限价均为337.4716万元。资料中未提及“余预算”或已使用金额，无法计算剩余预算。', '2026-11-12 23:18:33');
INSERT INTO `crm_chat_message` VALUES (3, 46, 1, 'user', '这个项目报过价？', '2026-11-12 23:19:14');
INSERT INTO `crm_chat_message` VALUES (4, 46, 1, 'assistant', '报过价。跟进资料显示有两版报价：第一版报价（报价单第一版.xlsx）和第二版报价（报价单第二版.xlsx），时间均为2026-11-12。', '2026-11-12 23:19:16');
INSERT INTO `crm_chat_message` VALUES (5, 46, 1, 'user', '方案出来了？', '2026-11-12 23:19:39');
INSERT INTO `crm_chat_message` VALUES (6, 46, 1, 'assistant', '方案已出。资料显示有“最终版方案”（2026-11-12 22:51:42），另有一份“最终版方案”附件为《安徽智飞龙科马除臭技术方案.pdf》（2026-11-12 22:52:04）。', '2026-11-12 23:19:40');
INSERT INTO `crm_chat_message` VALUES (7, 46, 1, 'user', '帮我打开方案看看', '2026-11-12 23:19:59');
INSERT INTO `crm_chat_message` VALUES (8, 46, 1, 'assistant', '我无法打开或查看附件内容，只能依据项目资料中的文字信息回答。资料仅显示存在“最终版方案”及附件《安徽智飞龙科马除臭技术方案.pdf》，具体内容未提供。', '2026-11-12 23:20:00');
INSERT INTO `crm_chat_message` VALUES (9, 46, 1, 'user', '这个项目有谁负责跟进？', '2026-11-12 23:20:18');
INSERT INTO `crm_chat_message` VALUES (10, 46, 1, 'assistant', '资料中未明确记录该项目的内部跟进负责人。跟进记录仅提到客户方有“张总”分管该项目，并留有张总手机号（1234567890），第一次拨打无人接听。', '2026-11-12 23:20:20');
INSERT INTO `crm_chat_message` VALUES (11, 46, 1, 'user', '跟该项目的资料给我进行一次综合研判，下一步该怎么做？', '2026-11-13 09:34:00');
INSERT INTO `crm_chat_message` VALUES (12, 46, 1, 'assistant', '# 综合研判\n\n**项目基本面**\n- 业主：肥东县众兴乡人民政府；预算199.21万元，工期90日历天，属中小型环保工程。\n- 内容：新建200立方/日一体化污水处理站+配套土建、给排水、电气、工艺，污水管网改造（检查井、污水管），现状泵站改造（清淤、封堵、换泵、液位计、控制柜等）。\n- 硬性门槛：市政公用工程施工总承包三级及以上资质+有效安全生产许可证；面向中小微企业/监狱企业/残疾人福利性单位承建；不接受联合体。\n- 时间紧：11月23日前获取采购文件，11月24日09点前提交响应文件。\n\n**资料匹配度问题（重点风险）**\n- 现有方案、报价、投标文件多为**除臭/VOC废气、活性炭吸附**类内容（如《安徽智飞龙科马除臭技术方案》《活性炭吸附VOC穿透曲线研究》），与本项目**污水处理站+管网+泵站改造**的技术方向明显不符，直接套用风险大。\n- 两版报价是否按本项目199.21万预算口径编制，资料未体现，需核实。\n- 资质、安许证、中小企业身份等资格条件资料中未见确认。\n\n**客户关系**\n- 已获张总手机号，两次接触（保安拦门、电话未接），已电话预约下周登门，关系尚浅。\n\n# 下一步建议\n1. **先核资格**：确认公司市政三级资质、安全生产许可证、中小企业身份是否满足，不满足则及早放弃，避免无效投入。\n2. **重做技术方案**：围绕污水处理站（200m³/d一体化设备选型）、管网改造、泵站改造三块重新编制，废气类方案仅作参考，不可直接投标。\n3. **重核报价**：按本项目清单口径重算两版报价，控制在199.21万预算内并留合理利润。\n4. **抢时间**：11月23日前完成采购文件获取，倒排至11月24日09点提交，预留审批与盖章时间。\n5. **推进客户拜访**：按预约登门拜访张总，摸清评标关注点与竞争情况；同时通过交易系统确认公告与文件细节。\n6. **明确内部负责人**：资料未记录跟进人，建议尽快指定专人统筹，避免节点遗漏。\n\n注：资料中未见资质、报价口径、竞争格局等信息，以上判断基于现有记录，需以采购文件为准进一步核实。', '2026-11-13 09:34:05');
INSERT INTO `crm_chat_message` VALUES (13, 43, 1, 'user', '现在项目进度', '2026-11-13 09:51:43');
INSERT INTO `crm_chat_message` VALUES (14, 43, 1, 'assistant', '根据现有资料，项目当前处于**公开招标阶段**，投标截止时间为**2026年12月2日10:30**，需在此之前通过安徽公共资源交易集团电子交易系统递交投标文件。资料中未提供更具体的进度信息（如是否已开标、评标等）。', '2026-11-13 09:51:45');
INSERT INTO `crm_chat_message` VALUES (15, 42, 1, 'user', '需要多少资金', '2026-11-13 09:52:50');
INSERT INTO `crm_chat_message` VALUES (16, 42, 1, 'assistant', '项目预算为70万元。', '2026-11-13 09:52:51');
INSERT INTO `crm_chat_message` VALUES (17, 42, 1, 'user', '把需要的告诉我', '2026-11-13 09:53:07');
INSERT INTO `crm_chat_message` VALUES (18, 42, 1, 'assistant', '参与本项目需要满足/准备的主要事项：\n\n1. **资质**：具备有效的《危险化学品经营许可证》，且许可范围包含柴油。\n2. **投标方式**：不接受联合体投标；本项目为非专门面向中小企业采购项目。\n3. **投标文件递交**：2026年12月2日9:00前登录安徽合肥公共资源交易电子服务系统递交。\n4. **供货要求**：供应火化用燃油（柴油），合同签订后一年供货服务。\n5. **预算**：70万元。\n6. **咨询电话**：18256591250（林健）。\n\n如需更细的投标材料清单，现有资料未提供。', '2026-11-13 09:53:09');
INSERT INTO `crm_chat_message` VALUES (19, 41, 1, 'user', '该项目目前的跟进情况', '2026-11-13 09:56:50');
INSERT INTO `crm_chat_message` VALUES (20, 41, 1, 'assistant', '资料中没有该项目的跟进情况信息，仅提供了商机概况（意向等级为“高”）及下一步安排：2026年11月18日17:30前获取招标文件，12月2日10点前递交投标文件。', '2026-11-13 09:56:51');

-- ----------------------------
-- Table structure for crm_crawl_source
-- ----------------------------
DROP TABLE IF EXISTS `crm_crawl_source`;
CREATE TABLE `crm_crawl_source`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `province` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '省/直辖市',
  `city` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '地级市',
  `base_domain` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '站点根域名',
  `list_url` varchar(2048) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '列表页 URL',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_province_city`(`province` ASC, `city` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '线索采集源配置表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of crm_crawl_source
-- ----------------------------
INSERT INTO `crm_crawl_source` VALUES (1, '安徽省', '合肥市', 'https://njggzy.nanjing.gov.cn', 'https://njggzy.nanjing.gov.cn/njweb/fjsz/buildService1.html', '2026-11-12 21:30:21', '2026-11-13 09:54:13');

-- ----------------------------
-- Table structure for crm_follow_up
-- ----------------------------
DROP TABLE IF EXISTS `crm_follow_up`;
CREATE TABLE `crm_follow_up`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `lead_id` bigint UNSIGNED NOT NULL COMMENT '线索ID',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '跟进内容',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_lead_time`(`lead_id` ASC, `create_time` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '线索跟进记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of crm_follow_up
-- ----------------------------
INSERT INTO `crm_follow_up` VALUES (1, 46, '第一次去拜访客户，保安不让进门，但是到听到了项目有张总分管。', '2026-11-12 22:38:01');
INSERT INTO `crm_follow_up` VALUES (2, 46, '通过其他渠道，要到了张总的手机号码（1234567890），第一次打无人接听。', '2026-11-12 22:39:04');
INSERT INTO `crm_follow_up` VALUES (3, 46, '同朋友介绍已经和老板电话预约下周登门拜访', '2026-11-13 09:31:20');
INSERT INTO `crm_follow_up` VALUES (4, 43, '收集资料，收集负责人电话', '2026-11-13 09:51:29');

-- ----------------------------
-- Table structure for crm_follow_up_file
-- ----------------------------
DROP TABLE IF EXISTS `crm_follow_up_file`;
CREATE TABLE `crm_follow_up_file`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `follow_up_id` bigint UNSIGNED NOT NULL COMMENT '跟进记录ID',
  `lead_id` bigint UNSIGNED NOT NULL COMMENT '线索ID',
  `original_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '原始文件名',
  `stored_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '存储文件名',
  `file_size` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '文件字节数',
  `content_type` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT 'MIME 类型',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_follow_up`(`follow_up_id` ASC) USING BTREE,
  INDEX `idx_lead`(`lead_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '线索跟进附件表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of crm_follow_up_file
-- ----------------------------
INSERT INTO `crm_follow_up_file` VALUES (1, 1, 46, 'dog_and_girl.jpeg', '78419feb8d4b4b389807f80634aff7fc.jpeg', 496395, 'image/jpeg', '2026-11-12 22:38:01');
INSERT INTO `crm_follow_up_file` VALUES (2, 3, 46, '中药.jpg', '5d00bfa6f9974eb78fc41bcf53c6ee27.jpg', 3804946, 'image/jpeg', '2026-11-13 09:31:20');

-- ----------------------------
-- Table structure for crm_owner_change
-- ----------------------------
DROP TABLE IF EXISTS `crm_owner_change`;
CREATE TABLE `crm_owner_change`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `lead_id` bigint UNSIGNED NOT NULL COMMENT '商机ID',
  `old_owner_id` bigint UNSIGNED NOT NULL DEFAULT 0 COMMENT '原负责人ID',
  `new_owner_id` bigint UNSIGNED NOT NULL COMMENT '新负责人ID',
  `note` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '变更说明',
  `operator_id` bigint UNSIGNED NOT NULL DEFAULT 0 COMMENT '操作人ID',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '变更时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_lead_time`(`lead_id` ASC, `create_time` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 6 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '商机负责人变更记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of crm_owner_change
-- ----------------------------
INSERT INTO `crm_owner_change` VALUES (1, 46, 0, 3, '', 1, '2026-11-12 23:45:07');
INSERT INTO `crm_owner_change` VALUES (2, 46, 3, 4, '用户01离职了', 1, '2026-11-12 23:45:24');
INSERT INTO `crm_owner_change` VALUES (3, 46, 4, 5, '用户02离职了', 1, '2026-11-13 09:30:24');
INSERT INTO `crm_owner_change` VALUES (4, 43, 0, 3, '开始跟进', 1, '2026-11-13 09:51:11');
INSERT INTO `crm_owner_change` VALUES (5, 68, 0, 7, '', 1, '2026-11-13 09:53:38');

-- ----------------------------
-- Table structure for crm_shangji
-- ----------------------------
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
) ENGINE = InnoDB AUTO_INCREMENT = 121 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'CRM商机线索表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of crm_shangji
-- ----------------------------
INSERT INTO `crm_shangji` VALUES (41, '安徽医科大学第一附属医院', '信息化', '[\"国家重大传染病防治基地信息化终端商用电脑采购\", \"商用电脑配送\", \"分批供货，每批接采购人通知后15个日历日内完成供货\"]', '258万元', '[\"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '高', '2026年11月18日17:30前登录安徽公共资源交易集团电子交易系统获取招标文件，12月2日10点前递交投标文件。', '合肥市蜀山区绩溪路218号', '安徽省', '合肥市', 0, '项目联系人：李工；电话：0551-66223646；采购人联系方式：0551-62922911；代理机构联系方式：0551-66223645', '安徽医科大学第一附属医院采购国家重大传染病防治基地信息化终端商用电脑及配送服务，预算258万元，合同签订后按1年供货周期分批供货，每批接通知后15个日历日内完成。', 117.267845, 31.847508, '安徽医科大学第一附属医院（北区）国家重大传染病防治基地信息化终端商用电脑采购及配送项目（二次）公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261111/4ae4ac04-6293-4dee-a432-56e2b539673a.html?ztbtab=002002001&biaoduanguid=9d235a09-d06f-4c8e-8588-2214c0577b5a', 'becbdcf26110a2ff1db2001e7a7dea8a', '2026-11-11', '2026-11-12 23:41:58');
INSERT INTO `crm_shangji` VALUES (42, '庐江县殡葬管理所', '能源', '[\"2026年火化燃油采购\", \"供应火化用燃油（柴油）\", \"合同签订后一年供货服务\"]', '70.000000万元', '[\"具备有效的《危险化学品经营许可证》（许可范围包含柴油）\", \"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '高', '2026年12月2日9:00前登录安徽合肥公共资源交易电子服务系统递交投标文件，项目咨询电话18256591250。', '安徽省合肥市庐江县庐城镇庐白路123号', '安徽省', '合肥市', 0, '林健 18256591250；采购人 15956500555', '庐江县殡葬管理所采购2026年火化燃油，预算70万元，合同期一年，要求具备含柴油范围的《危险化学品经营许可证》，投标截止2026年12月2日9:00。', 117.298527, 31.259663, '2026年火化燃油采购', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261111/0bb4d65d-4402-4913-adf6-667a19b1b2f2.html', 'dab746e7a527da8e4622c12f641ee3b6', '2026-11-11', '2026-11-12 23:41:58');
INSERT INTO `crm_shangji` VALUES (43, '合肥职业技术学院', '教育', '[\"分子生物学实验室升级改造\", \"相关设备及配套采购\", \"供货及安装调试\"]', '68万元', '[\"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '高', '2026年12月2日10:30前在安徽公共资源交易集团电子交易系统递交投标文件，项目咨询0551-66223922、66223923。', '合肥市瑶海区岱河路2号', '安徽省', '合肥市', 3, '项目联系人：李工，0551-66223646；项目咨询：0551-66223922、66223923', '合肥职业技术学院对2026年分子生物学实验室进行升级改造（二次）公开招标，预算及最高限价均为68万元，合同签订后45个日历日内完成供货及安装调试，投标截止时间为2026年12月2日10:30。', 117.359622, 31.915041, '合肥职业技术学院2026年分子生物学实验室升级改造（二次）公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261111/261de390-7f32-4c6f-8233-776de12f4513.html?ztbtab=002002001&biaoduanguid=57ffcfdf-d49e-4d41-9055-f768cbd74ad2', '4cb26e784d6a96dd644eecea0ef8e7c5', '2026-11-11', '2026-11-12 23:41:59');
INSERT INTO `crm_shangji` VALUES (44, '安徽省人民检察院', '信息化', '[\"第1包：项目详细设计服务\", \"第2包：项目主体建设（软件开发）\", \"第3包：项目监理服务\", \"第4包：项目测评服务\", \"数字检察法律监督线索一键推系统二期建设\"]', '第1包35.84万元；第2包552.72万元；第3包6.43万元；第4包19.76万元', '[\"本项目不接受联合体投标\", \"第3、4包专门面向中小企业采购，投标人所提供的服务须为中小微企业、监狱企业或残疾人福利性单位承接\", \"第4包投标人须具有商用密码检测机构(商用密码应用安全性评估业务)资质\", \"第1、2包不专门面向中小企业预留采购份额\"]', '中', '2026年11月18日17:30前登录安徽公共资源交易集团电子交易系统获取招标文件，12月2日10点前递交投标文件', '合肥市蜀山区祁门路298号', '安徽省', '合肥市', 0, '0551-63696559；0551-66223645；李工 0551-66223646', '安徽省人民检察院采购皖检数智数字检察法律监督线索一键推（二期）项目，分详细设计、主体建设、监理、测评4包，总预算614.75万元，主体建设包6个月内完成软件开发。', 117.235435, 31.810274, '安徽省检察机关皖检数智数字检察法律监督线索一键推（二期）项目公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261111/a3e7e2d3-eb7f-458d-96a3-90147508a1e2.html?ztbtab=002002001&biaoduanguid=bc514375-f4a4-47ba-af32-401184cfd76c', 'fca45c7fa4719941d2366250d5f07dfc', '2026-11-11', '2026-11-12 23:41:59');
INSERT INTO `crm_shangji` VALUES (45, '合肥市口腔医院', '医疗', '[\"采购消毒供应设备\", \"供货\", \"安装\", \"调试\", \"培训\"]', '116.500000万元', '[\"投标人具有医疗器械生产或医疗器械经营资格\", \"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '中', '2026年12月1日前登录安徽合肥公共资源交易电子服务系统获取招标文件，12月2日10:00前递交投标文件', '安徽省合肥市包河区烟墩街道滨湖科学城云谷路与江城路交口', '安徽省', '合肥市', 0, '郭雷0551-63736292/63732512；采购人0551-62993757', '合肥市口腔医院采购2026年消毒供应设备，预算116.5万元，合同生效接通知后30个日历日内完成供货、安装、调试、培训，投标截止2026年12月2日10:00。', 117.268275, 31.714497, '合肥市口腔医院2026年消毒供应设备采购', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261111/cf6f03cc-bf40-45f2-adc2-4706d0f84dab.html', '646372673d59300add17edcd3de3d674', '2026-11-11', '2026-11-12 23:42:00');
INSERT INTO `crm_shangji` VALUES (46, '肥东县众兴乡人民政府', '环保', '[\"新建一座日处理量200立方的成品一体化污水处理站\", \"污水处理站配套的土建、给排水、电气、水处理工艺等\", \"新建一体化污水处理站周边污水管网改造，包括新建检查井、污水管等\", \"现状一座污水泵站改造，包括泵站清淤、气囊封堵、更换潜水泵、出水管、液位计、控制柜等\"]', '199.210000万元', '[\"供应商所提供的工程由中小微企业、监狱企业或残疾人福利性单位承建\", \"供应商具备市政公用工程施工总承包三级及以上资质且具备有效的安全生产许可证\", \"本项目不接受联合体\"]', '中', '2026年11月23日前登录安徽合肥公共资源交易电子服务系统获取采购文件，11月24日09点前提交响应文件', '安徽省合肥市肥东县众兴乡', '安徽省', '合肥市', 5, '李博凌 0551-62520516；采购人 0551-67625215', '肥东县众兴乡人民政府采购农村污水处理升级改造工程，含新建200立方一体化污水处理站、污水管网改造及泵站改造，预算199.21万元，工期90日历天。', 117.408933, 31.984711, '肥东县众兴乡农村污水处理升级改造工程', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261111/50a95aa6-9df5-41eb-9ac7-07219fef842f.html', 'cc5de596ad14a6abadfd2544e5fcab05', '2026-11-11', '2026-11-12 23:42:00');
INSERT INTO `crm_shangji` VALUES (47, '合肥市庐阳区大杨镇社区卫生服务中心', '医疗', '[\"慢病一体化门诊设备采购\", \"第1包设备采购\", \"第2包设备采购\", \"第3包设备采购\", \"合同签订之日起10日内完成供货及安装\"]', '第1包260.000000万元,第2包52.160000万元,第3包26.000000万元；最高限价3381600.00元', '[\"本项目不接受联合体投标\", \"第1包预留部分采购项目预算专门面向中小企业采购，分包意向协议中中小微企业合同金额达到40%及以上（其中预留给小微企业的比例不低于70%），或所提供货物为中小微企业、监狱企业或残疾人福利性单位制造\", \"第2、3包专门面向中小企业采购（即投标人所提供的货物由中小微企业、监狱企业或残疾人福利性单位制造）\", \"具有医疗器械生产或医疗器械经营资格\", \"投标人应合理安排招标文件获取时间，因计算机及网络故障造成无法完成招标文件获取，责任自负\"]', '中', '2026年12月2日9:00前登录安徽合肥公共资源交易电子服务系统获取招标文件并递交投标文件，项目咨询0551-65633205。', '安徽省合肥市庐阳区四里河路与防汛路交口中铁品园28号楼；开标地点：合肥市庐阳区濉溪路335号（蓝钻尚界）B座4楼1号开标室', '安徽省', '合肥市', 0, '0551-65715136；0551-65633205；王工 0551-65633205', '合肥市庐阳区大杨镇社区卫生服务中心采购慢病一体化门诊设备一批，分3包，预算合计338.16万元，最高限价3381600.00元，合同签订之日起10日内完成供货及安装，2026年12月2日9:00开标。', 117.259791, 31.878365, '庐阳区卫健委委属机构慢病一体化门诊设备追加预算采购', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261111/31701939-faf0-4a63-8902-77661f999c2a.html', 'f36814fd1756e6b77367e14891b5a9b6', '2026-11-11', '2026-11-12 23:42:00');
INSERT INTO `crm_shangji` VALUES (48, '肥西县上派镇人民政府', '测绘服务', '[\"对上派镇辖区内土地处置等工作提供测绘技术服务\", \"承担镇自规分局负责实施项目涉及的规划土地相关测绘工作\", \"承担镇直二级机构、村、社区交办的其他测绘相关服务\", \"拟招1家成交供应商\"]', '70万元', '[\"供应商所提供的服务为中小微企业、监狱企业或残疾人福利性单位承接\", \"供应商须具有有效的乙级及以上测绘资质证书（专业类别包含：工程测量、界线与不动产测绘、地理信息系统工程、摄影测量与遥感）\", \"本项目不接受联合体投标\"]', '中', '2026年11月24日10时00分前登录安徽合肥公共资源交易中心电子交易系统提交响应文件，项目咨询0551-68825072。', '安徽省合肥市肥西县上派镇', '安徽省', '合肥市', 0, '符媛媛；0551-68825072；0551-68850035', '肥西县上派镇人民政府采购2026年上派镇测绘服务单位，拟招1家供应商提供土地处置等测绘技术服务，预算70万元，服务期12个月，响应截止2026年11月24日10时。', 117.15731, 31.714387, '2026年上派镇测绘服务单位项目竞争性磋商公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261111/7c625de9-a934-5408-e8eb-e77970c2192f.html?ztbtab=002002001&biaoduanguid=50c5feb2-5c6c-c234-1cf5-21439259c826', '2d6479832898adced6c0498d6c8642ee', '2026-11-11', '2026-11-12 23:42:01');
INSERT INTO `crm_shangji` VALUES (49, '合肥市第一人民医院', '医疗', '[\"各院区神经介入类耗材配送服务\", \"合同生效后1年内按采购人要求分批供货\", \"每批货物接采购人通知后3个日历日内完成供货\", \"1年期满经考核合格可续签后1年合同，最多续签一次\"]', '337.4716万元', '[\"本项目专门面向中小企业采购（即投标人所提供的服务为中小微企业、监狱企业或残疾人福利性单位承接）\", \"具有医疗器械生产或经营资格\", \"本项目不接受联合体投标\"]', '中', '2026年12月2日10点前登录电子服务系统递交投标文件，项目咨询0551-66223922', '合肥市庐阳区淮河路390号', '安徽省', '合肥市', 0, '0551-62183803；0551-66223922；李工 0551-66223923', '合肥市第一人民医院采购各院区神经介入类耗材配送服务，预算及最高限价均为337.4716万元，合同期1年、考核合格可续签一次，投标截止2026年12月2日10时。', 117.280304, 31.867426, '合肥市第一人民医院各院区神经介入类耗材配送服务（三次）公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261111/8c41d579-97eb-4066-8432-8d4f4aae6239.html?ztbtab=002002001&biaoduanguid=377252b5-ae25-4982-88e1-39afd8f85a10', '90069b7d08404f932d56cca134445ac2', '2026-11-11', '2026-11-12 23:42:01');
INSERT INTO `crm_shangji` VALUES (50, '长丰县下塘镇人民政府', '环保', '[\"长丰县下塘镇内指定小区5处智能垃圾分类投放站的建设\", \"智能垃圾分类投放站的安装采购\", \"智能垃圾分类投放站运维服务\"]', '117.460000万元', '[\"投标人所提供的货物为中小微企业、监狱企业或残疾人福利性单位制造\", \"本项目不接受联合体投标\", \"本项目为专门面向中小企业采购项目\"]', '高', '2026年12月2日10:00前登录安徽合肥公共资源交易电子服务系统递交投标文件', '长丰县下塘镇内指定小区', '安徽省', '合肥市', 0, '张乐；0551-62721981、62723379；0551-66465696', '长丰县下塘镇人民政府采购下塘镇2026年度生活垃圾分类设施建设，含5处智能垃圾分类投放站建设、安装及两年运维服务，预算117.46万元，合同签订后一个月内完成供货安装。', 117.215903, 32.237318, '下塘镇2026年度生活垃圾分类设施建设采购项目', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261111/9b10d014-35cf-4fff-a4f6-b4f490b8ed70.html', '86c60f54214adf3c73329140f18307c1', '2026-11-11', '2026-11-12 23:42:02');
INSERT INTO `crm_shangji` VALUES (51, '长丰县下塘镇人民政府', '建筑工程', '[\"下钱路总长685米，现状7.5米宽沥青路面，三级公路\", \"对老路路面龟裂、坑槽等病害实施病害处理\", \"路面修复养护\", \"具体详见磋商文件、工程量清单、图纸及补充答疑文件\"]', '253.780700万元', '[\"供应商须同时具有路基路面养护乙级及以上资质和交通安全设施养护资质\", \"具备有效的安全生产许可证\", \"本项目不接受联合体\", \"供应商所提供的工程为中小微企业、监狱企业或残疾人福利性单位承建\"]', '高', '2026年11月23日前登录安徽合肥公共资源交易电子服务系统获取采购文件，11月24日10点前提交响应文件', '下钱路（长丰县下塘镇）', '安徽省', '合肥市', 0, '黄殷武；0551-62723325；0551-62721978；0551-66465696', '长丰县下塘镇人民政府采购长丰县2026年农村公路修复养护项目—下钱路，对685米长三级公路沥青路面病害处理及修复养护，预算253.7807万元，最高限价1832759.46元，工期60日历天。', 117.215903, 32.237318, '长丰县2026年农村公路修复养护项目—下钱路', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261111/fabe7c9c-a1b6-4d7e-9c92-e0998e6e2d4e.html', '926d28c4af07f923f3ed5735259380c5', '2026-11-11', '2026-11-12 23:42:02');
INSERT INTO `crm_shangji` VALUES (52, '安徽省庐江县中医院', '医疗', '[\"胃肠镜采购\", \"供货、安装、调试\"]', '100.000000万元', '[\"具有医疗器械生产或医疗器械经营资格\", \"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '高', '2026年12月2日9:00前登录安徽合肥公共资源交易电子服务系统递交投标文件，项目咨询0551-87011301。', '安徽省合肥市庐江县庐城镇周瑜大道350号', '安徽省', '合肥市', 0, '缪梨华；0551-87011301；0551-87335182', '安徽省庐江县中医院采购金牛分院2026年胃肠镜，预算100万元，合同签订后10个日历日内完成供货、安装、调试，投标截止2026年12月2日9:00。', 117.280858, 31.253195, '庐江县中医院金牛分院2026年胃肠镜采购', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261111/df3d7d1c-7262-4adf-b25b-f8e0215a015e.html', '19a48dfc0e395231e783044803e97fe6', '2026-11-11', '2026-11-12 23:42:02');
INSERT INTO `crm_shangji` VALUES (53, '合肥市数据资源管理局', '信息化', '[\"第1包：项目监理服务等一批\", \"第2包：政务运营服务等一批\", \"合同签订后7个工作日内完成人员进场、前期筹备工作并正式启动项目服务\", \"合同履行期限为合同签订之日起12个月，考核合格可续签，续签年限最长不超过两年\"]', '第1包2.48万元；第2包397万元', '[\"本项目不接受联合体\", \"本项目为非专门面向中小企业采购项目\", \"供应商应合理安排采购文件获取时间，因计算机及网络故障造成无法完成采购文件获取的，责任自负\"]', '高', '2026年11月23日10点前在安徽公共资源交易集团电子交易系统提交响应文件，项目咨询电话0551-66223645。', '合肥市蜀山区月山西路和前河路交口', '安徽省', '合肥市', 0, '0551-63538856；0551-66223645；李工 0551-66223923', '合肥市数据资源管理局采购合肥市政务服务运营购买服务项目，分两包：第1包项目监理服务预算2.48万元，第2包政务运营服务预算397万元，合同期12个月，可续签最长两年。', 117.226117, 31.824367, '合肥市政务服务运营购买服务项目竞争性磋商公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261110/6b957f2a-06a2-4d3f-80fa-efedeb04a696.html?ztbtab=002002001&biaoduanguid=bfeb1fda-f5c1-4d7e-98d3-fc391e312a87', '3b370982bd04b27daaf7256ae1b424fe', '2026-11-10', '2026-11-12 23:42:03');
INSERT INTO `crm_shangji` VALUES (54, '安徽省应急管理厅', '制造', '[\"帽类（大檐帽、大檐凉帽、布面栽绒防寒帽）\", \"服装类（防寒服短款、春秋执勤服、常服、常服配套衬衣、夏装制式衬衣、裙子、冬执勤服、单裤）\", \"标志类（含腰带）\", \"鞋类\"]', '412万元', '[\"本项目专门面向监狱企业采购（投标人所提供的货物为监狱企业制造）\", \"本项目不接受联合体投标\"]', '高', '2026年11月17日17:30前登录安徽公共资源交易集团电子交易系统获取招标文件并准备投标', '合肥市包河区马鞍山路509号', '安徽省', '合肥市', 0, '0551-62999523；0551-66223645；李工 0551-66223646', '安徽省应急管理厅采购制式服装和标志一批，含帽类、服装类、标志类及鞋类，预算412万元，合同履行期限一年，专门面向监狱企业采购。', 117.300529, 31.83319, '安徽省应急管理系统制式服装和标志采购项目公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261110/326a1c5c-4683-4416-9db3-9ccb48ea12ba.html?ztbtab=002002001&biaoduanguid=5c017c30-4519-4a18-8aa3-c88f2e6c186c', '505457aa72a13ca9743904a27f8f1818', '2026-11-10', '2026-11-12 23:42:03');
INSERT INTO `crm_shangji` VALUES (55, '合肥市第二人民医院', '医疗', '[\"老年护理院医养结合设施设备一批\", \"第1包：医养结合设施设备\", \"第2包：医养结合设施设备\", \"第3包：医养结合设施设备\", \"合同生效后10个日历天内完成供货及安装\"]', '200万元（第1包50.504万元；第2包58.9万元；第3包90.596万元）', '[\"具有医疗器械生产或医疗器械经营资格\", \"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '高', '2026年12月1日10点前在安徽公共资源交易集团电子交易系统递交投标文件，项目咨询0551-66223922。', '合肥市瑶海区和平路246号', '安徽省', '合肥市', 0, '0551-62965091；0551-66223922；李工 0551-66223923', '合肥市第二人民医院采购老年护理院医养结合设施设备一批，分3包，预算及最高限价共200万元，合同生效后10个日历天内完成供货及安装，投标截止2026年12月1日10点。', 117.318423, 31.856642, '合肥市第二人民医院老年护理院医养结合设施设备第1-3包公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261110/1ef85f16-6158-4e5f-bf61-09505df5c458.html?ztbtab=002002001&biaoduanguid=9230fe56-fd9e-44a0-a670-4af44af331bb', '4b9bf4aeca68d5efb7dbe8296350e97b', '2026-11-10', '2026-11-12 23:42:04');
INSERT INTO `crm_shangji` VALUES (56, '安徽国际商务职业学院', '建筑工程', '[\"1号、5号楼阶梯教室改造\", \"第1包：1号楼阶梯教室改造\", \"第2包：5号楼阶梯教室改造\"]', '189万元（第1包78万元，第2包111万元）', '[\"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '低', '2026年11月17日17:30前登录电子服务系统获取招标文件，12月1日9:30前递交投标文件', '合肥市长丰县魏武路1号', '安徽省', '合肥市', 0, '0551-66319873；0551-66223645；李工 0551-66223646', '安徽国际商务职业学院对1号、5号楼阶梯教室进行改造，分2个包，预算及最高限价均为189万元，合同签订后40个日历日内完成。', 117.256002, 31.984747, '安徽国际商务职业学院1号、5号楼阶梯教室改造公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261110/2dcc8226-9e88-47d4-8da2-28d4bd0c7511.html?ztbtab=002002001&biaoduanguid=53f6d14b-f755-4b44-818b-3418c8791a3f', 'ba1060189b34bd22bb94e333e9bdef46', '2026-11-10', '2026-11-12 23:42:04');
INSERT INTO `crm_shangji` VALUES (57, '安徽合肥新站高新技术产业开发区社会发展局', '农业', '[\"承接新站高新区补充耕地质量检测鉴定服务\", \"拟采购1家服务单位\", \"服务期限采用1+X(X≤2)模式，合同期1年\"]', '60万元；最高限价300元/亩', '[\"本项目专门面向中小企业采购（即供应商所提供的服务为中小微企业、监狱企业或残疾人福利性单位承接）\", \"本项目不接受联合体投标\"]', '低', '2026年11月25日09时00分前在安徽合肥公共资源交易中心电子交易系统提交响应文件，项目咨询0551-65777681', '合肥市新站高新区', '安徽省', '合肥市', 0, '孙瑜 0551-65777681；采购人 0551-65777367', '安徽合肥新站高新技术产业开发区社会发展局采购新站高新区补充耕地质量检测鉴定服务，拟采购1家服务单位，预算60万元，最高限价300元/亩，服务期1年，专门面向中小企业采购。', 117.222942, 31.796672, '新站高新区补充耕地质量检测鉴定服务竞争性磋商公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261110/0dbc05ab-0e7b-f899-a1b9-6c1cd641d3ac.html?ztbtab=002002001&biaoduanguid=7c6a2c4b-bb8e-000c-e6cb-5ad1fe01a5a2', '17b856cb3648925db9671feff2640bfd', '2026-11-10', '2026-11-12 23:42:05');
INSERT INTO `crm_shangji` VALUES (58, '安徽省环境保护宣传教育中心', '信息化', '[\"2026年网络信息监测与宣传服务等一批\", \"媒体专项宣传服务\"]', '100万元', '[\"本项目不接受联合体\", \"本项目为非专门面向中小企业采购项目\"]', '低', '2026年11月17日17:30前登录安徽公共资源交易集团电子交易系统获取采购文件并准备响应文件', '合肥市蜀山区长江西路8号', '安徽省', '合肥市', 0, '项目联系人：李工，0551-66223646；采购人：0551-62811724；代理机构：0551-66223922、66223923', '安徽省环境保护宣传教育中心采购2026年媒体专项宣传项目（二次），内容为2026年网络信息监测与宣传服务等一批，预算及最高限价均为100万元，合同履行期限为合同签订后一年。', 117.266413, 31.858773, '2026年媒体专项宣传项目（二次）竞争性磋商公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261110/40b23736-1f82-4830-b803-e363439584e2.html?ztbtab=002002001&biaoduanguid=76025f8d-953c-4f55-b591-c0edbc8aff33', '21b9fd6270102850598b934db50d83b4', '2026-11-10', '2026-11-12 23:42:05');
INSERT INTO `crm_shangji` VALUES (59, '安徽合肥新站高新技术产业开发区应急和城市管理局', '建筑工程', '[\"新蚌埠路跨铁路桥增设行车道外侧防撞护栏、更换盖板\", \"文忠路桥行车道外侧防撞护栏加宽加高改造\", \"九顶山路铁路桥更换防抛网、修复桥梁混凝土裂缝及露筋病害\"]', '155万元（最高限价1461203.07元）', '[\"具备桥梁工程专业承包二级及以上资质\", \"具有有效的安全生产许可证\", \"本项目不接受联合体投标\"]', '低', '2026年11月24日09时00分前在安徽合肥公共资源交易中心电子交易系统提交响应文件，项目咨询0551-65777681。', '新站高新区新蚌埠路跨铁路桥、文忠路桥、九顶山路铁路桥', '安徽省', '合肥市', 0, '孙瑜；0551-65777681；0551-62777816', '安徽合肥新站高新技术产业开发区应急和城市管理局采购新站高新区三座跨铁路桥隐患整治工程，含防撞护栏增设改造、盖板更换、防抛网更换及裂缝露筋修复，预算155万元，工期90日历天。', 117.364713, 31.903176, '新站高新区三座跨铁路桥隐患整治项目竞争性磋商公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261110/a4ec3ecf-7cd9-4acd-c1dc-31806d34d3e6.html?ztbtab=002002001&biaoduanguid=def009a0-871a-27d5-3b13-f0de0aebeb2a', 'b9e2bb29b222e3e2cb34a5a45fa06cc2', '2026-11-10', '2026-11-12 23:42:05');
INSERT INTO `crm_shangji` VALUES (60, '安徽省高级人民法院', '信息化', '[\"安徽法院“一张网”安全运维服务（2026）\", \"详见采购文件\"]', '250万元', '[\"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '低', '2026年11月17日17:30前登录电子服务系统获取招标文件，12月1日10点前递交投标文件', '合肥市蜀山区长江西路472号', '安徽省', '合肥市', 0, '项目联系人：李工；电话：0551-66223646；采购人联系方式：0551-65599813；代理机构联系方式：0551-66223645', '安徽省高级人民法院采购安徽法院“一张网”安全运维服务（2026），预算及最高限价均为250万元，合同履行期限为合同生效起12个月，不接受联合体投标。', 117.239758, 31.851493, '安徽法院“一张网”安全运维服务（2026）公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261110/dfeb1190-f6aa-4924-819e-7d75fe4598a6.html?ztbtab=002002001&biaoduanguid=dc4deb93-b54b-47a9-9fbf-a6f3582cdc60', '2250f0474549f3b30d89fe5dce43f787', '2026-11-10', '2026-11-12 23:42:06');
INSERT INTO `crm_shangji` VALUES (61, '长丰县融媒体中心', '信息化', '[\"数字电视发射机采购\", \"配套设备采购\", \"设备安装\", \"设备调试\"]', '62.300000万元', '[\"投标人所提供的货物为中小微企业、监狱企业或残疾人福利性单位制造\", \"本项目为专门面向中小企业采购项目\", \"本项目不接受联合体投标\"]', '高', '2026年12月1日10:00前登录安徽合肥公共资源交易电子服务系统递交投标文件', '安徽省合肥市长丰县水湖镇杨公路体育公园内', '安徽省', '合肥市', 0, '0551-66681105；0551-62723373；0551-62723374；陈杰 0551-62723373、0551-62723374', '长丰县融媒体中心采购数字电视发射机及配套设备并安装调试，预算62.3万元，最高限价623000元，合同履行期限40日历天，专门面向中小企业采购。', 117.160391, 32.467952, '长丰县融媒体中心2026年数字电视发射机及配套设备采购项目', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261110/0c7a98e4-5e66-4d1f-9b0c-423886436d4f.html', '327897d6e0a1b6f26e5c5f40b4f11b54', '2026-11-10', '2026-11-13 09:28:45');
INSERT INTO `crm_shangji` VALUES (62, '合肥职业技术学院', '教育', '[\"数字媒体艺术设计专业实训室改造\", \"供货及安装调试\"]', '100.0万元', '[\"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '高', '2026年12月1日10点前在安徽公共资源交易集团电子交易系统递交投标文件，项目咨询0551-66223922。', '合肥市瑶海区岱河路2号', '安徽省', '合肥市', 0, '0551-82312662；0551-66223922；李工 0551-66223923', '合肥职业技术学院对数字媒体艺术设计专业实训室进行改造，预算100万元，合同签订后30个日历日内完成供货及安装调试，2026年12月1日10点投标截止。', 117.359622, 31.915041, '合肥职业技术学院2026年数字媒体艺术设计专业实训室改造（二次）公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261110/bee0bfef-af62-4c3d-8bc9-de9f8251d3c8.html?ztbtab=002002001&biaoduanguid=c6432f56-285e-48c3-a157-fe68b77b3ae9', '9e7b0c75071efcfa4bc1eaef0e7dbc4a', '2026-11-10', '2026-11-13 09:28:46');
INSERT INTO `crm_shangji` VALUES (63, '合肥市文化和旅游局（合肥市广播电视局、合肥市文物局）', '文化传媒', '[\"安徽广播电视精品创作周采购等一项\", \"详见磋商文件\"]', '60万元', '[\"本项目不接受联合体\", \"本项目为非专门面向中小企业采购项目\"]', '高', '2026年11月20日10点前在安徽公共资源交易集团电子交易系统提交响应文件，项目咨询0551-66223922。', '', '安徽省', '合肥市', 0, '李工；0551-66223646；0551-66223922；0551-63509966', '合肥市文化和旅游局采购安徽广播电视精品创作周项目一项，预算金额及最高限价均为60万元，合同履行至活动履约完成并通过验收，响应文件提交截止时间为2026年11月20日10点。', NULL, NULL, '安徽广播电视精品创作周竞争性磋商公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261109/6f897914-b71b-4183-a389-f8bb6cfb5890.html?ztbtab=002002001&biaoduanguid=fefbd876-fde8-4a8e-b1fd-64cd96c5e3cf', '810a8133c394777d73ad9dfcb7b805d7', '2026-11-09', '2026-11-13 09:28:46');
INSERT INTO `crm_shangji` VALUES (64, '合肥市公安局交通管理支队', '信息化', '[\"智慧铁骑违法抓拍设备采购等一批\", \"合同签订后3个自然日内完成供货\", \"4个自然日内完成安装调试\", \"5个自然日内完成数据接入\"]', '182.04万元', '[\"投标人所提供的货物为中小微企业、监狱企业或残疾人福利性单位制造\", \"本项目为专门面向中小企业采购项目\", \"本项目不接受联合体投标\"]', '高', '2026年12月1日10点前登录电子服务系统递交投标文件，项目咨询0551-66223922', '合肥市包河区马鞍山南路168号', '安徽省', '合肥市', 0, '0551-66269067；0551-66223922；李工 0551-66223923', '合肥市公安局交通管理支队采购智慧铁骑违法抓拍设备一批，预算及最高限价均为182.04万元，要求合同签订后3日内供货、4日内安装调试、5日内完成数据接入，专门面向中小企业采购。', 117.301709, 31.830769, '智慧铁骑违法抓拍设备采购公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261109/f6c082e6-f9a3-4326-b2d0-75cd1002208b.html?ztbtab=002002001&biaoduanguid=eb55c7ed-92ad-4cc3-9f16-0c6b70effec9', 'abd9f8bd6d83694b0e9614aa303702ce', '2026-11-09', '2026-11-13 09:28:46');
INSERT INTO `crm_shangji` VALUES (65, '安徽省疾病预防控制中心', '医疗', '[\"安徽省流感疫苗采购第6包\", \"本包别拟采购一家服务单位\", \"合同期限内按采购人要求分批供货\", \"中标人按采购人供货需求发货\", \"每次发货应尽可能为同批次疫苗\"]', '327万元', '[\"投标人须具有有效的药品生产许可证\", \"投标人须为所投产品的生产厂家\", \"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '高', '2026年11月16日17:30前登录电子服务系统获取招标文件，11月30日10点前递交投标文件', '合肥市蜀山区繁华大道12560号', '安徽省', '合肥市', 0, '0551-63674877；0551-66223922；李工 0551-66223923', '安徽省疾病预防控制中心采购安徽省流感疫苗第6包，预算327万元，最高限价9元/支，合同履行至2027年5月31日分批供货，投标人须为生产厂家并具有药品生产许可证。', 117.196289, 31.78373, '安徽省流感疫苗采购第6包公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261109/7307ca96-8919-4e50-9799-5b2cb40bf4cc.html?ztbtab=002002001&biaoduanguid=e6a6705a-6fcc-47c9-a6cc-3135b15b3d8a', '2a1663dc695c473533cdc1dbd608b2ee', '2026-11-09', '2026-11-13 09:28:46');
INSERT INTO `crm_shangji` VALUES (66, '合肥市交通运输局', '市政', '[\"合肥市国家综合货运枢纽补链强链提升行动全过程技术咨询服务\"]', '400万元', '[\"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '高', '2026年12月1日10点前登录电子服务系统递交投标文件，项目咨询电话0551-66223922', '合肥市', '安徽省', '合肥市', 0, '0551-62755629；0551-66223922；李工 0551-66223923', '合肥市交通运输局采购合肥市国家综合货运枢纽补链强链提升行动全过程技术咨询服务，预算及最高限价均为400万元，合同履行期限至2029年12月31日，投标截止时间为2026年12月1日10点。', 117.227267, 31.820567, '合肥市国家综合货运枢纽补链强链提升行动全过程技术咨询服务公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261109/77332618-5422-4393-aded-99fa92d0f0a4.html?ztbtab=002002001&biaoduanguid=1f84caf4-7f90-4807-8086-22b177cb4eb4', 'fe4f16dc18ca5edae8d4f0c64d120d57', '2026-11-09', '2026-11-13 09:28:47');
INSERT INTO `crm_shangji` VALUES (67, '合肥理工学院', '教育', '[\"实验室分析测试仪器采购一批\", \"完成供货安装\"]', '148万元', '[\"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '高', '2026年12月1日10点前在电子服务系统递交投标文件，项目咨询电话0551-66223922', '合肥市巢湖半岛生态科学城治中路6号', '安徽省', '合肥市', 0, '0551-62619895；0551-66223922；李工 0551-66223923', '合肥理工学院采购实验室分析测试仪器一批，预算及最高限价均为148万元，合同签订接通知后90个日历日内完成供货安装，投标截止2026年12月1日10点。', 117.594929, 31.609494, '合肥理工学院实验室分析测试仪器采购项目公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261109/b21b0612-ac48-46d5-ba19-4d21b99471a2.html?ztbtab=002002001&biaoduanguid=b2651289-5804-4824-af97-fe1e91282dee', '9a3cb95957da6d84836b5e45750fb613', '2026-11-09', '2026-11-13 09:28:47');
INSERT INTO `crm_shangji` VALUES (68, '肥东县中医医院', '医疗', '[\"肥东县中医医院物业（安保）服务\", \"首次服务期限为一年，可续签一次，总服务期限不超过两年（合同一年一签）\"]', '112.000000万元', '[\"供应商所提供的服务由中小微企业、监狱企业或残疾人福利性单位承接\", \"本项目为专门面向中小企业采购项目\", \"本项目不接受联合体\"]', '高', '2026年11月19日前登录安徽合肥公共资源交易电子服务系统获取采购文件，11月20日09点前提交响应文件', '安徽省合肥市肥东县店埠镇人民路18号', '安徽省', '合肥市', 7, '0551-67701248；黄丽 0551-62520569', '肥东县中医医院采购物业（安保）服务项目，预算112万元，服务期一年可续签一次、总期限不超过两年，面向中小企业采购，响应文件提交截止2026年11月20日09点。', 117.476139, 31.890343, '肥东县中医医院物业（安保）服务项目', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261109/0685c0d9-1af9-4e5e-863a-6ec7b1d4078e.html', '38dff26e3ab42106abe5448d96820d1d', '2026-11-09', '2026-11-13 09:28:47');
INSERT INTO `crm_shangji` VALUES (69, '合肥市第一人民医院', '医疗', '[\"第1包PCR、免疫组化相关试剂配送服务\", \"第4包临检免疫血型相关试剂配送服务\", \"第5包湿式生化免疫相关试剂配送服务\", \"第6包临检尿便体液相关试剂配送服务\", \"第7包福尔马林固定液配送服务\", \"第8包生化肝功能免疫相关试剂配送服务\", \"合同生效后1年内按采购人要求分批供货，每批货物接通知后3个日历日内完成供货\"]', '第1包84.83553万元；第4包380.961729万元；第5包196.639376万元；第6包283.183142万元；第7包6.232454万元；第8包3.0400208万元', '[\"本项目专门面向中小企业采购（即投标人所提供的服务为中小微企业、监狱企业或残疾人福利性单位承接）\", \"具有医疗器械生产或经营资格\", \"本项目不接受联合体投标\"]', '高', '2026年12月1日10点前登录电子服务系统获取招标文件并递交投标文件，项目咨询0551-66223922', '合肥市第一人民医院各院区（采购人地址：合肥市庐阳区淮河路390号）', '安徽省', '合肥市', 0, '0551-62183803；0551-66223922；李工 0551-66223923', '合肥市第一人民医院采购各院区检验试剂及辅材配送服务第1、4-8包（三次），预算合计约954.89万元，合同期1年，专门面向中小企业，投标截止2026年12月1日10点。', NULL, NULL, '合肥市第一人民医院各院区检验试剂及辅材配送服务第1、4-8包（三次）公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261109/d2c09431-ecc2-4263-a08b-83e0fb1d7d5c.html?ztbtab=002002001&biaoduanguid=4f57d8fa-85e1-498a-8dfd-a5000fa0d44c', '9c33bb3b905e508c7faa4244650abb25', '2026-11-09', '2026-11-13 09:28:48');
INSERT INTO `crm_shangji` VALUES (70, '安徽合肥新站高新技术产业开发区建设发展局', '信息化', '[\"承接新站高新区2026年国土变更调查第三方技术服务\", \"提供测绘相关技术服务\", \"服务期限采用1+X(X≤2)模式，合同期一年\"]', '150万元', '[\"具有测绘行政主管部门颁发的乙级及以上测绘资质（专业类别须同时包含工程测量、界线与不动产测绘、地理信息系统工程、摄影测量与遥感）\", \"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '高', '2026年11月20日09时00分前登录安徽合肥公共资源交易中心电子交易系统获取文件并提交响应文件，项目咨询0551-65777681。', '合肥市新站高新区', '安徽省', '合肥市', 0, '孙瑜；0551-65777681；0551-65777088', '安徽合肥新站高新技术产业开发区建设发展局采购新站高新区2026年国土变更调查第三方技术服务，预算150万元，服务期一年，采用竞争性磋商方式，响应文件提交截止2026年11月20日09时00分。', 117.222942, 31.796672, '新站高新区2026年国土变更调查第三方技术服务竞争性磋商公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261109/9eb89b51-c5f1-4b79-bdb3-6ed75814f5f2.html?ztbtab=002002001&biaoduanguid=d3c19684-2caf-2fb8-0ea1-357874728409', 'f03df81e73a953e5353e6a26d745095c', '2026-11-09', '2026-11-13 09:28:48');
INSERT INTO `crm_shangji` VALUES (71, '安徽肥西经济开发区管理委员会', '建筑工程', '[\"汇峰苹果小镇消防维修改造项目设计与施工\", \"1#、2#楼等住宅及综合楼消防维修改造\", \"3#至11#楼一类高层住宅及公共建筑消防维修改造\", \"地下车库消防维修改造\", \"合同签订后5个工作日内完成设计部分\"]', '150万元', '[\"供应商所提供的工程为中小微企业、监狱企业或残疾人福利性单位承建\", \"设计资质须具备消防设施工程设计专项甲级、建筑行业（建筑工程）专业工程设计甲级、建筑行业工程设计甲级或工程设计综合甲级之一\", \"施工资质须具备有效的消防工程专业承包一级资质及安全生产许可证\", \"联合体家数（含牵头方）不超过2家\"]', '高', '2026年11月13日10时前在安徽合肥公共资源交易中心电子交易系统提交响应文件，项目咨询0551-68825072。', '合肥经开区丹霞路与青龙潭路交口汇峰苹果小镇', '安徽省', '合肥市', 0, '夏腾飞 0551-68825072；采购人 0551-68991668', '安徽肥西经济开发区管理委员会采购肥西经开区汇峰苹果小镇消防维修改造项目，预算150万元，最高限价1500000.00元，工期40日历天，采用竞争性谈判方式。', 117.219655, 31.766165, '肥西经开区汇峰苹果小镇消防维修改造项目竞争性谈判公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261109/394d3cb8-2da3-b84c-c376-4656043b3c59.html?ztbtab=002002001&biaoduanguid=f83e0184-231d-a526-af73-9a358a5ba4b7', 'bf714ff65439ff80749f280a888cbada', '2026-11-09', '2026-11-13 09:28:49');
INSERT INTO `crm_shangji` VALUES (72, '合肥市第二人民医院', '医疗', '[\"合肥市第二人民医院医疗设备购置第4-7包等一批\", \"第4包医疗设备\", \"第5包医疗设备\", \"第6包医疗设备（含高频电氩气治疗仪）\", \"第7包医疗设备\", \"合同生效后10个日历天内完成供货及安装\"]', '第4包：32.32万元，第5包：20万元，第6包：56万元，第7包：49.5万元', '[\"第4、6、7包：具有医疗器械生产或医疗器械经营资格\", \"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '高', '2026年11月27日11点前登录电子服务系统获取招标文件并上传投标文件，项目咨询0551-66223922。', '合肥市瑶海区和平路246号', '安徽省', '合肥市', 0, '0551-62965091；0551-66223922；李工 0551-66223923', '合肥市第二人民医院公开招标医疗设备购置第4-7包，预算分别为32.32万元、20万元、56万元、49.5万元，合同生效后10个日历天内完成供货及安装，投标截止2026年11月27日11点。', 117.318423, 31.856642, '合肥市第二人民医院医疗设备购置第4-7包公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261106/e97f91d2-fbe5-4351-a750-9c206294c4d4.html?ztbtab=002002001&biaoduanguid=0673a140-1782-4579-af47-23e47633fd64', '983ef3237061e8fd1a7fddef34656747', '2026-11-06', '2026-11-13 09:28:49');
INSERT INTO `crm_shangji` VALUES (73, '合肥市第二人民医院', '医疗', '[\"医疗设备购置第1包\", \"医疗设备购置第2包\", \"医疗设备购置第3包\", \"合同生效后10个日历天内完成供货及安装\"]', '第1包107.5万元;第2包72.1万元;第3包42.3万元', '[\"第1-3包：具有医疗器械生产或医疗器械经营资格\", \"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '高', '2026年11月27日11点前在安徽公共资源交易集团电子交易系统递交投标文件，项目咨询0551-66223922', '合肥市瑶海区和平路246号', '安徽省', '合肥市', 0, '0551-62965091;0551-66223922;李工 0551-66223923', '合肥市第二人民医院公开招标医疗设备购置第1-3包，预算分别为107.5万元、72.1万元、42.3万元，合同生效后10个日历天内完成供货及安装，投标截止2026年11月27日11点。', 117.318423, 31.856642, '合肥市第二人民医院医疗设备购置第1-3包公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261106/d2c65358-9222-4c11-8989-af4450fad183.html?ztbtab=002002001&biaoduanguid=3ade9ea2-3f6c-4be2-b6ec-b4be939ab905', 'fe2dee044bc7e090c2bccfe59105d247', '2026-11-06', '2026-11-13 09:28:50');
INSERT INTO `crm_shangji` VALUES (74, '合肥市应急管理局', '安全生产服务', '[\"第1包长丰和庐阳企业现场评审等一批\", \"第2包新站和瑶海企业现场评审等一批\", \"第3包高新和蜀山企业现场评审等一批\", \"第4包肥东和包河企业现场评审等一批\", \"第5包经开和肥西企业现场评审等一批\", \"第6包庐江、巢湖市、安巢企业现场评审等一批\", \"第7包三级安全生产标准化评审等一批\"]', '第1包23.3728万元，第2包23.3728万元，第3包23.3728万元，第4包23.3728万元，第5包23.3728万元，第6包23.9360万元，第7包19.2万元', '[\"本项目第1-6包：专门面向中小企业采购（即供应商提供的服务为中小微企业、监狱企业或残疾人福利性单位承接）\", \"本项目是否接受联合体:否\", \"供应商应合理安排采购文件获取时间，特别是网络速度慢的地区防止在系统关闭前网络拥堵无法操作。如果因计算机及网络故障造成无法完成采购文件获取，责任自负\"]', '高', '2026年11月17日10点前在安徽公共资源交易集团电子交易系统提交响应文件，项目咨询0551-66223922、66223923。', '合肥市', '安徽省', '合肥市', 0, '0551-62755812；0551-66223922、66223923；李工 0551-66223646', '合肥市应急管理局采购2026年度合肥市三级安全生产标准化现场评审工作，分7个包，预算合计约160万元，合同签订后原则上12个月内完成。', 117.227267, 31.820567, '2026年度合肥市三级安全生产标准化现场评审工作竞争性磋商公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261106/ca05007f-b1e2-4ecb-93e6-cf944815d1e2.html?ztbtab=002002001&biaoduanguid=6971bede-3caf-488b-aa20-a75b8115f2b5', '21a7a03e4c26791e46690be0813c15d0', '2026-11-06', '2026-11-13 09:28:51');
INSERT INTO `crm_shangji` VALUES (75, '安徽省疾病预防控制中心', '医疗', '[\"采购吡喹酮片\", \"用于2026年中央补助血吸虫病防治\"]', '138.6万元', '[]', '中', '关注单一来源采购公告，联系采购人确认供应商及文件获取方式', '', '安徽省', '合肥市', 0, '', '安徽省疾病预防控制中心实施2026年中央补助血吸虫病防治吡喹酮片采购，采用单一来源采购方式，预算金额138.6万元。', NULL, NULL, '2026年中央补助血吸虫病防治吡喹酮片采购单一来源公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261106/f93c29f8-7204-4ded-b718-23a069a69a60.html?ztbtab=002002001&biaoduanguid=a469e439-f584-4dc2-b2fa-1b2e38290016', '7d85881e4e942a4c904d8e748bf863b7', '2026-11-06', '2026-11-13 09:28:51');
INSERT INTO `crm_shangji` VALUES (76, '安徽省疾病预防控制中心', '医疗', '[\"采购日本血吸虫抗体检测试剂盒（IHA）\", \"用于2026年中央补助血吸虫病防治项目\"]', '154.0万元', '[]', '中', '关注单一来源采购公示及招标文件，联系采购人确认供应商及后续流程', '', '安徽省', '合肥市', 0, '', '安徽省疾病预防控制中心实施2026年中央补助血吸虫病防治日本血吸虫抗体检测试剂盒（IHA）采购，预算154.0万元，采用单一来源采购方式。', NULL, NULL, '2026年中央补助血吸虫病防治日本血吸虫抗体检测试剂盒（IHA）采购单一来源公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261106/4b72e165-4e22-4311-94e8-fcd45826b006.html?ztbtab=002002001&biaoduanguid=4bec6c7d-b82c-4500-a5e0-8b36745ca51b', 'a4d327900efe970c5c2d7afe2065c45c', '2026-11-06', '2026-11-13 09:28:51');
INSERT INTO `crm_shangji` VALUES (77, '安徽省第二人民医院（安徽医学高等专科学校附属医院、安徽省职业病防治院）', '信息化', '[\"上海交通大学医学院附属仁济医院安徽医院OA（办公自动化）系统采购一批\", \"合同签订之日起120个日历日内完成供货、安装调试和交付使用\"]', '60万元', '[\"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '高', '2026年11月13日17:30前登录安徽公共资源交易集团电子交易系统获取招标文件，11月27日10点前递交投标文件', '合肥市瑶海区砀山路1868号', '安徽省', '合肥市', 0, '0551-64280881；0551-66223645；李工 0551-66223646', '安徽省第二人民医院（安徽医学高等专科学校附属医院、安徽省职业病防治院）采购上海交通大学医学院附属仁济医院安徽医院OA（办公自动化）系统一批，预算及最高限价均为60万元，合同签订之日起120个日历日内完成供货、安装调试和交付使用。', 117.306394, 31.895456, '上海交通大学医学院附属仁济医院安徽医院OA（办公自动化）系统采购公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261106/7ae8dd90-d167-49e4-a92f-5076981b9a55.html?ztbtab=002002001&biaoduanguid=26358b1a-b2f3-4764-82f1-80ba1c0c7c6b', '9dcc09019452583af227f6918acd4832', '2026-11-06', '2026-11-13 09:28:51');
INSERT INTO `crm_shangji` VALUES (78, '安徽科技工程大学', '教育', '[\"新能源学院实验教学仪器设备采购等一批\", \"合同签订后30日内供货并安装调试完毕\"]', '360万元', '[\"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '高', '2026年11月13日17:30前登录安徽公共资源交易集团电子交易系统获取招标文件，11月27日11点前递交投标文件。', '滁州市凤阳县东华路9号', '安徽省', '滁州市', 0, '项目联系人：李工 0551-66223923；采购人 0550-6733690；代理机构 0551-66223922', '安徽科技工程大学采购新能源学院实验教学仪器设备一批，预算及最高限价均为360万元，合同签订后30日内供货并安装调试完毕，投标截止时间为2026年11月27日11点。', 117.564183, 32.874512, '安徽科技工程大学新能源学院实验教学仪器设备采购项目（三次）公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261106/97a730ec-d378-44fa-8c9e-d499fc4beee1.html?ztbtab=002002001&biaoduanguid=757ea369-3cbc-4f4f-b29e-ddd09aec8460', 'caa187f6b9bd84e199497a2cdf343cd2', '2026-11-06', '2026-11-13 09:28:51');
INSERT INTO `crm_shangji` VALUES (79, '合肥市农业农村局', '医疗', '[\"采购种猪伪狂犬病活疫苗（HB2000株）\", \"采购猪瘟病毒E2蛋白重组杆状病毒灭活疫苗\", \"按采购人通知的时间和数量5个工作日内送达指定地点\", \"2026年12月20日前完成全部产品供货\"]', '51.29万元', '[\"本项目专门面向中小企业采购，投标人所提供的货物须为中小微企业、监狱企业或残疾人福利性单位所制造\", \"投标人如为生产商：须提供有效的《兽药生产许可证》（生产范围须同时包含猪伪狂犬病活疫苗（HB2000株）及猪瘟病毒E2蛋白重组杆状病毒灭活疫苗）和《兽药GMP证书》\", \"投标人如为经销商/代理商：须提供有效的《兽药经营许可证》（经营范围包含兽用生物制品），并承诺企业经营活动持续符合《兽药经营质量管理规范》（兽药GSP）要求\", \"本项目不接受联合体投标\"]', '高', '2026年11月27日10:30前登录安徽公共资源交易集团电子交易系统获取招标文件并递交投标文件，项目咨询电话0551-66223922、66223923。', '合肥市', '安徽省', '合肥市', 0, '李工；0551-66223646；0551-66223922；0551-66223923', '合肥市农业农村局采购2026年种猪伪狂犬等疫苗一批，预算及最高限价均为51.29万元，要求2026年12月20日前完成全部供货，本项目专门面向中小企业采购。', 117.227267, 31.820567, '合肥市2026年种猪伪狂犬等疫苗采购项目公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261106/5bf5acf6-cfd5-458e-8c74-74a440f7a4c2.html?ztbtab=002002001&biaoduanguid=8ba012e9-2759-405d-a17c-31e1f79f92a5', '54899ffaa8ae1562f9fabde15df2f6b9', '2026-11-06', '2026-11-13 09:28:52');
INSERT INTO `crm_shangji` VALUES (80, '合肥市妇女儿童保健中心', '医疗', '[\"非衍生化多种氨基酸、肉碱和琥珀酰丙酮测定试剂盒配送服务\", \"相关耗材配送服务\"]', '741.01466万元', '[\"具有医疗器械生产或医疗器械经营资格\", \"本项目不接受联合体投标\", \"本项目为非专门面向中小企业采购项目\"]', '高', '2026年11月27日10点30分前登录电子服务系统递交投标文件，项目咨询电话0551-66223922。', '合肥市包河区云谷路与玉龙路交口', '安徽省', '合肥市', 0, '0551-62161066；0551-66223922；李工 0551-66223923', '合肥市妇女儿童保健中心采购非衍生化多种氨基酸、肉碱和琥珀酰丙酮测定试剂盒及耗材等配送服务，预算741.01466万元，最高限价733.87126万元，合同期一年，可续签累计不超过3年。', 117.278019, 31.729377, '合肥市妇女儿童保健中心非衍生化多种氨基酸、肉碱和琥珀酰丙酮测定试剂盒及耗材等配送服务（二次）公开招标公告', 'https://ggzy.hefei.gov.cn/jyxx/002002/002002001/20261106/fe404dab-ccc6-435c-9e87-46d58a1cf15f.html?ztbtab=002002001&biaoduanguid=ff4ddf00-acf1-4ffb-bc24-43193b5b2af6', 'b71562da9097a053ceac8feed91ca33c', '2026-11-06', '2026-11-13 09:28:52');

-- ----------------------------
-- Table structure for crm_summary
-- ----------------------------
DROP TABLE IF EXISTS `crm_summary`;
CREATE TABLE `crm_summary`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `lead_id` bigint UNSIGNED NOT NULL COMMENT '商机ID',
  `tags` json NULL COMMENT '标签列表',
  `summary` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '摘要',
  `analysis` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '项目分析',
  `lessons` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '经验总结',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_lead`(`lead_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '项目总结表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of crm_summary
-- ----------------------------
INSERT INTO `crm_summary` VALUES (1, 46, '[\"农村污水处理\", \"一体化污水处理站\", \"污水管网改造\", \"泵站改造\", \"市政公用工程\", \"中小微企业\"]', '肥东县众兴乡人民政府招标农村污水处理升级改造工程，预算199.21万元，含新建200立方一体化污水处理站、管网及泵站改造，工期90日历天。要求市政公用工程施工总承包三级及以上资质，不接受联合体。意向等级中。已电话预约下周拜访，获取采购文件截止2026年11月23日，响应文件11月24日09点前提交。', '**商机**：预算199.21万元，含新建200立方一体化污水处理站、管网及泵站改造，工期90天，需求明确，属环保市政领域，可切入。\n\n**风险**：须中小微企业承建、市政三级及以上资质及安全生产许可证，不接受联合体；响应截止11月24日，时间紧。跟进记录中联系人（张总）与公告联系人（李博凌）不一致，且附件多为废气/除臭方案，与本项目匹配度存疑。\n\n**竞争**：资料未提供竞争对手信息，无法判断。\n\n**建议**：尽快核实资质与中小微身份，确认对接人；按污水站需求调整方案与报价，11月23日前获取采购文件并按时提交。', '经验：跟进中通过多渠道获取关键人信息并预约拜访，但首次拜访受阻，需提前确认准入；投标资料准备较充分，有多版方案和报价。教训：方案附件与污水项目不匹配（废气、除臭、VOC），存在资料错用风险；时间紧，须在11月24日前完成文件提交，并核实中小微企业承建、市政三级资质及不接受联合体等限制。', '2026-11-13 09:33:12');
INSERT INTO `crm_summary` VALUES (5, 45, '[\"消毒供应设备\", \"医疗采购\", \"口腔医院\", \"医疗器械资质\", \"不接受联合体\", \"合肥\"]', '合肥市口腔医院2026年消毒供应设备采购，预算116.5万元，位于合肥包河区。需求含设备供货、安装、调试、培训，合同生效接通知后30个日历日内完成。投标人须具备医疗器械生产或经营资格，不接受联合体，非专门面向中小企业。意向等级中。2026年12月1日前获取招标文件，12月2日10:00前递交投标文件。', '**商机**：预算116.5万元，需求明确（供货、安装、调试、培训），医疗消毒设备属刚需，意向等级中，可跟进。\n\n**风险**：须具备医疗器械生产或经营资格；不接受联合体；非专门面向中小企业；30日内完成交付，工期紧。\n\n**竞争**：未提供竞争对手信息，无法判断。\n\n**建议**：尽快确认自身资质，12月1日前获取招标文件，12月2日10:00前递交投标文件，提前备货保障30日交付。', '该项目经验：需提前确认医疗器械生产或经营资格，注意不接受联合体投标；应尽早登录电子服务系统获取招标文件，避免临近截止。教训：时间节点紧（12月1日获取、12月2日递交），须提前准备投标材料；非专门面向中小企业，需评估自身竞争力。', '2026-11-13 09:54:01');
INSERT INTO `crm_summary` VALUES (6, 43, '[\"教育\", \"实验室升级改造\", \"设备采购\", \"公开招标\", \"安徽合肥\", \"不接受联合体\"]', '合肥职业技术学院公开招标“2026年分子生物学实验室升级改造（二次）”，预算及最高限价68万元，内容为实验室升级改造及相关设备采购、供货与安装调试，合同签订后45个日历日内完成。项目位于合肥市瑶海区，不接受联合体投标，非专门面向中小企业。投标截止2026年12月2日10:30，意向等级高。跟进记录显示已收集资料及负责人电话。', '**商机**：预算68万元，教育行业实验室升级改造，意向等级高，需求明确（设备采购及安装调试），45日内交付，可跟进。\n\n**风险**：不接受联合体投标，非专门面向中小企业，需独立具备资质；二次招标或存流标背景，竞争可能集中。\n\n**竞争**：公开招标，合肥本地及省内实验室设备集成商或参与，需评估自身资质与价格空间。\n\n**建议**：尽快联系李工确认技术参数与资格要求，评估独立投标可行性，提前准备文件，12月2日前递交。', '该项目为二次招标，提示首次招标可能流标，应关注首次失败原因。经验：及时收集资料并联系负责人，跟进较主动。教训：需尽早核实二次招标背景及非专门面向中小企业、不接受联合体等限制对投标策略的影响，并预留充足时间准备文件。', '2026-11-13 09:54:27');
INSERT INTO `crm_summary` VALUES (7, 41, '[\"商用电脑采购\", \"信息化终端\", \"公开招标\", \"安徽医科大学第一附属医院\", \"合肥市\", \"分批供货\"]', '安徽医科大学第一附属医院（北区）国家重大传染病防治基地信息化终端商用电脑采购及配送项目（二次）公开招标，招标人为安徽医科大学第一附属医院，预算258万元，地点合肥市蜀山区。需求为商用电脑采购及分批配送，每批接通知后15个日历日内供货，供货周期1年。不接受联合体投标，非专门面向中小企业。意向等级高。需2026年11月18日17:30前获取招标文件，12月2日10点前递交投标文件。', '商机：预算258万元，医院信息化终端采购，意向等级高，分批供货周期一年，需求明确。风险：不接受联合体，非专门面向中小企业，需自行满足资质；投标时间紧。竞争：公开招标，合肥本地及省内电脑供应商可能参与，价格与服务竞争为主。建议：尽快获取招标文件，核实中小企业价格扣除政策，联合厂商锁定货源与15日供货能力，突出本地配送和售后响应，按时递交。', '该项目为二次招标，需关注首次流标原因，提前对接采购人及代理机构，确认技术参数与分批供货要求。经验：意向等级高、预算明确，应尽早获取招标文件并准备投标。教训：不接受联合体且非专门面向中小企业，需独立满足资质；供货时限紧，须提前落实货源与配送能力。', '2026-11-13 09:54:53');

-- ----------------------------
-- Table structure for crm_user
-- ----------------------------
DROP TABLE IF EXISTS `crm_user`;
CREATE TABLE `crm_user`  (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `username` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户名',
  `password_hash` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '密码哈希(PBKDF2)',
  `nickname` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '昵称',
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'user' COMMENT '角色:admin/user',
  `status` tinyint NOT NULL DEFAULT 1 COMMENT '状态:1启用 0禁用',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_username`(`username` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 12 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'CRM用户表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of crm_user
-- ----------------------------
INSERT INTO `crm_user` VALUES (1, 'admin', 'pbkdf2_sha256$200000$1cfbf6735c16b21a6ee3a9f21b89759e$ead4cfe881b696247a711c5bd4677109fef6bb8abacb4a0b5046fe9d4cd2403e', '管理员', 'admin', 1, '2026-11-12 20:19:19', '2026-11-12 23:33:56');
INSERT INTO `crm_user` VALUES (2, 'user', 'pbkdf2_sha256$200000$d2f09f86e59047d1cb630d6f2efcaf9a$0da085944f716ce6c4d84472cdc00244498ab8787a08cadd6dbbb794e4fe6446', '普通用户', 'user', 1, '2026-11-12 20:19:19', '2026-11-12 23:33:57');
INSERT INTO `crm_user` VALUES (3, 'user01', 'pbkdf2_sha256$200000$d4a72ce2452dbd32f5dc9fc639ba5644$facd0747a298412147398ab80a935b57c912b07e75d00402c8bb23e92e203e0f', '用户01', 'user', 1, '2026-11-12 23:33:57', '2026-11-12 23:33:57');
INSERT INTO `crm_user` VALUES (4, 'user02', 'pbkdf2_sha256$200000$1e40c754e2cea60763f7d3d5f151e8a3$42a5d667d067391c3fd5aaec16b54574bba3630576c5f30b5bb7d57d8454a7df', '用户02', 'user', 1, '2026-11-12 23:33:57', '2026-11-12 23:33:57');
INSERT INTO `crm_user` VALUES (5, 'user03', 'pbkdf2_sha256$200000$6253c5c5cd15e3210ae85ca3528c5e8d$5369b17198c100873839bf1942b788e97249303df6ae922ffddeec91ed2b1627', '用户03', 'user', 1, '2026-11-12 23:33:57', '2026-11-12 23:33:57');
INSERT INTO `crm_user` VALUES (6, 'user04', 'pbkdf2_sha256$200000$fc666929ccbd207e803034a60e67bdc3$7c607c8a35047d50bd3dfe271a8f2f97b6b6f829a2f45bec43ba8386540b1afa', '用户04', 'user', 1, '2026-11-12 23:33:57', '2026-11-12 23:33:57');
INSERT INTO `crm_user` VALUES (7, 'user05', 'pbkdf2_sha256$200000$caeb377eb884d6e43236f59de66c035b$42bffcee1cd46c7a04a502aa4d4f0dbc7f891accd745a3b15f0f412e92c2df97', '用户05', 'user', 1, '2026-11-12 23:33:57', '2026-11-12 23:33:57');
INSERT INTO `crm_user` VALUES (8, 'user06', 'pbkdf2_sha256$200000$ea7ed01e0832c450f47568c75c71e084$cd39e175d35caedcd9676228a576a493670ed7255f6b4f19033fa83d74c3d48d', '用户06', 'user', 1, '2026-11-12 23:33:58', '2026-11-12 23:33:58');
INSERT INTO `crm_user` VALUES (9, 'user07', 'pbkdf2_sha256$200000$c3cc0d11606e862ba85af1b7ef1d4a1e$3462925435ad4ad90f5a7a89b3329d0b17016a98bc78bbd69e4d1a4b29038bb2', '用户07', 'user', 1, '2026-11-12 23:33:58', '2026-11-12 23:33:58');
INSERT INTO `crm_user` VALUES (10, 'user08', 'pbkdf2_sha256$200000$ae01baef6f804ed34b231ea439a7c606$bf448ad1485704650ab152a51cad90a72f6db849fddbc0156e9b4c205bbf300f', '用户08', 'user', 1, '2026-11-12 23:33:58', '2026-11-12 23:33:58');
INSERT INTO `crm_user` VALUES (11, 'kzt', 'pbkdf2_sha256$200000$a3f63105995de858f0e33ddb19d6b978$e9e1d1cb08e9853ef3b99d261c2c47643385ed8c457f55ca511a0d08be1da730', 'admin', 'user', 1, '2026-11-13 09:52:34', '2026-11-13 09:52:34');

SET FOREIGN_KEY_CHECKS = 1;
