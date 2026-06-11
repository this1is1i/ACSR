"""
修复 Obsidian wikilink 兼容性：
  1. 每个 Q# 标题行末尾追加 ^qN 块锚点（Obsidian 块引用）
  2. [[QN]] → [[filename#^qN|QN]]（跨文件可点击）

运行: python scripts/fix_obsidian_links.py
"""
import re, os

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

# Q# → 所在文件名
QA_FILES = {
    "Q0":  "QA_2026-05-16_2026-06-02_v1", "Q2": "QA_2026-05-16_2026-06-02_v1",
    "Q3":  "QA_2026-05-16_2026-06-02_v1", "Q4": "QA_2026-05-16_2026-06-02_v1",
    "Q5":  "QA_2026-05-16_2026-06-02_v1", "Q6": "QA_2026-05-16_2026-06-02_v1",
    "Q7":  "QA_2026-05-16_2026-06-02_v1", "Q8": "QA_2026-05-16_2026-06-02_v1",
    "Q9":  "QA_2026-05-16_2026-06-02_v1", "Q10":"QA_2026-05-16_2026-06-02_v1",
    "Q11": "QA_2026-05-16_2026-06-02_v1", "Q12":"QA_2026-05-16_2026-06-02_v1",
    "Q13": "QA_2026-05-16_2026-06-02_v1", "Q14":"QA_2026-05-16_2026-06-02_v1",
    "Q16": "QA_2026-05-16_2026-06-02_v1",
    "Q17": "QA_2026-06-02_2026-06-05_v2", "Q18":"QA_2026-06-02_2026-06-05_v2",
    "Q19": "QA_2026-06-02_2026-06-05_v2", "Q20":"QA_2026-06-02_2026-06-05_v2",
    "Q21": "QA_2026-06-02_2026-06-05_v2", "Q22":"QA_2026-06-02_2026-06-05_v2",
    "Q23": "QA_2026-06-02_2026-06-05_v2", "Q24":"QA_2026-06-02_2026-06-05_v2",
    "Q25": "QA_2026-06-02_2026-06-05_v2", "Q26":"QA_2026-06-02_2026-06-05_v2",
    "Q27": "QA_2026-06-02_2026-06-05_v2", "Q28":"QA_2026-06-02_2026-06-05_v2",
    "Q29": "QA_2026-06-02_2026-06-05_v2", "Q30":"QA_2026-06-02_2026-06-05_v2",
    "Q31": "QA_2026-06-02_2026-06-05_v2", "Q32":"QA_2026-06-02_2026-06-05_v2",
    "Q33": "QA_2026-06-02_2026-06-05_v2", "Q34":"QA_2026-06-02_2026-06-05_v2",
    "Q35": "QA_2026-06-02_2026-06-05_v2", "Q36":"QA_2026-06-02_2026-06-05_v2",
    "Q37": "QA_2026-06-02_2026-06-05_v2",
    "Q38": "QA_2026-06-07_2026-06-08_v3", "Q39":"QA_2026-06-07_2026-06-08_v3",
    "Q40": "QA_2026-06-07_2026-06-08_v3", "Q41":"QA_2026-06-07_2026-06-08_v3",
    "Q42": "QA_2026-06-07_2026-06-08_v3", "Q43":"QA_2026-06-07_2026-06-08_v3",
    "Q44": "QA_2026-06-07_2026-06-08_v3", "Q45":"QA_2026-06-07_2026-06-08_v3",
    "Q46": "QA_2026-06-07_2026-06-08_v3",
    "Q47": "QA_2026-06-08_v4", "Q48":"QA_2026-06-08_v4",
    "Q49": "QA_2026-06-08_v4", "Q50":"QA_2026-06-08_v4",
    "Q51": "QA_2026-06-08_v4",
}

# Q# 标题行: ## Q42: 标题（日期）（git: hash）
HEADING_RE = re.compile(r'^(#{1,6}\s+)(Q\d+(?:追问)?)([：:].+)$')
# 孤立 wikilink: [[Q42]] 或 [[Q5追问]]
BARE_WIKILINK_RE = re.compile(r'\[\[(Q\d+(?:追问)?)\]\]')

def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    new_lines = []
    modified = False

    for line in lines:
        # Step 1: 给 Q# 标题加 ^qN 块锚点（如果还没有）
        m = HEADING_RE.match(line.strip())
        if m:
            prefix = m.group(1)
            q_id = m.group(2)
            rest = m.group(3)
            anchor = 'q5-ask' if '追问' in q_id else q_id.lower()
            # 检查是否已有锚点
            if '^' not in line.split('（')[0] if '（' in line else line:
                line = f'{prefix}{q_id}{rest} ^{anchor}'
                modified = True

        new_lines.append(line)

    if not modified:
        print(f"  -  {os.path.basename(filepath)} (no heading changes)")
        return

    content = "\n".join(new_lines)

    # Step 2: 替换孤立 [[QN]] → [[filename#^qN|QN]]
    def replace_wikilink(m):
        q_id = m.group(1)
        if q_id not in QA_FILES:
            return m.group(0)
        fname = QA_FILES[q_id]
        anchor = 'q5-ask' if '追问' in q_id else q_id.lower()
        return f'[[{fname}#^{anchor}|{q_id}]]'

    content = BARE_WIKILINK_RE.sub(replace_wikilink, content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  OK {os.path.basename(filepath)}")


def rebuild_index():
    """重新生成 索引.md，wikilink 使用 Obsidian 兼容格式。"""
    clusters = {
        "Arch 架构概览": ["Q0","Q4","Q8","Q29","Q35","Q45"],
        "Rec 推荐排序": ["Q2","Q16","Q22","Q23","Q42","Q43","Q47","Q51"],
        "RL Actor-Critic": ["Q5","Q20","Q24","Q25","Q26","Q38","Q49"],
        "Feat 特征工程": ["Q14","Q18","Q33","Q36","Q48"],
        "KG 知识图谱": ["Q7","Q19","Q27","Q46"],
        "Path 学习路径": ["Q6","Q9","Q28","Q39"],
        "DB 数据库": ["Q10","Q21","Q31","Q32","Q44"],
        "FE 前端": ["Q17","Q41"],
        "Msg 私信": ["Q3","Q40"],
        "Sec 安全": ["Q37"],
        "Async 异步": ["Q30","Q34"],
        "Eval 评估": ["Q50"],
        "Audit 审计": ["Q11","Q12"],
        "Theory 理论": ["Q13","Q46"],
    }

    lines = [
        "# QA 主题索引",
        "",
        "> 全部 QA 问答的内容地图。点击 Q# 跳转到对应问答的精确位置。",
        "> 在 Obsidian 中 `Ctrl+鼠标悬停` 可预览，`Ctrl+点击` 在新标签页打开。",
        "",
        "---",
        "",
    ]

    for cluster, q_ids in clusters.items():
        lines.append(f"## {cluster}")
        lines.append("")
        for q_id in q_ids:
            if q_id in QA_FILES:
                fname = QA_FILES[q_id]
                anchor = 'q5-ask' if '追问' in q_id else q_id.lower()
                lines.append(f"- [[{fname}#^{anchor}|{q_id}]]")
            else:
                lines.append(f"- {q_id}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 文件索引")
    lines.append("")
    lines.append("| 文件 | Q# |")
    lines.append("|------|-----|")
    lines.append("| QA_2026-05-16_2026-06-02_v1 | Q0–Q16 |")
    lines.append("| QA_2026-06-02_2026-06-05_v2 | Q17–Q37 |")
    lines.append("| QA_2026-06-07_2026-06-08_v3 | Q38–Q46 |")
    lines.append("| QA_2026-06-08_v4 | Q47–Q51 |")
    lines.append("")
    lines.append("> 2026-06-11")

    index_path = os.path.join(DOCS, "索引.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  OK index ({len(clusters)} clusters)")


if __name__ == "__main__":
    qa_files = [
        "QA_2026-05-16_2026-06-02_v1.md",
        "QA_2026-06-02_2026-06-05_v2.md",
        "QA_2026-06-07_2026-06-08_v3.md",
        "QA_2026-06-08_v4.md",
    ]
    print("Step 1: add ^block anchors + fix wikilinks...")
    for fname in qa_files:
        process_file(os.path.join(DOCS, fname))
    print("\nStep 2: rebuild index...")
    rebuild_index()
    print("\nDone.")
