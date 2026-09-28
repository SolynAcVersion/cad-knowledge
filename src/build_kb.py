# -*- coding: utf-8 -*-
"""
知识库站点生成器 v2
- 扫描 notes/ 目录下的 HTML 笔记（支持子目录 + 图片等资源）
- 自动生成索引首页 index.html（卡片 + 搜索 + 分类）
- 可直接推送到 GitHub Pages
"""
import json
import html
import re
import shutil
from pathlib import Path
from datetime import datetime
BASE = Path(r"C:\Users\songsongyu\aipywork\9")
NOTES_DIR = BASE / "notes"
SITE_DIR = BASE / "site"
NOTES_DIR.mkdir(parents=True, exist_ok=True)
SITE_DIR.mkdir(parents=True, exist_ok=True)
def extract_meta(fp: Path):
    """从 HTML 中提取标题和摘要"""
    raw = fp.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.I | re.S)
    title = html.unescape(m.group(1).strip()) if m else fp.stem
    if not title:
        title = fp.stem
    if title == fp.stem:
        m1 = re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.I | re.S)
        if m1:
            title = html.unescape(re.sub(r"<[^>]+>", "", m1.group(1)).strip())
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.I | re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    body = html.unescape(re.sub(r"\s+", " ", body)).strip()
    summary = body[:120] + ("…" if len(body) > 120 else "")
    category = fp.parent.name if fp.parent != NOTES_DIR else "未分类"
    return {
        "file": fp.name,
        "rel": str(fp.relative_to(NOTES_DIR)).replace("\\", "/"),
        "title": title,
        "summary": summary,
        "category": category,
        "mtime": datetime.fromtimestamp(fp.stat().st_mtime).strftime("%Y-%m-%d"),
        "size": fp.stat().st_size,
    }
def build():
    files = sorted(NOTES_DIR.rglob("*.html"))
    items = [extract_meta(f) for f in files]
    # 整体镜像 notes/ -> site/notes/（含图片等所有资源）
    dst_notes = SITE_DIR / "notes"
    if dst_notes.exists():
        shutil.rmtree(dst_notes, ignore_errors=True)
    shutil.copytree(NOTES_DIR, dst_notes)
    data_json = json.dumps(items, ensure_ascii=False)
    index_html = INDEX_TEMPLATE.replace("__DATA__", data_json)
    (SITE_DIR / "index.html").write_text(index_html, encoding="utf-8")
    (SITE_DIR / ".nojekyll").write_text("", encoding="utf-8")
    print(f"[OK] 共索引 {len(items)} 篇笔记 -> {SITE_DIR / 'index.html'}")
    for it in items:
        print("   -", it["category"], "|", it["title"])
    return items
INDEX_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CAD 知识库</title>
<style>
:root{
  --bg:#f7f8fa; --card:#ffffff; --ink:#1a1d24; --sub:#6b7280;
  --line:#e6e8ec; --accent:#2f6bff; --accent-soft:#eaf0ff;
  --shadow:0 1px 2px rgba(16,24,40,.04),0 8px 24px rgba(16,24,40,.06);
}
*{box-sizing:border-box;margin:0;padding:0}
body{
  font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif;
  background:var(--bg); color:var(--ink); line-height:1.65;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1120px;margin:0 auto;padding:56px 24px 96px}
header{margin-bottom:40px}
.eyebrow{
  display:inline-block;font-size:12px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--accent);background:var(--accent-soft);
  padding:5px 12px;border-radius:999px;font-weight:600;margin-bottom:18px;
}
h1{font-size:clamp(30px,4.4vw,46px);letter-spacing:-.02em;font-weight:800;line-height:1.15}
h1 span{color:var(--accent)}
.sub{color:var(--sub);margin-top:12px;font-size:15px}
.toolbar{
  display:flex;gap:12px;flex-wrap:wrap;align-items:center;
  margin:32px 0 28px;padding:14px;background:var(--card);
  border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);
}
.search{
  flex:1;min-width:220px;display:flex;align-items:center;gap:10px;
  background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:9px 14px;
  transition:border-color .2s,box-shadow .2s;
}
.search:focus-within{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.search input{border:0;background:transparent;outline:none;font:inherit;width:100%;color:var(--ink)}
.search svg{flex:none;opacity:.45}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.chip{
  border:1px solid var(--line);background:var(--card);color:var(--sub);
  padding:7px 14px;border-radius:999px;font-size:13px;cursor:pointer;
  transition:all .18s;font-family:inherit;
}
.chip:hover{border-color:var(--accent);color:var(--accent)}
.chip.on{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px}
.card{
  display:flex;flex-direction:column;background:var(--card);
  border:1px solid var(--line);border-radius:16px;padding:22px;
  text-decoration:none;color:inherit;box-shadow:var(--shadow);
  transition:transform .22s cubic-bezier(.2,.8,.2,1),box-shadow .22s,border-color .22s;
  position:relative;overflow:hidden;
}
.card::before{
  content:"";position:absolute;inset:0 auto 0 0;width:3px;
  background:var(--accent);transform:scaleY(0);transform-origin:top;
  transition:transform .28s cubic-bezier(.2,.8,.2,1);
}
.card:hover{transform:translateY(-4px);border-color:#d6ddf0;
  box-shadow:0 4px 8px rgba(16,24,40,.05),0 18px 40px rgba(16,24,40,.10)}
.card:hover::before{transform:scaleY(1)}
.tag{
  align-self:flex-start;font-size:11px;font-weight:700;letter-spacing:.06em;
  color:var(--accent);background:var(--accent-soft);
  padding:4px 10px;border-radius:6px;margin-bottom:14px;
}
.card h3{font-size:17px;font-weight:700;letter-spacing:-.01em;margin-bottom:9px;line-height:1.4}
.card p{font-size:13.5px;color:var(--sub);flex:1;
  display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.meta{
  display:flex;justify-content:space-between;align-items:center;
  margin-top:18px;padding-top:14px;border-top:1px solid var(--line);
  font-size:12px;color:var(--sub);
}
.arrow{color:var(--accent);font-weight:700;transition:transform .22s}
.card:hover .arrow{transform:translateX(4px)}
.empty{
  grid-column:1/-1;text-align:center;padding:80px 20px;color:var(--sub);
  background:var(--card);border:1px dashed var(--line);border-radius:16px;
}
footer{
  text-align:center;margin-top:64px;padding-top:28px;
  border-top:1px solid var(--line);color:var(--sub);font-size:12.5px;
}
footer a{color:var(--accent);text-decoration:none}
@media(max-width:600px){.wrap{padding:36px 16px 72px}.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="eyebrow">Knowledge Base</div>
    <h1>CAD <span>知识库</span></h1>
    <p class="sub" id="stat">加载中…</p>
  </header>
  <div class="toolbar">
    <label class="search">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
        <circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>
      </svg>
      <input id="q" type="search" placeholder="搜索标题、摘要或分类…">
    </label>
    <div class="chips" id="chips"></div>
  </div>
  <div class="grid" id="grid"></div>
  <footer>
    Generated by <a href="https://www.aipyaipy.com" target="_blank">AiPy</a> · 本地数据处理，不上传任何信息
  </footer>
</div>
<script>
const DATA = __DATA__;
const grid = document.getElementById('grid');
const chips = document.getElementById('chips');
const q = document.getElementById('q');
const stat = document.getElementById('stat');
let curCat = 'ALL';
const cats = ['ALL', ...Array.from(new Set(DATA.map(d => d.category)))];
cats.forEach(c => {
  const b = document.createElement('button');
  b.className = 'chip' + (c === 'ALL' ? ' on' : '');
  b.textContent = c === 'ALL' ? '全部' : c;
  b.onclick = () => {
    curCat = c;
    [...chips.children].forEach(x => x.classList.toggle('on', x === b));
    render();
  };
  chips.appendChild(b);
});
function esc(s){
  return String(s).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}
function render(){
  const kw = q.value.trim().toLowerCase();
  const list = DATA.filter(d => {
    const okCat = curCat === 'ALL' || d.category === curCat;
    const okKw = !kw || (d.title + d.summary + d.category).toLowerCase().includes(kw);
    return okCat && okKw;
  });
  stat.textContent = '共 ' + DATA.length + ' 篇笔记' + (list.length !== DATA.length ? '，筛选出 ' + list.length + ' 篇' : '');
  if (!list.length){
    grid.innerHTML = '<div class="empty">没有找到匹配的笔记 🔍</div>';
    return;
  }
  grid.innerHTML = list.map(d => `
    <a class="card" href="notes/${encodeURI(d.rel)}" target="_blank">
      <span class="tag">${esc(d.category)}</span>
      <h3>${esc(d.title)}</h3>
      <p>${esc(d.summary) || '暂无摘要'}</p>
      <div class="meta">
        <span>${esc(d.mtime)}</span>
        <span class="arrow">阅读 →</span>
      </div>
    </a>`).join('');
}
q.addEventListener('input', render);
render();
</script>
</body>
</html>
"""
if __name__ == "__main__":
    build()