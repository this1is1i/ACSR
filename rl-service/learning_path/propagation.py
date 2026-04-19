# learning_path/propagation.py
# 知识掌握度传播算法 —— 用于三维学习路径可视化颜色更新

from __future__ import annotations
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from knowledge_graph.kg_builder import KnowledgeGraph
from learning_path.path_builder import LearningPath, PathNode

logger = logging.getLogger(__name__)


class KnowledgePropagation:
    """
    知识掌握度传播算法。

    传播模型（仿照信息传播 / 影响力最大化）：

        Δmastery(A) = learning_event(A)          # 直接学习事件
        Δmastery(B) += Δmastery(A) * w(A→B)      # 一阶传播
        Δmastery(C) += Δmastery(B) * w(B→C)      # 二阶传播（衰减）

    其中 w(A→B) 为知识图谱中 A→B 边的权重，
    代表「掌握 A 对理解 B 的帮助程度」。

    应用场景：
        - 用户阅读一篇 RL 论文后，自动提升 MDP / Q-learning 相关知识的掌握度
        - 颜色映射：mastery=0 → 蓝色（未学），mastery=1 → 绿色（已掌握）
        - 控制三维图谱中节点的发光强度
    """

    def __init__(
        self,
        kg: KnowledgeGraph,
        decay_factor: float = 0.6,      # 每跳的传播衰减系数
        max_propagation_hops: int = 3,  # 最大传播跳数
        min_delta: float = 1e-4,        # 低于此阈值停止传播
    ):
        self.kg = kg
        self.decay = decay_factor
        self.max_hops = max_propagation_hops
        self.min_delta = min_delta

        # 全局掌握度状态 {node_id → mastery_value}
        self.mastery_state: Dict[str, float] = defaultdict(float)

    # ── 主接口 ────────────────────────────────────────────────────

    def update_mastery(
        self,
        event_node_id: str,
        delta: float = 1.0,
        event_type: str = "read",  # "read" | "favorite" | "write"
    ) -> Dict[str, float]:
        """
        用户发生学习事件时，传播掌握度更新。

        Args:
            event_node_id: 触发事件的节点 ID（通常为论文或关键词）
            delta:         直接掌握度增量（默认 1.0）
            event_type:    事件类型（影响传播强度）

        Returns:
            本次传播影响到的节点及其更新量 {node_id: delta}
        """
        # 事件类型系数
        event_multiplier = {"read": 1.0, "favorite": 1.5, "write": 2.0}.get(event_type, 1.0)
        effective_delta = delta * event_multiplier

        # 直接更新事件节点
        self.mastery_state[event_node_id] = min(
            1.0, self.mastery_state[event_node_id] + effective_delta
        )

        # 传播到邻居节点
        propagated: Dict[str, float] = {event_node_id: effective_delta}
        self._propagate(event_node_id, effective_delta, 0, propagated)

        logger.debug(
            f"掌握度传播：{event_node_id}，影响 {len(propagated)} 个节点"
        )
        return propagated

    def batch_update(
        self,
        history: List[str],
        event_type: str = "read",
    ) -> Dict[str, float]:
        """
        根据用户历史阅读批量更新掌握度（初始化时使用）。

        越早读的论文传播量越小（模拟遗忘效应），
        越近读的论文传播量越大。
        """
        n = len(history)
        all_propagated: Dict[str, float] = {}
        for i, paper_id in enumerate(history):
            # 时间衰减：越早读，掌握度贡献越低
            time_weight = (i + 1) / n
            updates = self.update_mastery(paper_id, delta=time_weight, event_type=event_type)
            for nid, d in updates.items():
                all_propagated[nid] = all_propagated.get(nid, 0) + d
        return all_propagated

    def get_mastery_snapshot(
        self,
        node_ids: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """
        获取当前掌握度快照。

        Args:
            node_ids: 指定查询的节点列表（None 返回全部）

        Returns:
            {node_id: mastery_value [0,1]}
        """
        if node_ids is None:
            return dict(self.mastery_state)
        return {nid: self.mastery_state.get(nid, 0.0) for nid in node_ids}

    def apply_to_path(
        self,
        path: LearningPath,
    ) -> LearningPath:
        """
        将当前掌握度状态应用到学习路径节点（更新 node.mastery 字段）。
        用于前端可视化时获取「带掌握度的路径数据」。
        """
        for node in path.nodes:
            node.mastery = round(
                min(1.0, self.mastery_state.get(node.node_id, 0.0)), 4
            )
        return path

    def get_color_mapping(
        self,
        node_ids: List[str],
    ) -> Dict[str, str]:
        """
        生成节点 → 颜色的映射（用于三维可视化）。

        颜色方案：
            mastery = 0.0  →  #3B82F6 (蓝色，未学习)
            mastery = 0.5  →  #F59E0B (橙色，学习中)
            mastery = 1.0  →  #10B981 (绿色，已掌握)
        """
        colors = {}
        for nid in node_ids:
            m = self.mastery_state.get(nid, 0.0)
            colors[nid] = self._mastery_to_color(m)
        return colors

    def get_glow_intensity(
        self,
        node_ids: List[str],
    ) -> Dict[str, float]:
        """
        生成节点发光强度映射（0.0~1.0），直接对应 Three.js 的 emissiveIntensity。
        """
        return {nid: self.mastery_state.get(nid, 0.0) for nid in node_ids}

    # ── 内部传播算法 ──────────────────────────────────────────────

    def _propagate(
        self,
        node_id: str,
        delta: float,
        hop: int,
        propagated: Dict[str, float],
    ) -> None:
        """
        递归传播掌握度。

        传播公式：
            mastery(neighbor) += delta * decay^(hop+1) * edge_weight

        传播沿 has_keyword、cite（反向）、publish_in 等边扩散。
        """
        if hop >= self.max_hops or delta < self.min_delta:
            return

        # 传播边类型及权重系数
        propagate_relations = {
            "has_keyword": 0.8,    # 论文 → 关键词：强传播
            "cite": 0.4,           # 论文 → 引用论文：中等传播
            "publish_in": 0.3,     # 论文 → 场馆：弱传播
        }

        for edge in self.kg._adj.get(node_id, []):
            rel_weight = propagate_relations.get(edge.relation)
            if rel_weight is None:
                continue

            neighbor_id = edge.dst_id
            new_delta = delta * self.decay * rel_weight * edge.weight

            if new_delta < self.min_delta:
                continue

            old_mastery = self.mastery_state.get(neighbor_id, 0.0)
            new_mastery = min(1.0, old_mastery + new_delta)
            self.mastery_state[neighbor_id] = new_mastery

            if neighbor_id not in propagated or propagated[neighbor_id] < new_delta:
                propagated[neighbor_id] = new_delta
                self._propagate(neighbor_id, new_delta, hop + 1, propagated)

    @staticmethod
    def _mastery_to_color(mastery: float) -> str:
        """将掌握度 [0,1] 映射为 HEX 颜色字符串。"""
        # 蓝 → 橙 → 绿 三色渐变
        if mastery < 0.5:
            t = mastery * 2
            r = int(59 + (245 - 59) * t)
            g = int(130 + (158 - 130) * t)
            b = int(246 + (11 - 246) * t)
        else:
            t = (mastery - 0.5) * 2
            r = int(245 + (16 - 245) * t)
            g = int(158 + (185 - 158) * t)
            b = int(11 + (129 - 11) * t)
        return f"#{r:02X}{g:02X}{b:02X}"
