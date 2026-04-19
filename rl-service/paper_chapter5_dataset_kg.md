# 第五章 数据集处理与科研知识图谱构建

---

## 5.1 AMiner 数据集介绍

### 5.1.1 数据集概述

AMiner（Academic Miner）是由清华大学开发的开放学术知识挖掘平台，提供学术文献和科研人员的综合数据集。本系统采用 **AMiner Citation Network Dataset V14**，主要统计指标如下：

| 统计项 | 数量 |
|---|---|
| 论文总数 | 5,260,000 篇 |
| 作者总数 | 4,900,000 人 |
| 引用关系 | 36,000,000 条 |
| 覆盖年份 | 1900–2024 |
| 涉及领域 | 计算机科学、物理、数学等 |

数据集下载地址：https://www.aminer.org/citation

### 5.1.2 数据格式

AMiner V14 采用 JSON 格式存储，每条论文记录包含以下字段：

```json
{
  "id": "aminer_001234",
  "title": "Playing Atari with Deep Reinforcement Learning",
  "abstract": "We present the first deep learning model...",
  "authors": [{"id": "author_001", "name": "Volodymyr Mnih", "org": "DeepMind"}],
  "year": 2013,
  "venue": "NIPS Workshop",
  "fos": [{"name": "Reinforcement Learning"}, {"name": "Deep Learning"}],
  "references": ["aminer_000123", "aminer_000456"]
}
```

本系统的 `AMinerLoader` 兼容 AMiner V12、V13、V14 多个版本的字段命名差异，并支持 JSON Array 和 JSONL 两种文件格式的流式解析，避免将大文件一次性加载到内存。

---

## 5.2 数据预处理

### 5.2.1 数据清洗流程

原始 AMiner 数据存在标题缺失、年份异常、摘要为空等质量问题。本系统实现以下清洗规则：

**去重策略**：以 `paper_id` 为主键去重；对于同一论文的多版本记录，保留摘要信息更完整的版本。

**过滤规则**：
- 标题长度 < 5 字符的记录视为无效
- 年份不在 [1990, 2026] 范围内的记录过滤
- 摘要长度 < 20 字符且无关键词的记录过滤

### 5.2.2 关键词提取

对于原始数据中关键词缺失的论文，系统采用 TF-IDF 算法从标题和摘要中自动提取关键词：

$$\text{TF-IDF}(t, d) = \frac{\text{tf}(t,d)}{\text{df}(t)/N}$$

其中 $\text{tf}(t,d)$ 为词 $t$ 在文档 $d$ 中的频次，$\text{df}(t)$ 为包含词 $t$ 的文档数，$N$ 为总文档数。

生产环境升级方案：使用 **KeyBERT** 或 **YAKE** 基于语义的关键词提取算法，结合计算机科学领域词典进行关键词标准化。

### 5.2.3 论文 Embedding 构建

论文语义向量化采用两种方案，通过参数切换：

**方案一（默认）**：TF-IDF 哈希 Embedding（无 GPU 依赖，开发阶段直接运行）

将标题+摘要+关键词拼接后，通过哈希映射构建 64 维稀疏向量，L2 归一化：

$$\mathbf{e}_i = \text{normalize}\left(\sum_{w \in d_i} \mathbf{h}(w)\right)$$

**方案二（生产推荐）**：基于 **SPECTER** 学术论文预训练模型（Allen AI）

```python
# 安装：pip install sentence-transformers
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("allenai-specter")
embeddings = model.encode(
    [p.text_for_embedding() for p in papers],
    batch_size=64, show_progress_bar=True
)
```

SPECTER 模型在引用感知的对比学习目标下预训练，生成的 768 维向量经 PCA 降维至 64 维，在科研论文语义相似度任务上显著优于 BERT。

---

## 5.3 知识图谱构建

### 5.3.1 图谱设计

本系统构建的科研知识图谱 $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ 包含四类节点和五类边关系：

**节点类型（$\mathcal{V}$）**：

| 节点类型 | 含义 | 来源字段 |
|---|---|---|
| Paper | 论文实体 | paper_id, title, abstract |
| Author | 研究者实体 | author_id, name, org |
| Keyword | 研究关键词 | keywords, fos |
| Venue | 发表场所 | venue, journal |

**边关系类型（$\mathcal{E}$）**：

| 关系类型 | 方向 | 含义 | 边数（估计） |
|---|---|---|---|
| author_of | Author → Paper | 作者撰写论文 | ~15M |
| cite | Paper → Paper | 论文引用关系 | ~36M |
| has_keyword | Paper → Keyword | 论文包含关键词 | ~25M |
| publish_in | Paper → Venue | 论文发表在期刊/会议 | ~5M |
| co_author | Author ↔ Author | 合著关系（推导） | ~8M |

### 5.3.2 图谱构建算法

构建流程共九步，时间复杂度为 $O(N_p + N_a + N_c)$（$N_p$=论文数，$N_a$=作者数，$N_c$=引用数）：

```
1. 创建 Paper 节点
2. 创建 Author 节点
3. 统计关键词频次，过滤低频词（freq < 2）
4. 创建 Keyword 节点（保留 Top-500）
5. 创建 Venue 节点
6. 构建 author_of 边
7. 构建 cite 边（过滤图外引用）
8. 构建 has_keyword 和 publish_in 边
9. 推导 co_author 边（O(k²) per paper，k=共同作者数）
```

关键词节点过滤策略防止图谱被高频停用词（如 "learning"、"model"）污染，保留语义区分度高的领域术语。

### 5.3.3 知识图谱存储

系统支持三种持久化方式：

- **JSON 文件**：人类可读，便于调试，适合小规模（< 10 万节点）
- **Pickle 二进制**：加载速度快（比 JSON 快约 5×），适合频繁加载场景
- **Neo4j 图数据库**（预留）：适合生产环境，支持 Cypher 查询语言

---

## 5.4 Embedding 升级与 RL 状态扩展

### 5.4.1 三类 Embedding 构建

基于知识图谱，系统构建三类 Embedding：

**论文 Embedding**（$\mathbf{e}^{\text{paper}}$）：由预处理阶段生成，维度 64。

**关键词 Embedding**（$\mathbf{e}^{\text{kw}}$）：通过包含该关键词的论文 embedding 均值池化：

$$\mathbf{e}^{\text{kw}}_k = \frac{1}{|\mathcal{P}_k|} \sum_{p \in \mathcal{P}_k} \mathbf{e}^{\text{paper}}_p$$

**作者 Embedding**（$\mathbf{e}^{\text{author}}$）：通过该作者所有论文 embedding 均值池化，体现作者研究兴趣分布：

$$\mathbf{e}^{\text{author}}_a = \frac{1}{|\mathcal{P}_a|} \sum_{p \in \mathcal{P}_a} \mathbf{e}^{\text{paper}}_p$$

### 5.4.2 RL 状态向量升级

第三阶段将 RL 状态向量从 64 维升级到 128 维：

$$s_t^{\text{v2}} = \left[\mathbf{e}^{\text{interest}}(32) \;\|\; \mathbf{e}^{\text{history}}(32) \;\|\; \mathbf{e}^{\text{KG}}(32) \;\|\; \mathbf{e}^{\text{community}}(32)\right]$$

其中 $\mathbf{e}^{\text{KG}}$ 为用户历史论文 embedding 的均值（知识图谱特征），$\mathbf{e}^{\text{community}}$ 为该用户作为作者的 embedding（社区行为特征）。

---

## 5.5 学习路径生成算法

### 5.5.1 知识掌握度传播模型

基于信息传播理论，定义**知识掌握度传播**模型：

当用户阅读论文 $A$ 时，触发掌握度更新事件，传播规则为：

$$\text{mastery}(A) \mathrel{+}= \Delta$$

$$\text{mastery}(B) \mathrel{+}= \Delta \cdot \lambda \cdot w(A \rightarrow B)$$

$$\text{mastery}(C) \mathrel{+}= \Delta \cdot \lambda^2 \cdot w(A \rightarrow B) \cdot w(B \rightarrow C)$$

其中 $\lambda = 0.6$ 为衰减因子，$w(A \rightarrow B)$ 为知识图谱中 $A \rightarrow B$ 边的权重（has_keyword 边权重 0.8，cite 边权重 0.4）。

### 5.5.2 颜色映射方案

掌握度值 $m \in [0,1]$ 映射到三维可视化颜色：

- $m = 0.0$：$\#3B82F6$（蓝色，未学习）
- $m = 0.5$：$\#F59E0B$（橙色，学习中）
- $m = 1.0$：$\#10B981$（绿色，已掌握）

中间值通过 RGB 线性插值计算，直接对应 Three.js 的 `emissiveIntensity` 属性。

### 5.5.3 学习路径序列生成

```
输入：用户历史阅读 H, 目标方向 target_topic
输出：有序学习路径 P = [n₁, n₂, ..., nₖ]

1. 提取用户已掌握关键词集合 K_known（来自 H）
2. 查询 target_topic 的关键词聚类 K_target
3. 构建路径节点：
     depth=0: K_known ∩ K_target（已掌握基础）
     depth=1: K_target 相关关键词（待学习）
     depth=2: target_topic 节点
     depth=3: target_topic 相关论文（具体阅读材料）
4. 按 depth 排列节点，构建 depth→depth+1 的连接边
5. 应用传播算法，更新各节点 mastery 值
6. 序列化为 JSON，供前端三维可视化渲染
```

---

## 5.6 推荐解释增强

引入知识图谱后，推荐解释从原有的「相似度匹配」扩展为四维图结构解释：

| 解释维度 | 来源 | 示例 |
|---|---|---|
| 语义相似度 | 论文 embedding 余弦相似度 | "与您的研究兴趣相似度 82%" |
| 关键词共现 | has_keyword 边重叠 | "共享关键词：Actor-Critic, MDP" |
| 引用关系 | cite 边 | "该论文引用了您读过的《DQN》" |
| 合著关系 | co_author + author_of 边 | "与您阅读的论文来自同一作者" |

---

*本章所有代码可通过 `python dataset_pipeline.py` 一键执行完整流水线。真实 AMiner 数据可从官网下载后替换 `data/aminer/` 目录中的文件，无需修改任何代码。*
