/*
 Navicat Premium Data Transfer

 Source Server         : localhost_3306
 Source Server Type    : MySQL
 Source Server Version : 80031
 Source Host           : localhost:3306
 Source Schema         : research_db

 Target Server Type    : MySQL
 Target Server Version : 80031
 File Encoding         : 65001

 Date: 13/04/2026 13:44:17
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for announcements
-- ----------------------------
DROP TABLE IF EXISTS `announcements`;
CREATE TABLE `announcements`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '公告ID',
  `title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '公告标题',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '公告内容',
  `publisher_id` bigint NOT NULL COMMENT '发布人ID',
  `priority` int NOT NULL DEFAULT 0 COMMENT '优先级: 0=普通 1=重要 2=紧急',
  `status` tinyint NOT NULL DEFAULT 1 COMMENT '状态: 0=下架 1=发布',
  `view_count` int NOT NULL DEFAULT 0 COMMENT '浏览次数',
  `publish_time` datetime NULL DEFAULT NULL COMMENT '定时发布时间',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_status_time`(`status` ASC, `publish_time` ASC) USING BTREE,
  INDEX `fk_announcement_publisher`(`publisher_id` ASC) USING BTREE,
  CONSTRAINT `fk_announcement_publisher` FOREIGN KEY (`publisher_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '系统公告表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of announcements
-- ----------------------------

-- ----------------------------
-- Table structure for behavior_log
-- ----------------------------
DROP TABLE IF EXISTS `behavior_log`;
CREATE TABLE `behavior_log`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `paper_id` bigint NOT NULL COMMENT '论文ID',
  `action` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '行为类型: click/favorite/read',
  `duration` int NULL DEFAULT NULL COMMENT '阅读时长（秒，action=read 时有值）',
  `source` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '来源页面: recommend/search/detail',
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '行为发生时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_paper_id`(`paper_id` ASC) USING BTREE,
  INDEX `idx_timestamp`(`timestamp` ASC) USING BTREE,
  INDEX `idx_user_action`(`user_id` ASC, `action` ASC) USING BTREE,
  CONSTRAINT `fk_behavior_paper` FOREIGN KEY (`paper_id`) REFERENCES `paper` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_behavior_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '用户行为日志表（RL 训练数据）' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of behavior_log
-- ----------------------------
INSERT INTO `behavior_log` VALUES (1, 1, 1, 'click', NULL, 'search', '2026-03-21 23:04:39');
INSERT INTO `behavior_log` VALUES (2, 1, 1, 'favorite', NULL, 'search', '2026-03-21 23:04:40');
INSERT INTO `behavior_log` VALUES (3, 1, 1, 'click', NULL, 'search', '2026-03-21 23:04:41');
INSERT INTO `behavior_log` VALUES (4, 1, 1, 'favorite', NULL, 'search', '2026-03-21 23:04:42');
INSERT INTO `behavior_log` VALUES (5, 1, 1, 'click', NULL, 'search', '2026-03-21 23:04:42');
INSERT INTO `behavior_log` VALUES (6, 1, 1, 'click', NULL, 'search', '2026-03-21 23:04:43');
INSERT INTO `behavior_log` VALUES (7, 1, 1, 'click', NULL, 'search', '2026-03-21 23:04:43');
INSERT INTO `behavior_log` VALUES (8, 1, 1, 'click', NULL, 'search', '2026-03-21 23:04:43');
INSERT INTO `behavior_log` VALUES (9, 1, 1, 'click', NULL, 'search', '2026-03-21 23:04:43');
INSERT INTO `behavior_log` VALUES (10, 1, 1, 'click', NULL, 'search', '2026-03-21 23:04:44');
INSERT INTO `behavior_log` VALUES (11, 1, 1, 'favorite', NULL, 'search', '2026-03-21 23:04:44');

-- ----------------------------
-- Table structure for board
-- ----------------------------
DROP TABLE IF EXISTS `board`;
CREATE TABLE `board`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '版块ID',
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '版块名称',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '版块描述',
  `icon` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '版块图标URL',
  `sort_order` int NOT NULL DEFAULT 0 COMMENT '排序号',
  `status` tinyint NOT NULL DEFAULT 1 COMMENT '状态: 0=禁用 1=启用',
  `post_count` int NOT NULL DEFAULT 0 COMMENT '帖子数量',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_name`(`name` ASC) USING BTREE,
  INDEX `idx_sort`(`sort_order` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '科研社区版块表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of board
-- ----------------------------

-- ----------------------------
-- Table structure for browse_history
-- ----------------------------
DROP TABLE IF EXISTS `browse_history`;
CREATE TABLE `browse_history`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `paper_id` bigint NOT NULL COMMENT '论文ID',
  `stay_duration` int NULL DEFAULT NULL COMMENT '停留时长(秒)',
  `browse_date` date NOT NULL COMMENT '浏览日期',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_paper_date`(`user_id` ASC, `paper_id` ASC, `browse_date` ASC) USING BTREE,
  INDEX `idx_user_time`(`user_id` ASC, `create_time` ASC) USING BTREE,
  INDEX `fk_browse_paper`(`paper_id` ASC) USING BTREE,
  CONSTRAINT `fk_browse_paper` FOREIGN KEY (`paper_id`) REFERENCES `paper` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_browse_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户浏览历史记录表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of browse_history
-- ----------------------------

-- ----------------------------
-- Table structure for comment
-- ----------------------------
DROP TABLE IF EXISTS `comment`;
CREATE TABLE `comment`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '评论ID',
  `post_id` bigint NOT NULL COMMENT '所属帖子ID',
  `user_id` bigint NOT NULL COMMENT '评论用户ID',
  `parent_id` bigint NULL DEFAULT NULL COMMENT '父评论ID(支持嵌套回复)',
  `root_id` bigint NULL DEFAULT NULL COMMENT '根评论ID(用于查询整个回复树)',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '评论内容',
  `like_count` int NOT NULL DEFAULT 0 COMMENT '点赞数',
  `is_best` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否精选: 0=否 1=是',
  `status` tinyint NOT NULL DEFAULT 1 COMMENT '状态: 0=删除 1=正常 2=审核中',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_post_id`(`post_id` ASC) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_root_id`(`root_id` ASC) USING BTREE,
  INDEX `idx_parent_id`(`parent_id` ASC) USING BTREE,
  INDEX `idx_create_time`(`create_time` ASC) USING BTREE,
  CONSTRAINT `fk_comment_parent` FOREIGN KEY (`parent_id`) REFERENCES `comment` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_comment_post` FOREIGN KEY (`post_id`) REFERENCES `post` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_comment_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '帖子评论/回复表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of comment
-- ----------------------------

-- ----------------------------
-- Table structure for favourite
-- ----------------------------
DROP TABLE IF EXISTS `favourite`;
CREATE TABLE `favourite`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '收藏ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `paper_id` bigint NOT NULL COMMENT '论文ID',
  `folder_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '默认收藏夹' COMMENT '收藏夹名称',
  `remark` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '收藏备注',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_paper`(`user_id` ASC, `paper_id` ASC) USING BTREE,
  INDEX `idx_user_folder`(`user_id` ASC, `folder_name` ASC) USING BTREE,
  INDEX `fk_fav_paper`(`paper_id` ASC) USING BTREE,
  CONSTRAINT `fk_fav_paper` FOREIGN KEY (`paper_id`) REFERENCES `paper` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_fav_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户论文收藏表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of favourite
-- ----------------------------

-- ----------------------------
-- Table structure for kg_entity
-- ----------------------------
DROP TABLE IF EXISTS `kg_entity`;
CREATE TABLE `kg_entity`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '实体ID',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '实体名称',
  `type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '实体类型: PAPER=论文 AUTHOR=作者 INSTITUTION=机构 KEYWORD=关键词 VENUE=期刊/会议',
  `external_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '外部ID(如AMiner作者ID)',
  `properties` json NULL COMMENT '实体属性(JSON格式)',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_name_type`(`name` ASC, `type` ASC) USING BTREE,
  INDEX `idx_type`(`type` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '知识图谱实体表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of kg_entity
-- ----------------------------

-- ----------------------------
-- Table structure for kg_relation
-- ----------------------------
DROP TABLE IF EXISTS `kg_relation`;
CREATE TABLE `kg_relation`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '关系ID',
  `source_id` bigint NOT NULL COMMENT '源实体ID',
  `target_id` bigint NOT NULL COMMENT '目标实体ID',
  `relation_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关系类型: AUTHOR_OF=作者 WRITE=写作 COLLABORATE=合作 CITE=引用 BELONG_TO=属于 RELATED_TO=相关',
  `weight` double NULL DEFAULT 1 COMMENT '关系权重',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_relation`(`source_id` ASC, `target_id` ASC, `relation_type` ASC) USING BTREE,
  INDEX `idx_source`(`source_id` ASC) USING BTREE,
  INDEX `idx_target`(`target_id` ASC) USING BTREE,
  CONSTRAINT `fk_rel_source` FOREIGN KEY (`source_id`) REFERENCES `kg_entity` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_rel_target` FOREIGN KEY (`target_id`) REFERENCES `kg_entity` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '知识图谱关系表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of kg_relation
-- ----------------------------

-- ----------------------------
-- Table structure for notification
-- ----------------------------
DROP TABLE IF EXISTS `notification`;
CREATE TABLE `notification`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '通知ID',
  `user_id` bigint NOT NULL COMMENT '接收用户ID(0表示全局广播)',
  `type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '通知类型: SYSTEM=系统 LIKE=点赞 COMMENT=评论 FOLLOW=关注 RECOMMEND=推荐',
  `title` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '通知标题',
  `content` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '通知内容',
  `related_id` bigint NULL DEFAULT NULL COMMENT '关联业务ID(如帖子ID、用户ID)',
  `is_read` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否已读: 0=未读 1=已读',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_user_type`(`user_id` ASC, `type` ASC) USING BTREE,
  INDEX `idx_user_read`(`user_id` ASC, `is_read` ASC, `create_time` ASC) USING BTREE,
  CONSTRAINT `fk_notice_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '系统通知表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of notification
-- ----------------------------

-- ----------------------------
-- Table structure for paper
-- ----------------------------
DROP TABLE IF EXISTS `paper`;
CREATE TABLE `paper`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '内部ID',
  `aminer_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'AMiner 原始论文ID',
  `title` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '论文标题',
  `abstract` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '摘要',
  `keywords` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '关键词（JSON 数组字符串）',
  `authors` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '作者列表（JSON 数组字符串）',
  `venue` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '发表会议/期刊',
  `year` smallint NULL DEFAULT NULL COMMENT '发表年份',
  `citation_count` int NOT NULL DEFAULT 0 COMMENT '被引次数',
  `embedding` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '论文向量 (base64/JSON，可选)',
  `deleted` tinyint(1) NOT NULL DEFAULT 0 COMMENT '逻辑删除',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `aminer_id`(`aminer_id` ASC) USING BTREE,
  INDEX `idx_year`(`year` ASC) USING BTREE,
  INDEX `idx_citation`(`citation_count` ASC) USING BTREE,
  FULLTEXT INDEX `ft_title_abstract`(`title`, `abstract`) COMMENT '全文检索索引'
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '论文表（AMiner 数据）' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of paper
-- ----------------------------
INSERT INTO `paper` VALUES (1, 'aminer_001', 'Playing Atari with Deep Reinforcement Learning', 'We present the first deep learning model to successfully learn control policies directly from high-dimensional sensory input using reinforcement learning.', '[\"RL\",\"DQN\",\"Atari\",\"Deep Learning\"]', '[\"Mnih, V\",\"Kavukcuoglu, K\"]', 'NIPS Workshop', 2013, 12000, NULL, 0, '2026-03-21 22:28:30', '2026-03-21 22:28:30');
INSERT INTO `paper` VALUES (2, 'aminer_002', 'Asynchronous Methods for Deep Reinforcement Learning', 'We propose a conceptually simple and lightweight framework for deep reinforcement learning that uses asynchronous gradient descent.', '[\"A3C\",\"Reinforcement Learning\",\"Asynchronous\"]', '[\"Mnih, V\",\"Badia, A\"]', 'ICML', 2016, 8500, NULL, 0, '2026-03-21 22:28:30', '2026-03-21 22:28:30');
INSERT INTO `paper` VALUES (3, 'aminer_003', 'Proximal Policy Optimization Algorithms', 'We propose a new family of policy gradient methods for reinforcement learning, which alternate between sampling data through interaction with the environment.', '[\"PPO\",\"Policy Gradient\",\"RL\"]', '[\"Schulman, J\",\"Wolski, F\"]', 'arXiv', 2017, 7200, NULL, 0, '2026-03-21 22:28:30', '2026-03-21 22:28:30');
INSERT INTO `paper` VALUES (4, 'aminer_004', 'Attention Is All You Need', 'We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.', '[\"Transformer\",\"Attention\",\"NLP\",\"Sequence Model\"]', '[\"Vaswani, A\",\"Shazeer, N\"]', 'NeurIPS', 2017, 50000, NULL, 0, '2026-03-21 22:28:30', '2026-03-21 22:28:30');
INSERT INTO `paper` VALUES (5, 'aminer_005', 'BERT: Pre-training of Deep Bidirectional Transformers', 'We introduce a new language representation model called BERT designed to pre-train deep bidirectional representations from unlabeled text.', '[\"BERT\",\"NLP\",\"Pre-training\",\"Transformers\"]', '[\"Devlin, J\",\"Chang, M\"]', 'NAACL', 2019, 35000, NULL, 0, '2026-03-21 22:28:30', '2026-03-21 22:28:30');

-- ----------------------------
-- Table structure for post
-- ----------------------------
DROP TABLE IF EXISTS `post`;
CREATE TABLE `post`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '帖子ID',
  `user_id` bigint NOT NULL COMMENT '发帖用户ID',
  `paper_id` bigint NULL DEFAULT NULL COMMENT '关联论文ID（可选）',
  `title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '帖子标题',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '帖子内容',
  `like_count` int NOT NULL DEFAULT 0 COMMENT '点赞数',
  `reply_count` int NOT NULL DEFAULT 0 COMMENT '回复数',
  `status` tinyint NOT NULL DEFAULT 0 COMMENT '帖子状态: 0=待审核 1=已发布 2=已驳回',
  `review_comment` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '审核备注',
  `reviewed_by` bigint NULL DEFAULT NULL COMMENT '审核管理员ID',
  `reviewed_time` datetime NULL DEFAULT NULL COMMENT '审核时间',
  `deleted` tinyint(1) NOT NULL DEFAULT 0 COMMENT '逻辑删除',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_create_time`(`create_time` ASC) USING BTREE,
  CONSTRAINT `fk_post_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '社区帖子表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of post
-- ----------------------------

-- ----------------------------
-- Table structure for private_messages
-- ----------------------------
DROP TABLE IF EXISTS `private_messages`;
CREATE TABLE `private_messages`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '私信ID',
  `sender_id` bigint NOT NULL COMMENT '发送者ID',
  `receiver_id` bigint NOT NULL COMMENT '接收者ID',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '消息内容',
  `msg_type` tinyint NOT NULL DEFAULT 1 COMMENT '消息类型: 1=文本 2=图片 3=链接',
  `is_read` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否已读: 0=未读 1=已读',
  `read_time` datetime NULL DEFAULT NULL COMMENT '阅读时间',
  `status` tinyint NOT NULL DEFAULT 1 COMMENT '状态: 0=已撤回 1=正常',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_sender`(`sender_id` ASC) USING BTREE,
  INDEX `idx_receiver`(`receiver_id` ASC) USING BTREE,
  INDEX `idx_conversation`(`sender_id` ASC, `receiver_id` ASC, `create_time` ASC) USING BTREE,
  CONSTRAINT `fk_msg_receiver` FOREIGN KEY (`receiver_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_msg_sender` FOREIGN KEY (`sender_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户私信表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of private_messages
-- ----------------------------

-- ----------------------------
-- Table structure for rl_training_log
-- ----------------------------
DROP TABLE IF EXISTS `rl_training_log`;
CREATE TABLE `rl_training_log`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '训练记录ID',
  `episode` int NOT NULL COMMENT '训练轮次',
  `user_id` bigint NOT NULL COMMENT '目标用户ID',
  `state` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '状态表示(用户当前兴趣向量)',
  `action` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '动作(推荐的论文ID列表)',
  `reward` double NOT NULL COMMENT '获得的奖励值',
  `cumulative_reward` double NULL DEFAULT NULL COMMENT '累积奖励',
  `loss` double NULL DEFAULT NULL COMMENT '模型损失',
  `model_version` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '模型版本',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_episode`(`episode` ASC) USING BTREE,
  INDEX `idx_user`(`user_id` ASC) USING BTREE,
  INDEX `idx_time`(`create_time` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '强化学习训练日志表(用于模型优化)' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of rl_training_log
-- ----------------------------

-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户名',
  `password` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'BCrypt 加密密码',
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '邮箱',
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'STUDENT' COMMENT '角色: STUDENT / RESEARCHER / ADMIN',
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '头像 URL',
  `bio` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '个人简介',
  `research_interests` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '研究方向（逗号分隔）',
  `deleted` tinyint(1) NOT NULL DEFAULT 0 COMMENT '逻辑删除: 0=正常 1=删除',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE,
  INDEX `idx_username`(`username` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '用户表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of user
-- ----------------------------
INSERT INTO `user` VALUES (1, 'admin', '$2a$10$lqOCFA3Qd6/XWEmhkv0LjeKhTTc3H4k7ffiCUVpUIqnUGjJ9iyUSm', 'admin@research.com', 'ADMIN', NULL, NULL, 'Machine Learning,Reinforcement Learning', 0, '2026-03-21 22:28:30', '2026-03-21 22:56:01');
INSERT INTO `user` VALUES (2, 'test_user', '$2a$10$lqOCFA3Qd6/XWEmhkv0LjeKhTTc3H4k7ffiCUVpUIqnUGjJ9iyUSm', 'test@research.com', 'RESEARCHER', NULL, NULL, 'NLP,Graph Neural Networks', 0, '2026-03-21 22:28:30', '2026-03-21 22:56:01');
INSERT INTO `user` VALUES (3, 'xixihaha', '$2a$10$lqOCFA3Qd6/XWEmhkv0LjeKhTTc3H4k7ffiCUVpUIqnUGjJ9iyUSm', NULL, 'STUDENT', NULL, NULL, NULL, 0, '2026-03-21 22:54:42', '2026-03-21 22:54:42');

-- ----------------------------
-- Table structure for user_contacts
-- ----------------------------
DROP TABLE IF EXISTS `user_contacts`;
CREATE TABLE `user_contacts`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '关系ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `contact_id` bigint NOT NULL COMMENT '联系人ID(被关注者)',
  `relation_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'FOLLOW' COMMENT '关系类型: FOLLOW=关注 FRIEND=好友 COLLABORATOR=合作者',
  `remark` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '备注名',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_contact`(`user_id` ASC, `contact_id` ASC) USING BTREE,
  INDEX `idx_contact`(`contact_id` ASC) USING BTREE,
  CONSTRAINT `fk_contact_friend` FOREIGN KEY (`contact_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_contact_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户联系人/关注表(用于社交关系网络)' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of user_contacts
-- ----------------------------

-- ----------------------------
-- Table structure for user_interest_history
-- ----------------------------
DROP TABLE IF EXISTS `user_interest_history`;
CREATE TABLE `user_interest_history`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `interest_tag` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '兴趣标签(研究方向)',
  `weight` double NOT NULL DEFAULT 1 COMMENT '兴趣权重(0-1)',
  `source` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '来源: register=注册 behavior=行为 feedback=反馈',
  `record_date` date NOT NULL COMMENT '记录日期',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_user_date`(`user_id` ASC, `record_date` ASC) USING BTREE,
  INDEX `idx_user_tag`(`user_id` ASC, `interest_tag` ASC) USING BTREE,
  CONSTRAINT `fk_interest_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户兴趣演化历史表(用于可视化兴趣变化趋势)' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of user_interest_history
-- ----------------------------

SET FOREIGN_KEY_CHECKS = 1;
