"""
为 docs/QA_*.md 文件的每个 Q# 条目添加 Obsidian 兼容的标签和 wikilink 元数据。
运行: python scripts/tag_qa.py
"""
import re, os

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

# ── 每个 Q# 条目的标签和关联 ──────────────────────────────────────────
QA_META = {
    # v1
    "Q0": (["#架构", "#技术栈"], ["[[Q4]]", "[[Q29]]", "[[Q45]]"]),
    "Q2": (["#推荐", "#主链路", "#Python服务"], ["[[Q5]]", "[[Q16]]", "[[Q42]]", "[[Q47]]"]),
    "Q3": (["#私信", "#WebSocket", "#STOMP"], ["[[Q40]]"]),
    "Q4": (["#业务功能", "#用户流程"], ["[[Q0]]", "[[Q8]]"]),
    "Q5": (["#Actor-Critic", "#RL", "#强化学习"], ["[[Q20]]", "[[Q25]]", "[[Q38]]", "[[Q49]]"]),
    "Q5追问": None,  # 由标题内容动态区分，见 process_file
    "Q11": (["#代码审计", "#BUG", "#死代码"], ["[[Q12]]"]),
    "Q12": (["#BUG修复", "#hash碰撞", "#KG-reward"], ["[[Q11]]"]),
    "Q13": (["#KG-RL协同", "#评估指标", "#MDP"], ["[[Q5]]", "[[Q7]]", "[[Q46]]"]),
    "Q6": (["#学习路径", "#可视化"], ["[[Q28]]", "[[Q39]]"]),
    "Q7": (["#Neo4j", "#图数据库", "#知识图谱"], ["[[Q19]]", "[[Q27]]", "[[Q44]]"]),
    "Q8": (["#流程图", "#用例", "#业务流程"], ["[[Q4]]"]),
    "Q9": (["#学习路径", "#可视化", "#3D"], ["[[Q6]]", "[[Q28]]"]),
    "Q10": (["#数据库", "#表结构", "#外键"], ["[[Q21]]", "[[Q31]]", "[[Q44]]"]),
    "Q14": (["#论文向量", "#去随机化", "#特征工程"], ["[[Q18]]", "[[Q33]]", "[[Q48]]"]),
    "Q16": (["#排序", "#归一化", "#质量门控"], ["[[Q22]]", "[[Q23]]", "[[Q42]]", "[[Q43]]"]),
    # v2
    "Q17": (["#前端", "#状态管理", "#Pinia"], ["[[Q41]]"]),
    "Q18": (["#特征工程", "#向量维度", "#用户状态"], ["[[Q14]]", "[[Q33]]", "[[Q36]]"]),
    "Q19": (["#知识图谱", "#投影矩阵", "#嵌入"], ["[[Q7]]", "[[Q27]]"]),
    "Q20": (["#Actor-Critic", "#梯度下降", "#训练"], ["[[Q5]]", "[[Q25]]", "[[Q38]]"]),
    "Q21": (["#数据库", "#设计范式", "#评估"], ["[[Q10]]", "[[Q31]]", "[[Q32]]"]),
    "Q22": (["#排序", "#Actor", "#评分"], ["[[Q16]]", "[[Q23]]", "[[Q42]]"]),
    "Q23": (["#排序", "#归一化", "#质量门控"], ["[[Q16]]", "[[Q22]]", "[[Q43]]"]),
    "Q24": (["#Actor", "#网络结构", "#推理"], ["[[Q5]]", "[[Q25]]", "[[Q42]]"]),
    "Q25": (["#Actor", "#Critic", "#训练"], ["[[Q20]]", "[[Q24]]", "[[Q38]]"]),
    "Q26": (["#RL", "#动作空间", "#候选集"], ["[[Q5]]", "[[Q42]]"]),
    "Q27": (["#知识图谱", "#拓扑", "#张量"], ["[[Q7]]", "[[Q19]]"]),
    "Q28": (["#学习路径", "#掌握度", "#3D可视化"], ["[[Q6]]", "[[Q9]]", "[[Q39]]"]),
    "Q29": (["#架构", "#三端", "#模块"], ["[[Q0]]", "[[Q35]]", "[[Q45]]"]),
    "Q30": (["#异步", "#线程池", "#可靠性"], ["[[Q2]]"]),
    "Q31": (["#数据库", "#FK", "#索引"], ["[[Q10]]", "[[Q21]]", "[[Q32]]"]),
    "Q32": (["#数据库", "#整改", "#迁移"], ["[[Q21]]", "[[Q31]]"]),
    "Q33": (["#特征工程", "#兴趣向量", "#维度"], ["[[Q18]]", "[[Q36]]"]),
    "Q34": (["#异步", "#线程池", "#可靠性"], ["[[Q30]]"]),
    "Q35": (["#架构", "#代码文档", "#函数级"], ["[[Q29]]"]),
    "Q36": (["#特征工程", "#行为向量", "#KG向量"], ["[[Q18]]", "[[Q33]]"]),
    "Q37": (["#安全", "#密码", "#BCrypt"], ["[[Q44]]"]),
    # v3
    "Q38": (["#Actor-Critic", "#RL训练", "#TD误差"], ["[[Q5]]", "[[Q20]]", "[[Q49]]"]),
    "Q39": (["#学习路径", "#掌握度传播", "#四层节点"], ["[[Q6]]", "[[Q28]]"]),
    "Q40": (["#私信", "#WebSocket", "#STOMP", "#代码实现"], ["[[Q3]]"]),
    "Q41": (["#前端", "#CSS", "#样式系统"], ["[[Q17]]"]),
    "Q42": (["#推荐", "#打分", "#完整流程"], ["[[Q2]]", "[[Q16]]", "[[Q22]]", "[[Q24]]", "[[Q47]]"]),
    "Q43": (["#排序", "#余弦相似度", "#评分计算"], ["[[Q16]]", "[[Q22]]", "[[Q42]]"]),
    "Q44": (["#数据库", "#表结构", "#字段"], ["[[Q10]]", "[[Q21]]"]),
    "Q45": (["#架构", "#包图", "#依赖"], ["[[Q0]]", "[[Q29]]"]),
    "Q46": (["#KG-RL协同", "#评估指标", "#MDP"], ["[[Q7]]", "[[Q5]]"]),
    # v4
    "Q47": (["#推荐", "#公式", "#LaTeX"], ["[[Q2]]", "[[Q42]]"]),
    "Q48": (["#特征工程", "#手工特征", "#MySQL"], ["[[Q14]]", "[[Q18]]"]),
    "Q49": (["#Actor-Critic", "#训练", "#逐行解析"], ["[[Q5]]", "[[Q20]]", "[[Q38]]"]),
    "Q50": (["#RL应用", "#可解释性", "#合作者匹配"], ["[[Q46]]"]),
    "Q51": (["#伪代码", "#特征构建", "#融合排序"], ["[[Q2]]", "[[Q5]]", "[[Q47]]"]),
}

Q_LINE_RE = re.compile(r'^## (Q\d+(?:追问)?)[：:]\s*(.+)', re.MULTILINE)

TOPIC_CLUSTERS = {
    "🏗️ 架构概览": ["Q0", "Q4", "Q8", "Q29", "Q35", "Q45"],
    "🎯 推荐排序": ["Q2", "Q16", "Q22", "Q23", "Q42", "Q43", "Q47", "Q51"],
    "🧠 Actor-Critic / RL训练": ["Q5", "Q5追问", "Q20", "Q24", "Q25", "Q26", "Q38", "Q49"],
    "📐 特征工程": ["Q14", "Q18", "Q33", "Q36", "Q48"],
    "🕸️ 知识图谱 / Neo4j": ["Q7", "Q19", "Q27", "Q46"],
    "📚 学习路径": ["Q6", "Q9", "Q28", "Q39"],
    "🗄️ 数据库设计": ["Q10", "Q21", "Q31", "Q32", "Q44"],
    "🎨 前端": ["Q17", "Q41"],
    "💬 私信 / WebSocket": ["Q3", "Q40"],
    "🔐 安全": ["Q37"],
    "⚡ 异步与可靠性": ["Q30", "Q34"],
    "🧪 可解释性与评估": ["Q50"],
    "🔍 代码审计与质量": ["Q11", "Q12"],
    "📊 理论基础": ["Q13", "Q46"],
}


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    modified = False
    # Find all Q# headings and insert metadata after each
    lines = content.split("\n")
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        # Check if this is a Q# heading
        m = Q_LINE_RE.match(line.strip())
        if m:
            q_id = m.group(1).strip()
            title = m.group(2).strip()
            if q_id in QA_META:
                meta = QA_META[q_id]
                # Q5追问: 根据标题内容区分包图 vs 算法伪代码
                if q_id == "Q5追问":
                    if "包图" in title or "模块" in title:
                        tags, related = ["#包图", "#Python模块", "#依赖"], ["[[Q5]]", "[[Q45]]"]
                    elif "伪代码" in title or "算法" in title:
                        tags, related = ["#算法", "#伪代码", "#推荐流程"], ["[[Q5]]", "[[Q2]]", "[[Q51]]"]
                    else:
                        tags, related = ["#架构", "#RL"], ["[[Q5]]"]
                else:
                    tags, related = meta
                tag_str = " ".join(tags)
                rel_str = ", ".join(related)
                new_lines.append("")
                new_lines.append(f"**标签**: {tag_str}")
                new_lines.append(f"**关联**: {rel_str}")
                modified = True
        i += 1

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines))
        print(f"  OK {os.path.basename(filepath)}")
    else:
        print(f"  -  {os.path.basename(filepath)} (no changes)")


def build_index():
    """生成 docs/索引.md MOC 文件"""
    lines = [
        "# QA 主题索引",
        "",
        "> 本文件是全部 QA 问答的内容地图（Map of Content）。点击任意 Q# 跳转至对应问答。",
        "> 在 Obsidian 中打开 `docs/` 作为 Vault 后，可按 `Ctrl+O` 快速跳转、图视图查看引用网络。",
        "",
        "---",
        "",
    ]

    for cluster, q_ids in TOPIC_CLUSTERS.items():
        lines.append(f"## {cluster}")
        lines.append("")
        for q_id in q_ids:
            if q_id in QA_META and QA_META[q_id] is not None:
                tags, _ = QA_META[q_id]
                tag_str = " ".join(tags)
                lines.append(f"- **[[{q_id}]]** — {tag_str}")
            elif q_id == "Q5追问":
                lines.append(f"- **[[{q_id}]]** — #包图 #算法 (双条目)")
            else:
                lines.append(f"- **{q_id}**")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 文件索引")
    lines.append("")
    lines.append("| 文件 | Q# 范围 |")
    lines.append("|------|---------|")
    lines.append("| `QA_2026-05-16_2026-06-02_v1.md` | Q0 – Q16 |")
    lines.append("| `QA_2026-06-02_2026-06-05_v2.md` | Q17 – Q37 |")
    lines.append("| `QA_2026-06-07_2026-06-08_v3.md` | Q38 – Q46 |")
    lines.append("| `QA_2026-06-08_v4.md` | Q47 – Q51 |")
    lines.append("")
    lines.append("> 最后更新: 2026-06-11")

    index_path = os.path.join(DOCS, "索引.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  ✓ 索引.md ({len(TOPIC_CLUSTERS)} 个主题簇)")


if __name__ == "__main__":
    qa_files = [
        "QA_2026-05-16_2026-06-02_v1.md",
        "QA_2026-06-02_2026-06-05_v2.md",
        "QA_2026-06-07_2026-06-08_v3.md",
        "QA_2026-06-08_v4.md",
    ]
    print("添加标签与 wikilink...")
    for fname in qa_files:
        process_file(os.path.join(DOCS, fname))
    print("\n生成 MOC 索引...")
    build_index()
    print("\n完成。")
