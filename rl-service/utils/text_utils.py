# utils/text_utils.py
# 文本清洗与分词工具（从 preprocess.py 提取）

import re
from typing import List

# 英文停用词表（轻量级，无需 nltk）
_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can",
    "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "or", "and", "but", "not", "this", "that", "we", "our",
    "paper", "propose", "show", "present", "method", "approach",
}


def clean_text(text: str) -> str:
    """移除控制字符、多余空格，统一编码。"""
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> List[str]:
    """简单英文分词，去除停用词和短词。"""
    text = re.sub(r"[^a-zA-Z\s]", " ", text.lower())
    return [w for w in text.split() if len(w) > 2 and w not in _STOP_WORDS]
