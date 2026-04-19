-- ============================================================
-- 科研推荐系统数据库建表语句
-- 数据库：MySQL 8.0+
-- 字符集：utf8mb4
-- ============================================================

CREATE DATABASE IF NOT EXISTS research_db
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE research_db;

-- ── 用户表 ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `user` (
    `id`          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `username`    VARCHAR(50)  NOT NULL UNIQUE         COMMENT '用户名',
    `password`    VARCHAR(128) NOT NULL                COMMENT 'BCrypt 加密密码',
    `email`       VARCHAR(100)                         COMMENT '邮箱',
    `role`        VARCHAR(20)  NOT NULL DEFAULT 'USER' COMMENT '角色: USER / ADMIN',
    `avatar`      VARCHAR(255)                         COMMENT '头像 URL',
    `bio`         TEXT                                 COMMENT '个人简介',
    `research_interests` VARCHAR(500)                  COMMENT '研究方向（逗号分隔）',
    `deleted`     TINYINT(1)   NOT NULL DEFAULT 0      COMMENT '逻辑删除: 0=正常 1=删除',
    `create_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    `update_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- ── 论文表（来源 AMiner 数据集）──────────────────────────────
CREATE TABLE IF NOT EXISTS `paper` (
    `id`             BIGINT       NOT NULL AUTO_INCREMENT COMMENT '内部ID',
    `aminer_id`      VARCHAR(64)  UNIQUE                  COMMENT 'AMiner 原始论文ID',
    `title`          VARCHAR(500) NOT NULL                COMMENT '论文标题',
    `abstract`       TEXT                                 COMMENT '摘要',
    `keywords`       VARCHAR(500)                         COMMENT '关键词（JSON 数组字符串）',
    `authors`        VARCHAR(500)                         COMMENT '作者列表（JSON 数组字符串）',
    `venue`          VARCHAR(200)                         COMMENT '发表会议/期刊',
    `year`           SMALLINT                             COMMENT '发表年份',
    `citation_count` INT          NOT NULL DEFAULT 0      COMMENT '被引次数',
    `embedding`      TEXT                                 COMMENT '论文向量 (base64/JSON，可选)',
    `deleted`        TINYINT(1)   NOT NULL DEFAULT 0      COMMENT '逻辑删除',
    `create_time`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_year`         (`year`),
    INDEX `idx_citation`     (`citation_count`),
    FULLTEXT INDEX `ft_title_abstract` (`title`, `abstract`) COMMENT '全文检索索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='论文表（AMiner 数据）';

-- ── 用户行为日志表 ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `behavior_log` (
    `id`         BIGINT      NOT NULL AUTO_INCREMENT COMMENT '日志ID',
    `user_id`    BIGINT      NOT NULL                COMMENT '用户ID',
    `paper_id`   BIGINT      NOT NULL                COMMENT '论文ID',
    `action`     VARCHAR(20) NOT NULL                COMMENT '行为类型: click/favorite/read',
    `duration`   INT                                 COMMENT '阅读时长（秒，action=read 时有值）',
    `source`     VARCHAR(50)                         COMMENT '来源页面: recommend/search/detail',
    `timestamp`  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '行为发生时间',
    PRIMARY KEY (`id`),
    INDEX `idx_user_id`    (`user_id`),
    INDEX `idx_paper_id`   (`paper_id`),
    INDEX `idx_timestamp`  (`timestamp`),
    INDEX `idx_user_action`(`user_id`, `action`),
    CONSTRAINT `fk_behavior_user`  FOREIGN KEY (`user_id`)  REFERENCES `user`(`id`),
    CONSTRAINT `fk_behavior_paper` FOREIGN KEY (`paper_id`) REFERENCES `paper`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户行为日志表（RL 训练数据）';

-- ── 社区帖子表 ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `post` (
    `id`          BIGINT   NOT NULL AUTO_INCREMENT COMMENT '帖子ID',
    `user_id`     BIGINT   NOT NULL                COMMENT '发帖用户ID',
    `paper_id`    BIGINT                           COMMENT '关联论文ID（可选）',
    `title`       VARCHAR(200)                     COMMENT '帖子标题',
    `content`     TEXT     NOT NULL                COMMENT '帖子内容',
    `like_count`  INT      NOT NULL DEFAULT 0      COMMENT '点赞数',
    `reply_count` INT      NOT NULL DEFAULT 0      COMMENT '回复数',
    `deleted`     TINYINT(1) NOT NULL DEFAULT 0    COMMENT '逻辑删除',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_user_id`   (`user_id`),
    INDEX `idx_create_time`(`create_time`),
    CONSTRAINT `fk_post_user` FOREIGN KEY (`user_id`) REFERENCES `user`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='社区帖子表';

-- ── 推荐记录表（记录每次推荐结果，用于效果追踪）────────────
CREATE TABLE IF NOT EXISTS `recommendation_log` (
    `id`         BIGINT       NOT NULL AUTO_INCREMENT,
    `user_id`    BIGINT       NOT NULL                COMMENT '用户ID',
    `paper_id`   BIGINT       NOT NULL                COMMENT '被推荐论文ID',
    `score`      DOUBLE                               COMMENT '推荐分数',
    `reason`     VARCHAR(500)                         COMMENT '推荐理由',
    `rank`       INT                                  COMMENT '推荐排名',
    `clicked`    TINYINT(1)   NOT NULL DEFAULT 0      COMMENT '用户是否点击',
    `create_time`DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_user_id`    (`user_id`),
    INDEX `idx_create_time`(`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='推荐记录表';

-- ── 初始测试数据 ──────────────────────────────────────────────
-- 管理员账号 admin / admin123（BCrypt 加密）
INSERT INTO `user` (`username`, `password`, `email`, `role`, `research_interests`) VALUES
('admin', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iAt6Z5EH', 'admin@research.com', 'ADMIN', 'Machine Learning,Reinforcement Learning'),
('test_user', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iAt6Z5EH', 'test@research.com', 'USER', 'NLP,Graph Neural Networks');

-- 示例论文数据
INSERT INTO `paper` (`aminer_id`, `title`, `abstract`, `keywords`, `authors`, `venue`, `year`, `citation_count`) VALUES
('aminer_001', 'Playing Atari with Deep Reinforcement Learning', 'We present the first deep learning model to successfully learn control policies directly from high-dimensional sensory input using reinforcement learning.', '["RL","DQN","Atari","Deep Learning"]', '["Mnih, V","Kavukcuoglu, K"]', 'NIPS Workshop', 2013, 12000),
('aminer_002', 'Asynchronous Methods for Deep Reinforcement Learning', 'We propose a conceptually simple and lightweight framework for deep reinforcement learning that uses asynchronous gradient descent.', '["A3C","Reinforcement Learning","Asynchronous"]', '["Mnih, V","Badia, A"]', 'ICML', 2016, 8500),
('aminer_003', 'Proximal Policy Optimization Algorithms', 'We propose a new family of policy gradient methods for reinforcement learning, which alternate between sampling data through interaction with the environment.', '["PPO","Policy Gradient","RL"]', '["Schulman, J","Wolski, F"]', 'arXiv', 2017, 7200),
('aminer_004', 'Attention Is All You Need', 'We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.', '["Transformer","Attention","NLP","Sequence Model"]', '["Vaswani, A","Shazeer, N"]', 'NeurIPS', 2017, 50000),
('aminer_005', 'BERT: Pre-training of Deep Bidirectional Transformers', 'We introduce a new language representation model called BERT designed to pre-train deep bidirectional representations from unlabeled text.', '["BERT","NLP","Pre-training","Transformers"]', '["Devlin, J","Chang, M"]', 'NAACL', 2019, 35000);
