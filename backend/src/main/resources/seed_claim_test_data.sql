-- ============================================================
-- 作者认领功能测试数据（基于 Neo4j 真实作者-论文关系）
-- 密码: 123456 (BCrypt)
-- 执行前确认: user 表 AUTO_INCREMENT=10, paper 表有 ID 1-5
-- ============================================================

-- ═══ 新建用户（与论文作者同名，用于认领匹配）═══════════════
INSERT INTO `user` (`username`, `password`, `email`, `role`, `research_interests`) VALUES
('Mnih, V',      '$2b$12$QjZY15zfJqurPwAFirPpw.Q/fSyqgpeqinc5sRoJQqJSYk4leujxe', 'mnih@test.edu',   'RESEARCHER', 'Reinforcement Learning, Deep Learning'),
('Vaswani, A',   '$2b$12$QjZY15zfJqurPwAFirPpw.Q/fSyqgpeqinc5sRoJQqJSYk4leujxe', 'vaswani@test.edu', 'RESEARCHER', 'Attention Mechanism, NLP, Transformer'),
('Devlin, J',    '$2b$12$QjZY15zfJqurPwAFirPpw.Q/fSyqgpeqinc5sRoJQqJSYk4leujxe', 'devlin@test.edu',  'RESEARCHER', 'NLP, BERT, Pre-training'),
('Schulman, J',  '$2b$12$QjZY15zfJqurPwAFirPpw.Q/fSyqgpeqinc5sRoJQqJSYk4leujxe', 'schulman@test.edu','RESEARCHER', 'Reinforcement Learning, Policy Optimization'),
('Shazeer, N',   '$2b$12$QjZY15zfJqurPwAFirPpw.Q/fSyqgpeqinc5sRoJQqJSYk4leujxe', 'shazeer@test.edu', 'RESEARCHER', 'Attention Mechanism, Sparse Models'),
('Badia, A',     '$2b$12$QjZY15zfJqurPwAFirPpw.Q/fSyqgpeqinc5sRoJQqJSYk4leujxe', 'badia@test.edu',   'RESEARCHER', 'Reinforcement Learning, Async Methods');

-- ═══ 作者认领记录 ═══════════════════════════════════════════
-- paper 1: Playing Atari with Deep Reinforcement Learning
-- paper 2: Asynchronous Methods for Deep RL
-- paper 3: Proximal Policy Optimization Algorithms
-- paper 4: Attention Is All You Need
-- paper 5: BERT: Pre-training of Deep Bidirectional Transformers

INSERT INTO `paper_author_claim` (`paper_id`, `user_id`, `author_name`, `match_method`, `confidence`, `status`, `responded_at`, `create_time`) VALUES

-- ── 待确认 (status=0) ──
(1, 10, 'Mnih, V',      'exact', 1.00, 0, NULL, '2026-05-23 10:00:00'),
(2, 10, 'Mnih, V',      'exact', 1.00, 0, NULL, '2026-05-23 10:05:00'),
(3, 13, 'Schulman, J',  'exact', 1.00, 0, NULL, '2026-05-23 11:00:00'),
(4, 11, 'Vaswani, A',   'exact', 1.00, 0, NULL, '2026-05-24 08:30:00'),

-- ── 已确认 (status=1) ──
(1, 15, 'Badia, A',     'fuzzy', 0.78, 1, '2026-05-22 14:00:00', '2026-05-20 09:00:00'),
(4, 14, 'Shazeer, N',   'exact', 1.00, 1, '2026-05-23 16:30:00', '2026-05-20 10:00:00'),
(5, 12, 'Devlin, J',    'exact', 1.00, 1, '2026-05-24 09:00:00', '2026-05-21 08:00:00'),

-- ── 已否认 (status=2) ──
(5, 11, 'Vaswani, A',   'fuzzy', 0.50, 2, '2026-05-24 10:00:00', '2026-05-22 12:00:00');
