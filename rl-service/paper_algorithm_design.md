# 第三章 基于 Actor–Critic 的科研推荐系统算法设计

---

## 3.1 问题形式化定义

本文将科研内容推荐问题建模为**马尔可夫决策过程（MDP）**，形式化为五元组：

$$\mathcal{M} = \langle \mathcal{S},\ \mathcal{A},\ \mathcal{P},\ \mathcal{R},\ \gamma \rangle$$

其中各元素定义如下：

- **状态空间** $\mathcal{S}$：用户在每个时间步的科研兴趣画像；
- **动作空间** $\mathcal{A}$：从候选科研内容集合中选取推荐项；
- **转移概率** $\mathcal{P}$：用户与推荐内容交互后兴趣向量的漂移规律；
- **奖励函数** $\mathcal{R}$：综合多维度交互信号的即时回报；
- **折扣因子** $\gamma \in [0,1)$：平衡短期点击率与长期科研价值的权重。

系统目标为学习最优策略 $\pi^*$，使得期望累积折扣奖励最大化：

$$J(\pi) = \mathbb{E}_{\pi}\left[\sum_{t=0}^{T} \gamma^t r_t\right]$$

---

## 3.2 状态空间设计

用户状态向量 $s_t \in \mathbb{R}^{d}$（$d=64$）由以下特征拼接构成：

$$s_t = \left[\mathbf{e}^{\text{interest}}_{t} \;\|\; \mathbf{e}^{\text{history}}_{t} \;\|\; \mathbf{e}^{\text{KG}}_{t} \;\|\; \mathbf{e}^{\text{community}}_{t}\right]$$

| 特征分量 | 维度 | 来源 | 状态 |
|---|---|---|---|
| 兴趣向量 $\mathbf{e}^{\text{interest}}$ | 32 | 用户画像 embedding | 已实现 |
| 历史行为向量 $\mathbf{e}^{\text{history}}$ | 32 | 近期交互均值池化 | 已实现 |
| 知识图谱特征 $\mathbf{e}^{\text{KG}}$ | 32 | 图神经网络（GNN）编码 | 预留接口 |
| 社区行为特征 $\mathbf{e}^{\text{community}}$ | 16 | 相似用户协同信号 | 预留接口 |

状态转移规律遵循以下规则：用户每次与推荐内容交互后，历史行为向量通过指数移动平均更新：

$$\mathbf{e}^{\text{history}}_{t+1} = 0.9 \cdot \mathbf{e}^{\text{history}}_{t} + 0.1 \cdot \mathbf{e}^{\text{item}}_{t}$$

该设计模拟了用户科研兴趣随交互逐渐漂移的动态过程。

---

## 3.3 动作空间设计

动作空间 $\mathcal{A} = \{0, 1, \ldots, N-1\}$ 为**离散动作空间**，$N$ 为候选科研内容数量。  
每个时间步，Agent 从 $N$ 个候选条目中选择一项进行推荐。

**Top-K 推荐扩展**：推理阶段利用 Actor 网络输出的概率分布，选取概率最高的 $K$ 个动作，实现多路推荐：

$$\text{Top-K}(s) = \underset{a \in \mathcal{A}}{\text{arg-topk}}\; \pi(a \mid s)$$

---

## 3.4 奖励函数设计

为解决传统推荐系统仅优化点击率、忽视长期科研价值的缺陷，本文设计了**多维度加权线性奖励函数**：

$$r_t = \alpha \cdot c_{\text{click}} + \beta \cdot c_{\text{fav}} + \gamma_r \cdot c_{\text{read}} + \delta \cdot c_{\text{topic}} + \eta \cdot c_{\text{LTV}}$$

各项含义如下：

| 符号 | 含义 | 量纲 | 权重（默认值） |
|---|---|---|---|
| $c_{\text{click}}$ | 用户点击行为 | {0, 1} | $\alpha = 1.0$ |
| $c_{\text{fav}}$ | 用户收藏行为 | {0, 1} | $\beta = 2.0$ |
| $c_{\text{read}}$ | 归一化阅读时长 | [0, 1] | $\gamma_r = 0.5$ |
| $c_{\text{topic}}$ | 研究方向匹配度（余弦相似度） | [0, 1] | $\delta = 3.0$ |
| $c_{\text{LTV}}$ | 长期科研价值（引用潜力×匹配度） | [0, 1] | $\eta = 1.5$ |

奖励函数封装为独立模块，支持通过继承 `BaseRewardFunction` 替换为任意自定义策略（如多目标 RL、好奇心驱动奖励等）。

---

## 3.5 Actor–Critic 算法设计

### 3.5.1 策略网络（Actor）

Actor 网络 $\pi(a \mid s;\, \theta)$ 输出候选动作上的概率分布：

$$\pi(a \mid s;\, \theta) = \text{Softmax}\left(\mathbf{W}_3 \cdot \text{ReLU}\left(\mathbf{W}_2 \cdot \text{ReLU}\left(\mathbf{W}_1 s + \mathbf{b}_1\right) + \mathbf{b}_2\right) + \mathbf{b}_3\right)$$

网络各层使用 **LayerNorm** 稳定训练，最终层权重以正交初始化（gain=0.01）压缩初始策略的确定性，保证充分探索。

### 3.5.2 价值网络（Critic）

Critic 网络 $V(s;\, w)$ 估计当前状态的期望累积回报：

$$V(s;\, w) = \mathbf{W}_3' \cdot \text{ReLU}\left(\mathbf{W}_2' \cdot \text{ReLU}\left(\mathbf{W}_1' s + \mathbf{b}_1'\right) + \mathbf{b}_2'\right) + \mathbf{b}_3'$$

### 3.5.3 TD 误差计算

采用**单步时序差分（TD(0)）**估计优势函数：

$$\delta_t = r_t + \gamma \cdot V(s_{t+1};\, w) \cdot (1 - d_t) - V(s_t;\, w)$$

其中 $d_t \in \{0,1\}$ 为终止标志，终止时目标仅使用即时奖励。

### 3.5.4 网络参数更新

**Critic 更新**（最小化均方 TD 误差）：

$$\mathcal{L}_{\text{critic}} = \delta_t^2, \qquad w \leftarrow w - \alpha_w \nabla_w \mathcal{L}_{\text{critic}}$$

**Actor 更新**（策略梯度 + 熵正则化）：

$$\mathcal{L}_{\text{actor}} = -\log \pi(a_t \mid s_t;\, \theta) \cdot \delta_t^{\text{stop\_grad}} - \beta_e \cdot H(\pi(\cdot \mid s_t))$$

$$\theta \leftarrow \theta - \alpha_\theta \nabla_\theta \mathcal{L}_{\text{actor}}$$

其中熵项 $H(\pi) = -\sum_a \pi(a\mid s)\log\pi(a\mid s)$ 防止策略过早收敛，鼓励多样化推荐，避免信息茧房效应。梯度裁剪（max\_norm=1.0）防止梯度爆炸。

---

## 3.6 系统工程架构

本系统遵循**单一职责原则**，各模块职责清晰，支持水平替换：

```
rl_recommender/
├── config.py          # 超参数统一管理
├── train.py           # 主训练循环（Episode × Step）
├── agent.py           # Actor-Critic 智能体（核心算法）
├── models/
│   ├── actor.py       # 策略网络 π(a|s; θ)
│   └── critic.py      # 价值网络 V(s; w)
├── env/
│   └── rec_env.py     # 推荐环境（可替换为真实数据库）
├── utils/
│   ├── reward.py      # 可插拔奖励函数模块
│   └── logger.py      # 训练日志记录
└── data/
    └── mock_data.py   # 数据层（含数据库适配器接口）
```

推荐环境（`rec_env.py`）遵循 OpenAI Gym 风格接口，通过替换 `MockDataGenerator` 为 `DatabaseAdapter` 子类，即可无缝接入 MySQL 数据库或 Spring Boot REST API，无需修改算法层代码。

---

## 3.7 算法复杂度分析

| 维度 | 复杂度 |
|---|---|
| 前向推断（单步） | $O(d \cdot h + h^2 + h \cdot N)$，$h$=hidden\_dim |
| Critic 更新 | $O(d \cdot h + h^2)$（单步反向传播） |
| Actor 更新 | $O(d \cdot h + h^2 + h \cdot N)$（单步反向传播） |
| 空间复杂度 | $O(d \cdot h + h^2 + h \cdot N)$（参数量） |
| Top-K 推荐 | $O(N \log K)$（堆排序） |

---

## 3.8 预留扩展接口说明

| 扩展方向 | 预留位置 | 接入方式 |
|---|---|---|
| 知识图谱 GNN embedding | `Actor.forward_with_kg()` / `rec_env.inject_kg_features()` | 拼接至状态向量 |
| 推荐理由自然语言生成 | `rec_env.generate_explanation()` | 对接 LLM 或模板引擎 |
| Spring Boot API 推理 | `agent.predict_for_api()` | JSON 序列化接口 |
| PPO 替换 Actor-Critic | `agent.update_ppo()` | 替换 `update()` 方法 |
| 多目标 RL 奖励 | 继承 `BaseRewardFunction` | 实现 `compute()` 方法 |
| TensorBoard / WandB | `logger.init_tensorboard()` / `logger.init_wandb()` | 一行调用启用 |

---

*本章代码均通过 Python AST 语法验证，可直接运行训练。核心算法实现位于 `agent.py`，推荐环境接口位于 `env/rec_env.py`。*
