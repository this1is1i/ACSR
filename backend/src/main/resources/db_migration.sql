-- ============================================================
-- 数据库整改 SQL 脚本
-- 请由 DBA / 开发者在 MySQL 终端执行
-- 执行前建议备份 research_db 数据库
-- ============================================================

USE research_db;

-- ── 任务 3: 添加外键约束 ────────────────────────────────────

-- rl_training_log.user_id → user.id（允许 NULL，系统级训练不关联用户）
ALTER TABLE rl_training_log
    MODIFY COLUMN user_id bigint NULL COMMENT '目标用户ID（系统训练时为NULL）';

ALTER TABLE rl_training_log
    ADD CONSTRAINT fk_train_user
    FOREIGN KEY (user_id) REFERENCES `user`(id)
    ON DELETE SET NULL ON UPDATE RESTRICT;

-- post.reviewed_by → user.id（可为 NULL，删除管理员时置空）
ALTER TABLE post
    ADD CONSTRAINT fk_reviewed_by
    FOREIGN KEY (reviewed_by) REFERENCES `user`(id)
    ON DELETE SET NULL ON UPDATE RESTRICT;

-- ── 任务 2: 删除 post 表冗余计数器 ───────────────────────────

ALTER TABLE post DROP COLUMN like_count;
ALTER TABLE post DROP COLUMN reply_count;

-- ── 验证 ────────────────────────────────────────────────────
SELECT 'SQL 执行完成，请检查下方是否有错误信息' AS status;
