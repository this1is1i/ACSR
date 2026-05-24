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

 Date: 24/05/2026 18:47:17
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

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
) ENGINE = InnoDB AUTO_INCREMENT = 186 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '用户行为日志表（RL 训练数据）' ROW_FORMAT = DYNAMIC;

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
) ENGINE = InnoDB AUTO_INCREMENT = 30 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '帖子评论/回复表' ROW_FORMAT = DYNAMIC;

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
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户论文收藏表' ROW_FORMAT = DYNAMIC;

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
) ENGINE = InnoDB AUTO_INCREMENT = 3016 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '论文表（AMiner 数据）' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for paper_author_claim
-- ----------------------------
DROP TABLE IF EXISTS `paper_author_claim`;
CREATE TABLE `paper_author_claim`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '认领记录ID',
  `paper_id` bigint NOT NULL COMMENT '论文ID',
  `user_id` bigint NOT NULL COMMENT '被匹配的用户ID',
  `author_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '论文中匹配到的原始作者名',
  `match_method` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'exact' COMMENT '匹配方式: exact/fuzzy/manual',
  `confidence` decimal(3, 2) NULL DEFAULT NULL COMMENT '匹配置信度 0.00~1.00',
  `status` tinyint NOT NULL DEFAULT 0 COMMENT '认领状态: 0=待确认 1=已确认为本人 2=已否认 3=已过期',
  `responded_at` datetime NULL DEFAULT NULL COMMENT '用户响应时间',
  `admin_note` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '管理员备注',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_paper_user`(`paper_id` ASC, `user_id` ASC) USING BTREE,
  INDEX `idx_user_status`(`user_id` ASC, `status` ASC) USING BTREE,
  INDEX `idx_paper_id`(`paper_id` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  CONSTRAINT `fk_claim_paper` FOREIGN KEY (`paper_id`) REFERENCES `paper` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_claim_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '论文作者认领表（用户确认论文是否为其著作）' ROW_FORMAT = Dynamic;

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
) ENGINE = InnoDB AUTO_INCREMENT = 16 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '社区帖子表' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for post_like
-- ----------------------------
DROP TABLE IF EXISTS `post_like`;
CREATE TABLE `post_like`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `post_id` bigint NOT NULL,
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_post`(`user_id` ASC, `post_id` ASC) USING BTREE,
  INDEX `idx_post_id`(`post_id` ASC) USING BTREE,
  CONSTRAINT `post_like_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `post_like_ibfk_2` FOREIGN KEY (`post_id`) REFERENCES `post` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 23 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '帖子点赞表' ROW_FORMAT = Dynamic;

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
) ENGINE = InnoDB AUTO_INCREMENT = 31 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户私信表' ROW_FORMAT = DYNAMIC;

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
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '强化学习训练日志表(用于模型优化)' ROW_FORMAT = DYNAMIC;

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
) ENGINE = InnoDB AUTO_INCREMENT = 10 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '用户表' ROW_FORMAT = DYNAMIC;

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
) ENGINE = InnoDB AUTO_INCREMENT = 29 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户联系人/关注表(用于社交关系网络)' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for user_feature_snapshot
-- ----------------------------
DROP TABLE IF EXISTS `user_feature_snapshot`;
CREATE TABLE `user_feature_snapshot`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '快照ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `feature_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '特征类型: interest|history|kg',
  `feature_vector` json NOT NULL COMMENT '特征向量 (float list)',
  `feature_dim` int NOT NULL COMMENT '向量维度',
  `source` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'computed' COMMENT '来源: computed|cached|fallback',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_type`(`user_id` ASC, `feature_type` ASC) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_updated`(`updated_at` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 22 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户RL特征向量缓存表' ROW_FORMAT = Dynamic;

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
) ENGINE = InnoDB AUTO_INCREMENT = 105 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户兴趣演化历史表(用于可视化兴趣变化趋势)' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
