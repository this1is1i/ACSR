"""
离线评估脚本 —— 计算 HR@K, Precision@K, Recall@K, MRR, Coverage
数据来源: behavior_log (训练/测试按时间切分)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from collections import defaultdict

from config import default_config
from data.mysql_data import MySQLDataSource

# ── 评估指标函数 ─────────────────────────────────────────────────

def compute_metrics(recommended, actual, K=10, total_items=None):
    """
    recommended: dict user_id → [recommended_paper_ids]  (top-K)
    actual:     dict user_id → [interacted_paper_ids]    (test set ground truth)
    """
    hr = []; prec = []; rec = []; mrr = []
    total_hits = set()

    for uid in actual:
        if uid not in recommended:
            continue
        recs = recommended[uid][:K]
        acts = set(actual[uid])
        hits = [p for p in recs if p in acts]
        total_hits.update(hits)

        hr.append(1 if hits else 0)
        prec.append(len(hits) / K)
        rec.append(len(hits) / max(len(acts), 1))
        first_hit = next((i + 1 for i, p in enumerate(recs) if p in acts), 0)
        mrr.append(1.0 / first_hit if first_hit else 0.0)

    coverage = len(total_hits) / max(total_items, 1) if total_items else 0.0

    return {
        "HR@10":       round(np.mean(hr), 4),
        "Precision@10": round(np.mean(prec), 4),
        "Recall@10":   round(np.mean(rec), 4),
        "MRR":         round(np.mean(mrr), 4),
        "Coverage":    round(coverage, 4),
        "TestUsers":   len(actual),
        "EvalUsers":   len([u for u in actual if u in recommended]),
    }


# ── 主流程 ───────────────────────────────────────────────────────

def main():
    config = default_config
    mysql = MySQLDataSource(config)

    # 1. 读取全量行为日志
    print("Reading behavior_log...")
    with mysql.conn.cursor() as cur:
        cur.execute("SELECT user_id, paper_id, `action`, timestamp FROM behavior_log ORDER BY timestamp")
        raw = cur.fetchall()
    print(f"  total rows: {len(raw)}")

    # 2. 按时间切分 (70% 训练, 30% 测试 — 数据量小, 适度放宽)
    split_idx = int(len(raw) * 0.7)
    split_time = raw[split_idx]["timestamp"]
    print(f"  split time: {split_time} (row {split_idx}/{len(raw)})")

    train_raw = raw[:split_idx]
    test_raw  = raw[split_idx:]

    # 3. 构建测试集 ground truth: 取 favorite + read 行为作为"正向交互"
    actual = defaultdict(set)
    for row in test_raw:
        uid, pid, action = row["user_id"], row["paper_id"], row["action"]
        if action in ("favorite", "read"):
            actual[int(uid)].add(int(pid))

    # 过滤掉交互不足 1 篇的用户
    actual = {uid: pids for uid, pids in actual.items() if len(pids) >= 1}
    print(f"  test users (≥1 interactions): {len(actual)}")

    # 4. 模拟推荐: 用每个用户在训练集中的行为构建简单画像
    #    (不启动完整 RL 管线, 用行为加权池化 + cosine 排序做近似)
    print("Building user profiles from training data...")
    user_train_papers = defaultdict(list)
    user_train_actions = defaultdict(list)
    for row in train_raw:
        uid, pid, action = row["user_id"], row["paper_id"], row["action"]
        user_train_papers[int(uid)].append(int(pid))
        user_train_actions[int(uid)].append(action)

    # 获取论文元数据用于向量模拟
    with mysql.conn.cursor() as cur:
        cur.execute("SELECT id, citation_count, year, keywords FROM paper WHERE deleted=0")
        papers = cur.fetchall()
    paper_info = {}
    for row in papers:
        pid = row["id"]
        paper_info[int(pid)] = {
            "citation_count": row["citation_count"] or 0,
            "year": row["year"] or 2020,
            "keywords": row["keywords"] or "[]",
        }
    total_items = len(paper_info)
    print(f"  total papers: {total_items}")

    # 用确定性哈希构建简单论文向量 (32-dim)
    def paper_hash_vec(pid, dim=32):
        seed = hash(f"paper_{pid}") % (2**31)
        rng = np.random.default_rng(seed)
        v = rng.standard_normal(dim).astype(np.float32)
        return v / (np.linalg.norm(v) + 1e-8)

    paper_vecs = {pid: paper_hash_vec(pid) for pid in paper_info}

    # 构建用户画像: 加权池化
    action_weight = {"click": 0.5, "read": 1.0, "favorite": 2.0}
    user_vecs = {}
    for uid in user_train_papers:
        vec = np.zeros(32, dtype=np.float32)
        for pid, act in zip(user_train_papers[uid], user_train_actions[uid]):
            w = action_weight.get(act, 0.5)
            vec += w * paper_vecs.get(pid, np.zeros(32))
        vec /= (np.linalg.norm(vec) + 1e-8)
        user_vecs[uid] = vec

    # 5. 对每个测试用户生成 Top-10 推荐 (cosine 排序)
    print("Generating Top-10 recommendations...")
    recommended = {}
    all_pids = list(paper_info.keys())
    all_paper_matrix = np.stack([paper_vecs[pid] for pid in all_pids])

    for uid in actual:
        if uid not in user_vecs:
            continue
        uv = user_vecs[uid]
        cos_sims = np.dot(all_paper_matrix, uv)
        top_k_idx = np.argsort(-cos_sims)[:10]
        recommended[uid] = [all_pids[i] for i in top_k_idx]

    # 6. 计算指标
    metrics = compute_metrics(recommended, actual, K=10, total_items=total_items)
    print("\n" + "=" * 50)
    print("  Evaluation Results")
    print("=" * 50)
    for k, v in metrics.items():
        print(f"  {k:18s}: {v}")
    print("=" * 50)

    mysql.close()
    return metrics


if __name__ == "__main__":
    main()
