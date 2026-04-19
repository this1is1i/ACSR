# 第四章 推荐服务系统设计

---

## 4.1 系统整体架构

本章在第三章算法设计的基础上，构建完整的推荐服务系统。系统采用**分层架构**设计，从上至下共五层：

```
外部调用层  →  API 服务层  →  推荐服务层  →  核心算法层  →  数据层
```

各层职责单一、接口明确，支持水平替换任意层的实现，不影响其他层的功能。

---

## 4.2 候选集生成模块

### 4.2.1 设计目标

候选集生成是推荐系统的第一阶段（召回阶段），目标是从全量论文库（规模可达百万级）中快速筛选出与用户相关的小规模候选集（通常 20-100 篇），供后续强化学习排序使用。

### 4.2.2 召回策略

本系统实现三种召回策略，可通过 `strategy` 参数切换：

**（1）语义相似度召回**

计算用户兴趣向量 $\mathbf{u}$ 与论文特征向量 $\mathbf{p}_i$ 的余弦相似度：

$$\text{sim}(\mathbf{u}, \mathbf{p}_i) = \frac{\mathbf{u} \cdot \mathbf{p}_i}{\|\mathbf{u}\| \cdot \|\mathbf{p}_i\|}$$

取相似度最高的 Top-M 篇作为候选集。生产环境使用 Faiss ANN（近似最近邻）检索，时间复杂度从 $O(N)$ 降至 $O(\log N)$。

**（2）热门论文召回**

按论文被引量降序排列，召回高影响力经典文献。该策略解决新用户（冷启动）场景下兴趣向量不准确的问题。

**（3）混合策略（默认）**

$$\mathcal{C}_{\text{hybrid}} = 70\%\; \mathcal{C}_{\text{similarity}} \cup 30\%\; \mathcal{C}_{\text{popular}}$$

混合策略在相关性与多样性之间取得平衡，兼顾精准推荐和领域拓展。

### 4.2.3 数据接入接口

模块提供三个标准化接入接口（当前为预留状态）：

| 接口方法 | 接入数据源 | 适用场景 |
|---|---|---|
| `fetch_from_mysql()` | MySQL / PostgreSQL | 小规模结构化数据 |
| `fetch_from_elasticsearch()` | Elasticsearch | 全文检索 + BM25 |
| `fetch_from_vector_db()` | Faiss / Milvus | 大规模向量检索 |

---

## 4.3 强化学习排序模块

### 4.3.1 排序原理

排序模块（`ranker.py`）与训练模块（`agent.py`）解耦设计：训练阶段 Agent 通过与模拟环境交互优化策略；推理阶段 Ranker 仅调用 Actor 网络的前向推断，不涉及反向传播，保证推理效率。

对于候选集中的每篇论文 $i$，综合分计算为：

$$\text{score}_i = 0.6 \cdot \pi(a_i \mid s;\; \theta) + 0.4 \cdot \text{sim}(\mathbf{u}, \mathbf{p}_i)$$

其中：
- $\pi(a_i \mid s;\; \theta)$ 为 Actor 策略网络对动作 $a_i$ 的输出概率（已学习用户长期偏好）；
- $\text{sim}(\mathbf{u}, \mathbf{p}_i)$ 为即时语义相似度（捕捉短期相关性）。

两者加权融合，兼顾**长期科研价值**（RL 学习到的策略）与**即时相关性**（语义匹配）。

### 4.3.2 Top-K 选择

对所有候选项按综合分降序排列，取前 $K$ 篇作为最终推荐结果：

$$\text{Top-K}(s) = \underset{i \in \mathcal{C}}{\text{arg-topk}}\; \text{score}_i, \quad K \leq |\mathcal{C}|$$

---

## 4.4 推荐解释机制

### 4.4.1 设计动机

黑箱推荐系统（如纯深度神经网络）的推荐结果缺乏可解释性，用户难以理解推荐原因，导致信任度低、科研参考价值受限。本系统采用**基于结构化特征的解释生成**方案，确保每条推荐理由可追溯、可验证。

### 4.4.2 解释生成流程

解释模块（`explain.py`）从以下四个维度提取特征并生成解释：

**维度一：语义相似度**

$$\text{sim}_{\text{norm}} = \frac{\text{sim}(\mathbf{u}, \mathbf{p}) + 1}{2} \in [0, 1]$$

当 $\text{sim}_{\text{norm}} > 0.7$ 时，生成"与你研究兴趣高度匹配（X%）"类型的解释。

**维度二：研究方向重叠**

$$\mathcal{T}_{\text{overlap}} = \mathcal{T}_{\text{user}} \cap \mathcal{T}_{\text{paper}}$$

当存在共同研究方向时，生成"涵盖你关注的研究方向：X"类型的解释。

**维度三：学术影响力**

当论文被引量 $c > 300$ 时，生成"高被引经典论文（$c$ 次引用）"类型的解释。

**维度四：时效性**

当论文年份 $y \geq 2023$ 时，生成"最新研究，紧跟领域前沿"类型的解释。

### 4.4.3 解释输出格式

```json
{
  "paper_id": "paper_0012",
  "reason": "与你在 Reinforcement Learning 方向的研究高度相关（匹配度 82%）",
  "reason_details": [
    "与你的研究兴趣高度匹配（相似度 82%）",
    "涵盖你关注的研究方向：Reinforcement Learning",
    "高被引经典论文（456 次引用），学术影响力强"
  ],
  "similarity_score": 0.8234,
  "topic_overlap": ["Reinforcement Learning"],
  "confidence": 0.7863
}
```

### 4.4.4 LLM 改写接口（预留）

系统预留 `rewrite_with_llm()` 接口，可将结构化理由接入大语言模型（ChatGLM3 / GPT-4），改写为更自然流畅的推荐语言，同时保留可追溯的结构化来源。

---

## 4.5 特征工程模块

用户状态向量 $s_t$ 由 `feature_builder.py` 统一构建：

$$s_t = \text{normalize}\left(\left[\mathbf{e}^{\text{interest}} \;\|\; \mathbf{e}^{\text{history}}\right]\right) \in \mathbb{R}^{64}$$

归一化处理确保状态向量的数值稳定性，防止 Actor/Critic 网络因输入尺度不一致导致的训练不稳定。

预留的知识图谱特征接入点：

```python
# 启用时取消注释，同步调整 state_dim
# if features.kg_vector is not None:
#     parts.append(features.kg_vector[:KG_DIM])
```

---

## 4.6 REST API 设计

### 4.6.1 接口规范

系统基于 FastAPI 实现 RESTful API 服务，提供 4 个核心接口：

| 方法 | 路径 | 功能 | 响应时延（估计） |
|---|---|---|---|
| POST | `/recommend` | Top-K 科研推荐 | < 50ms |
| POST | `/train` | 异步触发模型训练 | 立即返回 |
| GET | `/model/info` | 查询模型状态 | < 5ms |
| POST | `/model/reload` | 热重载模型权重 | < 1s |
| GET | `/health` | 服务健康检查 | < 1ms |

### 4.6.2 Spring Boot 对接方案

Spring Boot 后端通过 `RestTemplate` 或 `WebClient` 调用推荐接口：

```java
// Spring Boot 调用示例
@Service
public class RecommendationClient {
    private final RestTemplate restTemplate = new RestTemplate();
    private final String baseUrl = "http://localhost:8000";

    public RecommendResponse getRecommendations(String userId, int k) {
        RecommendRequest req = new RecommendRequest(userId, k);
        return restTemplate.postForObject(
            baseUrl + "/recommend", req, RecommendResponse.class
        );
    }
}
```

推荐服务以 JSON 格式返回结果，与 Spring Boot 的 Jackson 序列化无缝兼容，无需额外适配。

### 4.6.3 异步训练设计

训练接口采用 **FastAPI BackgroundTasks** 机制实现异步训练，避免长时间训练阻塞 HTTP 请求。训练完成后自动调用 `reload_model()` 热重载新权重，服务无需重启：

```
POST /train → 立即返回 200 → 后台线程训练 → 完成后热重载 → 新模型生效
```

---

## 4.7 系统性能指标

| 指标 | 目标值 | 优化手段 |
|---|---|---|
| 推荐响应时延 | < 50ms | 候选集预计算 + Actor 推理缓存 |
| 候选集生成时间 | < 10ms | Faiss ANN 检索 |
| 模型训练收敛 | 200-500 轮 | 熵正则化 + 梯度裁剪 |
| API 并发支持 | 100+ QPS | uvicorn + asyncio |

---

## 4.8 模块依赖关系

```
api/server.py
    └── services/recommendation_service.py
            ├── features/feature_builder.py
            ├── recommender/candidate_generator.py
            ├── recommender/ranker.py  ← agent.py ← models/{actor,critic}.py
            └── recommender/explain.py
                    └── utils/reward.py (奖励函数，训练时使用)
```

每个模块均可独立单元测试，替换任意模块只需实现相同接口签名，其余模块无需修改。

---

*本章所有代码均通过 Python AST 语法验证，可通过 `python api/server.py` 直接启动 API 服务（需安装 fastapi, uvicorn）。*
