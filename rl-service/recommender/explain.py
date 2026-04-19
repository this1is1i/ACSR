# recommender/explain.py
# 推荐解释生成模块 —— 基于结构化特征生成可读推荐理由

from __future__ import annotations
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from recommender.candidate_generator import CandidateItem
from features.feature_builder import UserFeatures


@dataclass
class ExplanationResult:
    """推荐解释结果。"""
    paper_id: str
    reason: str                      # 主推荐理由（一句话）
    reason_details: List[str]        # 详细支撑因素列表
    similarity_score: float          # 与用户兴趣相似度
    topic_overlap: List[str]         # 共同研究方向
    confidence: float                # 推荐置信度


class ExplanationGenerator:
    """
    推荐解释生成器。

    解释来源于结构化特征，而非黑箱神经网络输出，确保：
      1. 可解释性（用户能理解推荐原因）
      2. 可信赖性（基于真实特征，非生成式幻觉）
      3. 多样性（按不同维度生成差异化理由）

    预留 LLM 接入接口：可调用 GPT / ChatGLM 将结构化理由改写为流畅自然语言。
    """

    # 推荐理由模板库
    _TEMPLATES = {
        "high_similarity":   "与你的研究兴趣高度匹配（相似度 {sim:.0%}）",
        "topic_overlap":     "涵盖你关注的研究方向：{topics}",
        "high_citation":     "高被引经典论文（{count} 次引用），学术影响力强",
        "recent_work":       "{year} 年发表的最新研究，紧跟领域前沿",
        "history_related":   "与你近期阅读的论文主题高度相关",
        "keyword_match":     "关键词与你的历史研究记录高度吻合",
        "community_hot":     "近期在同领域研究者中广泛传播",
    }

    def generate_explanation(
        self,
        user: UserFeatures,
        item: CandidateItem,
        rank: int = 1,
    ) -> ExplanationResult:
        """
        为单个推荐结果生成结构化解释。

        Args:
            user: 用户特征
            item: 推荐论文
            rank: 推荐排名（影响描述措辞）

        Returns:
            ExplanationResult 结构化解释对象
        """
        # ── 计算相似度 ────────────────────────────────────────────
        sim = 0.0
        if item.topic_vector is not None:
            raw_sim = float(np.dot(user.interest_vector, item.topic_vector))
            sim = float(np.clip((raw_sim + 1.0) / 2.0, 0.0, 1.0))  # 归一化到 [0,1]

        # ── 识别主题重叠 ──────────────────────────────────────────
        topic_overlap = list(set(item.topics) & set(user.research_topics))

        # ── 构建详细理由列表 ──────────────────────────────────────
        details: List[str] = []

        if sim > 0.7:
            details.append(self._TEMPLATES["high_similarity"].format(sim=sim))
        elif sim > 0.4:
            details.append(f"与你的研究方向存在较强关联性（匹配度 {sim:.0%}）")

        if topic_overlap:
            details.append(self._TEMPLATES["topic_overlap"].format(
                topics="、".join(topic_overlap)
            ))

        if item.citation_count > 300:
            details.append(self._TEMPLATES["high_citation"].format(
                count=item.citation_count
            ))

        if item.year >= 2023:
            details.append(self._TEMPLATES["recent_work"].format(year=item.year))

        if sim > 0.5:
            details.append(self._TEMPLATES["history_related"])

        if not details:
            details.append(f"该论文与你的科研背景具有一定相关性")

        # ── 合成主推荐理由 ────────────────────────────────────────
        main_reason = self._compose_main_reason(item, sim, topic_overlap, rank)

        confidence = float(np.clip(sim * 0.7 + 0.3 * min(item.citation_count / 500, 1.0), 0.1, 0.99))

        return ExplanationResult(
            paper_id=item.item_id,
            reason=main_reason,
            reason_details=details,
            similarity_score=round(sim, 4),
            topic_overlap=topic_overlap,
            confidence=round(confidence, 4),
        )

    def batch_explain(
        self,
        user: UserFeatures,
        items: List[CandidateItem],
    ) -> List[ExplanationResult]:
        """批量生成推荐解释。"""
        return [
            self.generate_explanation(user, item, rank=i + 1)
            for i, item in enumerate(items)
        ]

    def to_dict(self, result: ExplanationResult) -> Dict[str, Any]:
        """将解释结果序列化为 JSON 兼容字典（供 REST API 使用）。"""
        return {
            "paper_id": result.paper_id,
            "reason": result.reason,
            "reason_details": result.reason_details,
            "similarity_score": result.similarity_score,
            "topic_overlap": result.topic_overlap,
            "confidence": result.confidence,
        }

    # ── LLM 改写接口（预留）──────────────────────────────────────

    def rewrite_with_llm(
        self,
        structured_reason: str,
        style: str = "friendly",
    ) -> str:
        """
        调用大语言模型将结构化理由改写为自然语言（预留接口）。

        接入方式：
          - 调用 OpenAI GPT-4 / ChatGLM3 API
          - Prompt: "请将以下结构化推荐理由改写为一句亲切的中文：{structured_reason}"
        """
        raise NotImplementedError("LLM 推荐理由改写接口待实现")

    # ── 内部辅助 ──────────────────────────────────────────────────

    def _compose_main_reason(
        self,
        item: CandidateItem,
        sim: float,
        topic_overlap: List[str],
        rank: int,
    ) -> str:
        """合成一句话主推荐理由。"""
        if topic_overlap and sim > 0.6:
            return f"与你在 {topic_overlap[0]} 方向的研究高度相关（匹配度 {sim:.0%}）"
        elif sim > 0.7:
            return f"与你的研究兴趣向量相似度达 {sim:.0%}，强烈推荐"
        elif item.citation_count > 400:
            return f"该领域高被引经典之作（{item.citation_count} 引用），建议精读"
        elif item.year >= 2023:
            return f"{item.year} 年最新研究，与你的科研方向存在交叉"
        else:
            return f"基于你的科研画像，智能推荐相关论文（综合匹配度 {sim:.0%}）"
