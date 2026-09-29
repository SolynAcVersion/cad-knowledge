#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库投稿工具：传入一个 HTML 笔记，自动归档、更新首页并推送到 GitHub fork。

用法:
    python3 src/add_note.py <笔记.html> [分类] [选项]

示例:
    python3 src/add_note.py ~/demo.html CAD调研
    python3 src/add_note.py ~/demo.html 技术笔记 --icon 🧪 --dry-run
    python3 src/add_note.py ~/demo.html 新分类名          # 不存在的分类会自动建分区

行为:
    1. 复制笔记到 notes/<分类>/文件名
    2. 从 <title>/<h1> 提取标题，从正文提取摘要，在 index.html 对应分类插入卡片
    3. git commit（风格与仓库历史一致）并 push 到 origin main
"""
import argparse
import html as htmllib
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTES_DIR = ROOT / "notes"
INDEX = ROOT / "index.html"

DEFAULT_ICONS = {
    "AI技术": "🧠",
    "CAD调研": "📐",
    "技术笔记": "🛠️",
    "读书笔记": "📖",
}
DEFAULT_CATEGORY = "技术笔记"
PAGES_BASE = "https://solynacversion.github.io/cad-knowledge"


def extract_meta(fp: Path):
    """从 HTML 里提取标题和摘要，规则与 src/build_kb.py 保持一致。"""
    raw = fp.read_text(encoding="utf-8", errors="ignore")
    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.I | re.S)
    if m:
        title = htmllib.unescape(m.group(1)).strip()
    if not title:
        m1 = re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.I | re.S)
        if m1:
            title = htmllib.unescape(re.sub(r"<[^>]+>", "", m1.group(1))).strip()
    if not title:
        title = fp.stem

    body = re.sub(r"<head[^>]*>.*?</head>", " ", raw, flags=re.I | re.S)
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", body, flags=re.I | re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    body = htmllib.unescape(re.sub(r"\s+", " ", body)).strip()
    summary = body[:80] + ("…" if len(body) > 80 else "")
    return title, summary


def find_section(index_html: str, category: str):
    """返回 (分类区块的起始位置, 该分类 cards 容器闭合 </div> 的位置)。"""
    for m in re.finditer(
        r'<div class="section">\s*<h2>(.*?)</h2>\s*<div class="cards">', index_html
    ):
        h2_plain = re.sub(r"\s", "", htmllib.unescape(m.group(1)))
        if re.sub(r"\s", "", category) in h2_plain:
            close = index_html.index("</div>", m.end())
            return m.start(), close
    return None


def build_card(category: str, filename: str, title: str, summary: str, icon: str) -> str:
    return (
        f'      <a class="card" href="notes/{category}/{filename}">\n'
        f"        <span class=\"icon\">{icon}</span>\n"
        f"        <h3>{htmllib.escape(title)}</h3>\n"
        f"        <p>{htmllib.escape(summary)}</p>\n"
        f"      </a>\n"
    )


def insert_card(index_html: str, category: str, card: str):
    """把卡片插进对应分类；分类不存在时在 </main> 前新建分区。返回新 index 内容。"""
    hit = find_section(index_html, category)
    if hit:
        start, close = hit
        line_start = index_html.rfind("\n", 0, close) + 1
        return index_html[:line_start] + card + index_html[line_start:]
    section = (
        f'  <div class="section">\n'
        f"    <h2>{htmllib.escape(category)}</h2>\n"
        f'    <div class="cards">\n'
        f"{card}"
        f"    </div>\n"
        f"  </div>\n"
    )
    return index_html.replace("</main>", section + "</main>")


def run(cmd, **kw):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        sys.exit(f"[失败] 命令出错: {' '.join(cmd)}")
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser(description="把 HTML 笔记加入知识库并推送到 GitHub")
    ap.add_argument("file", help="要收录的 HTML 文件")
    ap.add_argument("category", nargs="?", default=DEFAULT_CATEGORY,
                    help=f"分类名（默认 {DEFAULT_CATEGORY}；现有: {'、'.join(DEFAULT_ICONS)}）")
    ap.add_argument("--icon", default=None, help="卡片图标 emoji（默认按分类选择）")
    ap.add_argument("--dry-run", action="store_true", help="只预览将要做的改动，不写文件不提交")
    ap.add_argument("--no-push", action="store_true", help="只本地 commit，不 push")
    args = ap.parse_args()

    src = Path(args.file).expanduser().resolve()
    if not src.is_file():
        sys.exit(f"[失败] 找不到文件: {src}")

    icon = args.icon or DEFAULT_ICONS.get(args.category, "📄")
    dest = NOTES_DIR / args.category / src.name
    if dest.exists() and not args.dry_run:
        sys.exit(f"[失败] 目标已存在: {dest}（换个文件名或先删除旧文件）")

    title, summary = extract_meta(src)
    card = build_card(args.category, src.name, title, summary, icon)
    commit_msg = f"feat: 新增 {title}（归入 {args.category} 分类）"

    if args.dry_run:
        print(f"[预览] 复制  {src} -> notes/{args.category}/{src.name}")
        print(f"[预览] 提交  {commit_msg}")
        print(f"[预览] 推送  origin main" + ("（--no-push 跳过）" if args.no_push else ""))
        print(f"[预览] 首页卡片:\n{card}")
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    INDEX.write_text(insert_card(INDEX.read_text(encoding="utf-8"), args.category, card),
                     encoding="utf-8")

    run(["git", "add", "-A"])
    run(["git", "commit", "-m", commit_msg])
    print(f"[OK] 已提交: {commit_msg}")

    if not args.no_push:
        run(["git", "push", "origin", "main"])
        print(f"[OK] 已推送到 origin main")
        print(f"     本地预览: http://127.0.0.1:8080/notes/{args.category}/{src.name}")
        print(f"     Pages 地址（稍等一两分钟部署）: {PAGES_BASE}/notes/{args.category}/{src.name}")
    else:
        print("[OK] 已跳过 push（--no-push）")


if __name__ == "__main__":
    main()
