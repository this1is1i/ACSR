-- ============================================================
-- Seed data: community posts, comments, messages, contacts
-- Safe to re-run: uses INSERT IGNORE throughout.
-- ============================================================

-- ── Posts (3-5 sample community posts) ────────────────────────
INSERT IGNORE INTO post (id, user_id, paper_id, title, content, like_count, reply_count, status, create_time, update_time)
VALUES
(1, 2, 4, 'Why Attention Mechanism Changed NLP Forever',
 'I have been studying the Transformer architecture recently and I am amazed at how it reshaped the entire NLP landscape. The self-attention mechanism allows the model to capture long-range dependencies that RNNs could never handle. What do you think is the most impactful application of attention beyond NLP?',
 12, 3, 1, '2026-04-15 09:30:00', '2026-04-15 09:30:00'),

(2, 1, 1, 'Getting Started with Deep Reinforcement Learning',
 'For newcomers to RL, the DQN paper by Mnih et al. is a must-read. It was the first to successfully combine deep learning with reinforcement learning for playing Atari games. I recommend starting here before moving to more advanced methods like PPO or SAC. Happy to discuss!',
 8, 2, 1, '2026-04-10 14:20:00', '2026-04-10 14:20:00'),

(3, 2, 5, 'BERT Fine-Tuning Best Practices',
 'After working with BERT for several downstream tasks, I found that the learning rate and batch size are critical hyperparameters. Too high a learning rate and the pre-trained weights get destroyed. I have compiled some best practices from recent papers — share your experiences too!',
 5, 2, 1, '2026-04-08 11:00:00', '2026-04-08 11:00:00'),

(4, 3, 2, 'A3C vs PPO — Which One Should I Use?',
 'I am a student trying to implement a reinforcement learning project. I have read both the A3C and PPO papers. A3C is asynchronous and works well on CPU, while PPO is simpler and more stable. Which one would you recommend for a beginner project with limited GPU resources?',
 3, 1, 1, '2026-04-20 16:45:00', '2026-04-20 16:45:00'),

(5, 1, 3, 'PPO Implementation Tips and Tricks',
 'I recently implemented PPO from scratch and learned a lot. Key takeaways: 1) the clipping parameter really matters, 2) GAE (Generalized Advantage Estimation) improves stability significantly, 3) normalizing rewards helps a lot. I am sharing my code and notes — feedback welcome!',
 15, 4, 1, '2026-04-18 08:15:00', '2026-04-18 08:15:00');

-- ── Comments (threaded replies on posts) ─────────────────────
INSERT IGNORE INTO comment (id, post_id, user_id, parent_id, root_id, content, like_count, is_best, status, create_time, update_time)
VALUES
-- Comments on post 1 (Why Attention Mechanism Changed NLP)
(1, 1, 3, NULL, NULL, 'Great post! I am just starting to learn about Transformers in my NLP class. Any good beginner resources?', 3, 0, 1, '2026-04-15 10:30:00', '2026-04-15 10:30:00'),
(2, 1, 2, 1, 1, 'I recommend starting with "The Illustrated Transformer" by Jay Alammar — it explains the concepts visually. Then read the original paper.', 5, 1, 1, '2026-04-15 11:00:00', '2026-04-15 11:00:00'),
(3, 1, 1, NULL, NULL, 'Attention has also been huge in computer vision — Vision Transformers (ViT) are now competitive with CNNs. The cross-domain impact is remarkable.', 7, 0, 1, '2026-04-16 09:00:00', '2026-04-16 09:00:00'),

-- Comments on post 2 (Getting Started with Deep RL)
(4, 2, 2, NULL, NULL, 'Totally agree! I also recommend Spinning Up by OpenAI as a practical guide. It has clean implementations of all the major algorithms.', 4, 0, 1, '2026-04-10 15:30:00', '2026-04-10 15:30:00'),
(5, 2, 3, 4, 4, 'Thanks for the suggestion! I will check it out. Do they have Chinese translations?', 1, 0, 1, '2026-04-11 10:00:00', '2026-04-11 10:00:00'),

-- Comments on post 5 (PPO Implementation Tips)
(6, 5, 2, NULL, NULL, 'Point 3 about reward normalization is so important! I wasted a week debugging before realizing my rewards were not scaled properly.', 6, 0, 1, '2026-04-18 10:00:00', '2026-04-18 10:00:00'),
(7, 5, 3, 6, 6, 'Same here! What range do you usually normalize to? I have seen both [-1, 1] and standardization to N(0, 1).', 2, 0, 1, '2026-04-18 12:00:00', '2026-04-18 12:00:00'),
(8, 5, 1, 7, 6, 'I recommend running mean/std normalization (N(0,1)) with a small epsilon to avoid division by zero. Clip to [-10, 10] as a safety measure.', 4, 0, 1, '2026-04-18 14:00:00', '2026-04-18 14:00:00'),

-- Comments on post 3 (BERT Fine-Tuning)
(9, 3, 1, NULL, NULL, 'Great tips! I have also found that using a linear warmup schedule for the first 10% of steps really helps stabilize training.', 3, 0, 1, '2026-04-09 08:00:00', '2026-04-09 08:00:00'),
(10, 3, 2, 9, 9, 'Absolutely! The warmup prevents the model from making drastic updates before it has seen enough of the downstream data distribution.', 2, 0, 1, '2026-04-09 09:30:00', '2026-04-09 09:30:00');

-- ── Contacts (follow relationships between users) ─────────────
INSERT IGNORE INTO user_contacts (id, user_id, contact_id, relation_type, remark, create_time)
VALUES
(1, 1, 2, 'FOLLOW', NULL, '2026-04-01 10:00:00'),
(2, 2, 1, 'FOLLOW', NULL, '2026-04-01 11:00:00'),
(3, 1, 3, 'FOLLOW', NULL, '2026-04-05 09:00:00'),
(4, 3, 2, 'FOLLOW', 'test_user 学长', '2026-04-10 14:00:00'),
(5, 2, 3, 'FOLLOW', NULL, '2026-04-12 16:00:00');

-- ── Private messages (chat history between users) ─────────────
INSERT IGNORE INTO private_messages (id, sender_id, receiver_id, content, msg_type, is_read, read_time, status, create_time)
VALUES
-- Conversation between admin (1) and test_user (2)
(1, 1, 2, 'Hi! I saw your post about Transformers — great analysis! I am working on a similar topic. Would you be interested in collaborating?', 1, true, '2026-04-15 13:00:00', 1, '2026-04-15 12:30:00'),
(2, 2, 1, 'Thanks! Yes, I would love to collaborate. I am currently experimenting with attention mechanisms for knowledge graph reasoning. What area are you focusing on?', 1, true, '2026-04-15 13:05:00', 1, '2026-04-15 13:02:00'),
(3, 1, 2, 'That sounds really interesting! I am exploring how RL can be combined with knowledge graphs for recommendation systems. Maybe we can combine our work — RL + attention for KG-based recommendations?', 1, true, '2026-04-15 13:10:00', 1, '2026-04-15 13:08:00'),
(4, 2, 1, 'That is a great idea! Let me put together some related work and share my notes. I will send you a document by end of week.', 1, false, NULL, 1, '2026-04-15 13:15:00'),

-- Conversation between test_user (2) and xixihaha (3)
(5, 3, 2, 'Hello~ I saw you are a researcher in NLP and GNN. I am a student and would love to learn more about these fields. Do you have any advice?', 1, true, '2026-04-16 10:00:00', 1, '2026-04-16 09:30:00'),
(6, 2, 3, 'Hi xixihaha! Happy to help. I recommend starting with the fundamentals — Andrew Ng''s ML course, then dive into specific papers. Start with something manageable like BERT fine-tuning before tackling GNNs.', 1, true, '2026-04-16 10:05:00', 1, '2026-04-16 10:02:00'),
(7, 3, 2, 'Thank you so much! I just finished the Stanford CS224N course on NLP. Should I move to graph neural networks next or focus more on Transformers?', 1, true, '2026-04-16 11:00:00', 1, '2026-04-16 10:55:00'),
(8, 2, 3, 'I would suggest spending more time on Transformers first — they are the foundation for many modern architectures including Graph Transformers. Once you are comfortable with attention mechanisms, GNNs will be much easier to understand.', 1, false, NULL, 1, '2026-04-16 11:10:00'),

-- Conversation between admin (1) and xixihaha (3)
(9, 1, 3, 'Welcome to the research community! I noticed you joined recently. Let me know if you have any questions about the platform.', 1, true, '2026-04-18 09:00:00', 1, '2026-04-18 08:45:00'),
(10, 3, 1, 'Thank you admin! The platform is really helpful. I am currently exploring the knowledge graph feature — the visualization is amazing!', 1, true, '2026-04-18 09:05:00', 1, '2026-04-18 09:02:00');
