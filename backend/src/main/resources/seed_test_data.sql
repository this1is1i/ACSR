-- ============================================================
-- 测试数据填充脚本（用户已存在，使用实际 ID: 5-9）
-- ============================================================

-- ═══ 用户兴趣历史（新用户 5-9）════════════════════════════
INSERT INTO `user_interest_history` (`user_id`, `interest_tag`, `weight`, `source`, `record_date`) VALUES
(5, 'Reinforcement Learning', 0.90, 'registration', '2026-04-01'),
(5, 'Knowledge Graph', 0.80, 'behavior', '2026-04-15'),
(5, 'Graph Neural Networks', 0.70, 'behavior', '2026-04-20'),
(6, 'NLP', 0.85, 'registration', '2026-04-05'),
(6, 'Deep Learning', 0.75, 'behavior', '2026-04-18'),
(6, 'Transformer', 0.65, 'behavior', '2026-04-25'),
(7, 'Computer Vision', 0.88, 'registration', '2026-04-10'),
(7, 'Federated Learning', 0.72, 'behavior', '2026-04-22'),
(8, 'Recommender Systems', 0.92, 'registration', '2026-04-12'),
(8, 'User Modeling', 0.68, 'behavior', '2026-04-28'),
(9, 'Multi-modal Learning', 0.86, 'registration', '2026-04-08'),
(9, 'Knowledge Distillation', 0.74, 'behavior', '2026-05-01');

-- ═══ 行为日志 ═══════════════════════════════════════════════
INSERT INTO `behavior_log` (`user_id`, `paper_id`, `action`, `duration`, `source`, `timestamp`) VALUES
(1, 1, 'read', 360, 'recommend', '2026-05-01 09:30:00'),
(1, 1, 'favorite', NULL, 'detail', '2026-05-01 09:36:00'),
(1, 2, 'click', NULL, 'recommend', '2026-05-02 10:15:00'),
(1, 3, 'read', 480, 'search', '2026-05-03 14:20:00'),
(1, 4, 'click', NULL, 'recommend', '2026-05-04 08:45:00'),
(1, 5, 'favorite', NULL, 'search', '2026-05-04 16:00:00'),
(2, 4, 'read', 600, 'recommend', '2026-05-01 11:00:00'),
(2, 5, 'read', 320, 'search', '2026-05-02 15:30:00'),
(2, 110, 'click', NULL, 'recommend', '2026-05-03 09:10:00'),
(2, 145, 'favorite', NULL, 'detail', '2026-05-04 13:25:00'),
(3, 351, 'click', NULL, 'search', '2026-05-02 16:40:00'),
(3, 110, 'read', 280, 'recommend', '2026-05-03 11:55:00'),
(5, 145, 'read', 520, 'recommend', '2026-05-05 09:00:00'),
(5, 145, 'favorite', NULL, 'detail', '2026-05-05 09:10:00'),
(5, 351, 'click', NULL, 'search', '2026-05-06 14:30:00'),
(5, 617, 'read', 400, 'recommend', '2026-05-07 10:00:00'),
(6, 351, 'click', NULL, 'search', '2026-05-05 08:20:00'),
(6, 617, 'read', 350, 'recommend', '2026-05-06 13:15:00'),
(6, 697, 'click', NULL, 'search', '2026-05-07 15:45:00'),
(7, 617, 'click', NULL, 'recommend', '2026-05-05 10:30:00'),
(7, 697, 'read', 300, 'search', '2026-05-06 11:00:00'),
(7, 145, 'click', NULL, 'recommend', '2026-05-08 09:20:00'),
(8, 1, 'read', 450, 'recommend', '2026-05-06 08:00:00'),
(8, 2, 'click', NULL, 'search', '2026-05-07 16:30:00'),
(8, 3, 'favorite', NULL, 'detail', '2026-05-08 11:15:00'),
(9, 4, 'read', 380, 'search', '2026-05-07 10:45:00'),
(9, 5, 'click', NULL, 'recommend', '2026-05-08 14:00:00');

-- ═══ 浏览历史 ══════════════════════════════════════════════
INSERT INTO `browse_history` (`user_id`, `paper_id`, `stay_duration`, `browse_date`) VALUES
(1, 2, 180, '2026-05-03'), (1, 3, 240, '2026-05-04'),
(1, 5, 120, '2026-05-05'), (1, 110, 90, '2026-05-06'),
(2, 1, 200, '2026-05-02'), (2, 145, 300, '2026-05-04'),
(2, 351, 150, '2026-05-05'), (2, 697, 100, '2026-05-07'),
(5, 617, 260, '2026-05-06'), (5, 351, 180, '2026-05-08'),
(6, 110, 120, '2026-05-05'), (6, 145, 190, '2026-05-07'),
(7, 4, 160, '2026-05-06'), (7, 5, 140, '2026-05-08'),
(8, 1, 220, '2026-05-07'), (9, 4, 170, '2026-05-08');

-- ═══ 收藏 ══════════════════════════════════════════════════
INSERT INTO `favourite` (`user_id`, `paper_id`, `remark`) VALUES
(1, 1, 'RL classic must-read'),
(1, 5, 'BERT milestone paper'),
(2, 4, 'Transformer origin paper'),
(2, 145, 'KG + recommendation survey'),
(5, 145, 'Foundational literature for my research'),
(5, 617, 'Federated learning survey'),
(8, 1, 'RL classic reading'),
(8, 3, 'PPO algorithm paper'),
(9, 4, 'Multi-modal research reference'),
(3, 351, 'NLP intro reference');

-- ═══ 社区板块 ══════════════════════════════════════════════
INSERT INTO `board` (`name`, `description`, `sort_order`, `post_count`) VALUES
('Paper Discussion', 'Discuss latest papers and share reading notes', 1, 0),
('Tech Q&A', 'Technical questions during research', 2, 0);

-- ═══ 社区帖子 ══════════════════════════════════════════════
INSERT INTO `post` (`user_id`, `paper_id`, `title`, `content`, `status`, `create_time`) VALUES
(5, 145, 'Recent advances in KG-enhanced recommendation',
 'Recent papers show that combining KG embeddings with collaborative filtering significantly improves cold-start recommendation performance. Anyone has experience in this area?',
 1, '2026-05-05 10:00:00'),
(6, 4, 'Transformer beyond NLP: application thoughts',
 'Attention mechanism has revolutionized not only NLP but also CV, speech, and recommendation. I am exploring multi-head attention for user behavior sequence modeling. Welcome to discuss.',
 1, '2026-05-06 14:30:00'),
(7, 617, 'Privacy-preserving federated learning: balancing accuracy',
 'A core challenge in federated learning: how to protect user privacy while maintaining model accuracy? Differential privacy and homomorphic encryption each have trade-offs.',
 1, '2026-05-07 09:15:00'),
(8, 1, 'RL beginner learning path recommendations',
 'As a newcomer to RL, I started with the classic Sutton textbook combined with OpenAI Gym practice. Playing Atari with DRL is a great starting point, recommended to fellow beginners.',
 1, '2026-05-08 11:00:00'),
(2, NULL, 'Academic writing tools collection',
 'I compiled my commonly used academic writing tools: Zotero for reference management, Overleaf for online LaTeX, Grammarly for grammar checking, Connected Papers for exploring related papers. Any other recommendations?',
 1, '2026-04-28 16:20:00');

-- ═══ 评论 ══════════════════════════════════════════════════
INSERT INTO `comment` (`post_id`, `user_id`, `parent_id`, `content`, `create_time`) VALUES
(6, 1, NULL, 'Great survey! Recent work on GNN + recommendation is also a hot direction.', '2026-05-05 11:00:00'),
(6, 2, NULL, 'Any open-source dataset recommendations for KG+RS experiments?', '2026-05-05 13:20:00'),
(6, 5, 2, 'Try MovieLens-1M with Freebase for KG construction, or Amazon Reviews dataset.', '2026-05-05 14:50:00'),
(7, 9, NULL, 'Transformer in CV has many interesting works, recommend DETR and ViT papers.', '2026-05-06 16:00:00'),
(7, 7, NULL, 'Are there lightweight Transformer implementations for quick experiments?', '2026-05-06 17:30:00'),
(7, 1, 5, 'Use HuggingFace Transformers library, one line to load pretrained models. Also try TinyBERT and DistilBERT.', '2026-05-07 08:45:00'),
(8, 2, NULL, 'Non-IID data distribution in federated learning is one of the biggest practical challenges.', '2026-05-07 10:00:00'),
(8, 8, NULL, 'I used Flower framework in my experiments, supports multiple FL algorithms, highly recommended.', '2026-05-07 14:00:00'),
(9, 2, NULL, 'The classic Sutton & Barto book is indeed the best introduction to RL.', '2026-05-08 12:30:00'),
(9, 9, NULL, 'Also recommend Andrej Karpathy''s blog "Pong from Pixels" - 130 lines to understand Policy Gradient.', '2026-05-08 15:00:00');

-- ═══ 联系人关系 ═══════════════════════════════════════════
INSERT INTO `user_contacts` (`user_id`, `contact_id`, `relation_type`, `remark`) VALUES
(1, 2, 'COLLABORATOR', 'collaborator'),
(1, 8, 'MENTOR', 'advisor'),
(2, 1, 'COLLABORATOR', 'collaborator'),
(2, 5, 'COLLABORATOR', 'collaborator'),
(5, 1, 'COLLABORATOR', 'peer'),
(5, 2, 'COLLABORATOR', 'peer'),
(6, 7, 'CLASSMATE', 'classmate'),
(7, 6, 'CLASSMATE', 'classmate'),
(8, 9, 'COLLEAGUE', 'colleague'),
(9, 8, 'COLLEAGUE', 'colleague');

-- ═══ 私信 ══════════════════════════════════════════════════
INSERT INTO `private_messages` (`sender_id`, `receiver_id`, `content`, `create_time`) VALUES
(1, 2, 'Hi, recently saw a paper on Graphormer, very relevant to your research direction.', '2026-05-04 09:00:00'),
(2, 1, 'Thanks! I am preparing a Transformer+KG survey paper.', '2026-05-04 09:15:00'),
(1, 2, 'Great, need any help with review?', '2026-05-04 09:20:00'),
(5, 2, 'Are you presenting the KG progress update at next group meeting?', '2026-05-05 14:00:00'),
(2, 5, 'Sure, I will prepare slides focusing on KG embedding and GNN integration.', '2026-05-05 14:30:00'),
(6, 7, 'Want to go to the library this weekend? Found some good CV papers.', '2026-05-06 10:00:00'),
(7, 6, 'Sounds good! I have been looking at DETR-related papers, can discuss together.', '2026-05-06 10:10:00'),
(8, 1, 'Professor, I have some questions about the experimental design for the recommendation system.', '2026-05-07 08:30:00'),
(1, 8, 'No problem, come to my office at 3pm and we can discuss in person.', '2026-05-07 08:35:00'),
(9, 8, 'Chen, can you share your experience in multi-modal learning? Our group is also focusing on this.', '2026-05-08 11:00:00');

-- ═══ 通知 ══════════════════════════════════════════════════
INSERT INTO `notification` (`user_id`, `type`, `title`, `content`) VALUES
(1, 'SYSTEM', 'Recommendation model update', 'Actor-Critic model has completed a new round of training with improved accuracy'),
(2, 'COMMENT', 'Someone replied to your comment', 'researcher_li replied to your comment on the KG + recommendation post'),
(5, 'LIKE', 'Your post received new likes', 'Your post on KG-enhanced recommendation received 5 new likes'),
(6, 'SYSTEM', 'Research interest recommendation update', 'Based on your recent reading behavior, we recommend new papers on Transformer'),
(8, 'MENTION', 'Someone mentioned you', 'alice_prof mentioned your work in a post');

-- ═══ 训练日志 ══════════════════════════════════════════════
INSERT INTO `rl_training_log` (`episode`, `user_id`, `reward`, `cumulative_reward`, `loss`, `model_version`) VALUES
(100, 1, 2.35, 185.6, 0.042, 'v1.0'),
(200, 1, 3.12, 392.1, 0.031, 'v1.1'),
(300, 1, 3.48, 521.7, 0.025, 'v1.2'),
(400, 1, 3.89, 668.3, 0.019, 'v1.3'),
(500, 1, 4.15, 803.5, 0.015, 'v1.4');

-- ═══ 用户特征快照 ══════════════════════════════════════════
INSERT INTO `user_feature_snapshot` (`user_id`, `feature_type`, `feature_vector`, `feature_dim`) VALUES
(1, 'interest', '[0.85, 0.72, 0.31, 0.08, 0.15, 0.22, 0.41, 0.03]', 64),
(1, 'history',  '[0.42, 0.63, 0.18, 0.91, 0.55, 0.07, 0.33, 0.28]', 64),
(2, 'interest', '[0.12, 0.05, 0.88, 0.73, 0.09, 0.01, 0.56, 0.44]', 64),
(2, 'history',  '[0.33, 0.21, 0.67, 0.45, 0.78, 0.12, 0.19, 0.51]', 64);
