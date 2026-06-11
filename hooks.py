"""
MkDocs 构建钩子：转换 Obsidian 格式到 MkDocs 格式。
  1. 标题行的 ^qN 块锚点 → {#qN} MkDocs 锚点
  2. [[file#^qN|QN]] wikilink → [QN](file.md#qN) 标准链接

源文件保持 Obsidian 兼容，仅在构建时转换。
"""
import re

# [[file#^anchor|display]]
WIKILINK_RE = re.compile(r'\[\[([a-zA-Z0-9_./-]+)#\^([a-zA-Z0-9_-]+)\|([^\]]+)\]\]')
# ^block-id at end of heading line
BLOCK_ANCHOR_RE = re.compile(r'\s*\^([a-zA-Z0-9_-]+)\s*$', re.MULTILINE)


def on_page_markdown(markdown, page, config, files):
    """在 MkDocs 处理 markdown 之前执行。"""

    # Step 1: ^q5 → {#q5}
    def replace_block_anchor(m):
        anchor = m.group(1)
        return f' {{#{anchor}}}'

    markdown = BLOCK_ANCHOR_RE.sub(replace_block_anchor, markdown)

    # Step 2: [[file#^anchor|text]] → [text](file.md#anchor)
    def replace_wikilink(m):
        fname = m.group(1)
        anchor = m.group(2)
        text = m.group(3)
        if not fname.endswith('.md'):
            fname += '.md'
        return f'[{text}]({fname}#{anchor})'

    markdown = WIKILINK_RE.sub(replace_wikilink, markdown)

    return markdown
