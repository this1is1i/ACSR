-- ============================================================
-- Seed data for knowledge graph & visualization
-- Run after research_db.sql to populate kg_entity, kg_relation,
-- user_interest_history, and browse_history from existing data.
-- Safe to re-run: uses INSERT IGNORE throughout.
-- ============================================================

-- Step 1: Insert unique keywords from papers into kg_entity
INSERT IGNORE INTO kg_entity (name, type, properties, create_time)
SELECT DISTINCT jt.keyword, 'KEYWORD', '{}', NOW()
FROM paper,
JSON_TABLE(
    CAST(keywords AS JSON),
    '$[*]' COLUMNS (keyword VARCHAR(100) COLLATE utf8mb4_unicode_ci PATH '$')
) AS jt
WHERE deleted = 0
  AND keywords IS NOT NULL
  AND keywords != ''
  AND JSON_VALID(keywords);

-- Step 2: Insert papers into kg_entity (type=PAPER)
INSERT IGNORE INTO kg_entity (name, type, external_id, properties, create_time)
SELECT title, 'PAPER', aminer_id,
       JSON_OBJECT('year', COALESCE(year, 0),
                   'citation_count', citation_count,
                   'venue', COALESCE(venue, '')),
       NOW()
FROM paper
WHERE deleted = 0;

-- Step 3: Create keyword-paper relations (PAPER RELATED_TO KEYWORD)
INSERT IGNORE INTO kg_relation (source_id, target_id, relation_type, weight, create_time)
SELECT pe.id, ke.id, 'RELATED_TO', 1.0, NOW()
FROM paper p
JOIN kg_entity pe ON pe.external_id COLLATE utf8mb4_0900_ai_ci = p.aminer_id AND pe.type = 'PAPER',
JSON_TABLE(
    CAST(p.keywords AS JSON),
    '$[*]' COLUMNS (keyword VARCHAR(100) COLLATE utf8mb4_unicode_ci PATH '$')
) AS jt
JOIN kg_entity ke ON ke.name = jt.keyword AND ke.type = 'KEYWORD'
WHERE p.deleted = 0
  AND p.keywords IS NOT NULL
  AND p.keywords != ''
  AND JSON_VALID(p.keywords);

-- Step 4: Create keyword co-occurrence relations (KEYWORD RELATED_TO KEYWORD)
INSERT IGNORE INTO kg_relation (source_id, target_id, relation_type, weight, create_time)
SELECT e1.id, e2.id, 'RELATED_TO', LEAST(1.0, t.co_count / 10.0), NOW()
FROM (
    SELECT k1.keyword AS kw1, k2.keyword AS kw2, COUNT(*) AS co_count
    FROM paper p,
    JSON_TABLE(CAST(p.keywords AS JSON), '$[*]' COLUMNS (keyword VARCHAR(100) COLLATE utf8mb4_unicode_ci PATH '$')) AS k1,
    JSON_TABLE(CAST(p.keywords AS JSON), '$[*]' COLUMNS (keyword VARCHAR(100) COLLATE utf8mb4_unicode_ci PATH '$')) AS k2
    WHERE p.deleted = 0
      AND p.keywords IS NOT NULL AND JSON_VALID(p.keywords)
      AND k1.keyword < k2.keyword
    GROUP BY k1.keyword, k2.keyword
) t
JOIN kg_entity e1 ON e1.name = t.kw1 AND e1.type = 'KEYWORD'
JOIN kg_entity e2 ON e2.name = t.kw2 AND e2.type = 'KEYWORD';

-- Step 5: Generate user_interest_history from user.research_interests
-- For each user, split research_interests by comma, create 12 monthly records
INSERT IGNORE INTO user_interest_history (user_id, interest_tag, weight, source, record_date, create_time)
SELECT u.id,
       TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(u.research_interests, ',', n.num), ',', -1)) AS interest_tag,
       ROUND(0.5 + (RAND(n.num) * 0.5), 2) AS weight,
       'register' AS source,
       DATE_SUB(CURRENT_DATE, INTERVAL (12 - m.month_num) MONTH) AS record_date,
       NOW()
FROM user u
CROSS JOIN (
    SELECT 1 AS num UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL
    SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8
) n
CROSS JOIN (
    SELECT 1 AS month_num UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL
    SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL
    SELECT 9 UNION ALL SELECT 10 UNION ALL SELECT 11 UNION ALL SELECT 12
) m
WHERE u.research_interests IS NOT NULL
  AND u.research_interests != ''
  AND u.deleted = 0
  AND TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(u.research_interests, ',', n.num), ',', -1)) != ''
  AND n.num <= (LENGTH(u.research_interests) - LENGTH(REPLACE(u.research_interests, ',', '')) + 1);

-- Step 6: Generate browse_history from behavior_log
INSERT IGNORE INTO browse_history (user_id, paper_id, stay_duration, browse_date, create_time)
SELECT user_id, paper_id,
       COALESCE(MAX(duration), 0) AS stay_duration,
       DATE(timestamp) AS browse_date,
       NOW()
FROM behavior_log
GROUP BY user_id, paper_id, DATE(timestamp);
