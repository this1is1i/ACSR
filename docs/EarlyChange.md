# 每日变更记录

## 2026-05-08

### 核心目标
消除 Python 推荐服务的"假数据"问题，打通 MySQL + Neo4j 真实数据链路。

### 数据架构变更
- **MySQL**: 删除 `kg_entity` / `kg_relation` 表（与 Neo4j 冗余），新增 `user_feature_snapshot` 表（用户 RL 特征缓存）
- **Neo4j**: 5 类关系齐全（HAS_KEYWORD 4018、AUTHOR_OF 2470、CITE 1993、PUBLISH_IN 1005、CO_AUTHOR 310），1005 Paper 节点
- **数据流**: 用户特征从 MySQL behavior_log 读取，论文池从 Neo4j 加载，KG 嵌入从图结构实时计算

### Python 服务 (`rl-service/`)
| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `data/mysql_data.py` | MySQL 数据访问层，读 behavior_log / user_interest_history |
| 重写 | `features/feature_builder.py` | 从 MySQL 真实数据构建用户向量（兴趣/历史/KG），支持缓存 |
| 修改 | `services/recommendation_service.py` | 注入 MySQLDataSource；KG 初始化支持 Neo4j 三级回退；推荐解释改用 KG 图结构 |
| 修改 | `config.py` | +MySQL 五参数配置段 |
| 新增 | `knowledge_graph/kg_embedder.py` | `create_kg_embedder()` 工厂函数 |
| 修改 | `knowledge_graph/graph_query.py` | 索引构建兼容大小写；修复 explain_recommendation 引用边匹配 |
| 修改 | `knowledge_graph/graph_storage.py` | `_edge_from_row` 统一 relation 小写规范化 |
| 修改 | `api/server.py` | 学习路径端点集成 KnowledgePropagation，返回 color/glowIntensity；训练触发 config 拷贝 |
| 修改 | `train.py` | KG 构建共享 create_kg_embedder |
| 新增 | `utils/text_utils.py` | clean_text / tokenize（从 preprocess.py 提取） |
| 删除 | `recommender/explain.py` | 模板解释被 GraphQuery.explain_recommendation 取代 |
| 删除 | `dataset/preprocess.py` | 有用部分迁移到 text_utils.py |
| 删除 | `dataset_pipeline.py` | 功能已被 RecommendationService 覆盖 |
| 删除 | 9 处空壳接口 | agent/candidate_generator/reward/logger/mock_data |

### Java 后端
| 操作 | 文件 | 说明 |
|------|------|------|
| 重写 | `KnowledgeServiceImpl.java` | 不再读 MySQL kg_entity/kg_relation，改由 Python 提供图谱数据 |
| 修改 | `VisualizationServiceImpl.java` | buildKnowledgeGraph 改为调 Python /learning-path；修复 N+1 查询；buildKeywordFrequencyMap 改用 interest_history |
| 修改 | `PythonRecClient.java` | 新增 LearningPathRequest/Response DTO 和 getLearningPath() 方法 |
| 修改 | `RecommendServiceImpl.java` | 添加诊断日志（pyResp 状态 / reason 预览） |
| 修改 | `KnowledgeController.java` | 节点数据透传 color/glowIntensity |

### Vue 前端
| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `KnowledgeGraph.vue` | 删除本地 masteryColor/masteryHex；3D 渲染改用 pathNodes/pathEdges；修复空数组 fallback |
| 修改 | `utils/path.js` | buildLearningPathSummary 透传 pathNodes |

### 已修复 Bug（按发现顺序）
1. `self._graph_query = None` 在 `_init_kg()` 之后执行 → 覆盖了已初始化的 GraphQuery
2. `train.py` 调用已删除的 `predict_for_api()` → crash
3. `KnowledgeGraph.vue` 空 `[]` 不触发 fallback（JS 中 [] 是 truthy）
4. `path_builder.py` 关键词可能被加上双重 `kw_` 前缀
5. `graph_query.py` edge.relation 大小写不匹配导致索引为空
6. N+1 查询：每条 behavior_log 逐一 selectById → 改为批量 findByIds
7. 全表扫描：`paperMapper.selectList(null)` → 改用 interest_history 聚合
8. mutable 全局 config：`train.py` 和 `server.py` 直接修改 `default_config`
9. `assembleFromPython` 中 paperId 可能为 null

### 当前服务状态
- **启动顺序**: RL service (:8000) → Backend (:8080) → Frontend (:5173)
- **Neo4j**: `bolt://localhost:7687`, user=neo4j, pass=seeworld123
- **MySQL**: `research_db`, user=root, pass=qwer1234
- **Python 服务启动日志关键行**: `GraphQuery 索引: paper_kw=..., KG 初始化完成` 确认数据链路正常
