# -*- coding: utf-8 -*-
"""
知识库站点生成器 v3
- 分类侧边栏（带数量统计）
- 排序（最新/最早/标题）
- 最近更新区
- 实时搜索
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
        "ts": fp.stat().st_mtime,
        "size": fp.stat().st_size,
    }
def build():
    files = sorted(NOTES_DIR.rglob("*.html"))
    items = [extract_meta(f) for f in files]
    dst_notes = SITE_DIR / "notes"
    if dst_notes.exists():
        shutil.rmtree(dst_notes, ignore_errors=True)
    shutil.copytree(NOTES_DIR, SITE_DIR / "notes")
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
  --bg:#f6f7f9; --card:#ffffff; --ink:#171a21; --sub:#697280;
  --line:#e6e8ec; --accent:#2f6bff; --accent-soft:#eaf0ff;
  --shadow:0 1px 2px rgba(16,24,40,.04),0 8px 24px rgba(16,24,40,.06);
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif;
  background:var(--bg);color:var(--ink);line-height:1.65;-webkit-font-smoothing:antialiased}
.layout{max-width:1240px;margin:0 auto;padding:48px 24px 96px;
  display:grid;grid-template-columns:240px 1fr;gap:36px;align-items:start}
.sidebar{position:sticky;top:24px;background:var(--card);border:1px solid var(--line);
  border-radius:16px;padding:20px;box-shadow:var(--shadow)}
.side-title{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--sub);
  font-weight:700;margin-bottom:14px}
.cat{display:flex;align-items:center;justify-content:space-between;width:100%;
  padding:9px 12px;border:0;background:transparent;border-radius:9px;cursor:pointer;
  font:inherit;font-size:14px;color:var(--ink);transition:background .15s;text-align:left}
.cat:hover{background:var(--accent-soft)}
.cat.on{background:var(--accent);color:#fff;font-weight:600}
.cat .n{font-size:12px;opacity:.75;background:rgba(0,0,0,.06);border-radius:6px;
  padding:1px 8px;min-width:26px;text-align:center}
.cat.on .n{background:rgba(255,255,255,.25)}
.side-tip{margin-top:18px;padding-top:16px;border-top:1px solid var(--line);
  font-size:12px;color:var(--sub);line-height:1.7}
header{margin-bottom:28px}
.eyebrow{display:inline-block;font-size:12px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--accent);background:var(--accent-soft);padding:5px 12px;border-radius:999px;
  font-weight:600;margin-bottom:16px}
h1{font-size:clamp(28px,4vw,42px);letter-spacing:-.02em;font-weight:800}
h1 span{color:var(--accent)}
.sub{color:var(--sub);margin-top:10px;font-size:14.5px}
.toolbar{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:26px 0 24px}
.search{flex:1;min-width:200px;display:flex;align-items:center;gap:10px;
  background:var(--card);border:1px solid var(--line);border-radius:10px;padding:9px 14px;
  transition:border-color .2s,box-shadow .2s}
.search:focus-within{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.search input{border:0;background:transparent;outline:none;font:inherit;width:100%}
select{border:1px solid var(--line);background:var(--card);border-radius:10px;
  padding:9px 12px;font:inherit;font-size:13.5px;color:var(--ink);cursor:pointer}
.section-title{font-size:13px;font-weight:700;color:var(--sub);letter-spacing:.08em;
  text-transform:uppercase;margin:26px 0 14px;display:flex;align-items:center;gap:10px}
.section-title::after{content:"";flex:1;height:1px;background:var(--line)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:18px}
.card{display:flex;flex-direction:column;background:var(--card);border:1px solid var(--line);
  border-radius:16px;padding:20px;text-decoration:none;color:inherit;box-shadow:var(--shadow);
  transition:transform .22s cubic-bezier(.2,.8,.2,1),box-shadow .22s,border-color .22s;
  position:relative;overflow:hidden}
.card::before{content:"";position:absolute;inset:0 auto 0 0;width:3px;background:var(--accent);
  transform:scaleY(0);transform-origin:top;transition:transform .28s cubic-bezier(.2,.8,.2,1)}
.card:hover{transform:translateY(-4px);border-color:#d6ddf0;
  box-shadow:0 4px 8px rgba(16,24,40,.05),0 18px 40px rgba(16,24,40,.10)}
.card:hover::before{transform:scaleY(1)}
.tag{align-self:flex-start;font-size:11px;font-weight:700;letter-spacing:.06em;
  color:var(--accent);background:var(--accent-soft);padding:4px 10px;border-radius:6px;margin-bottom:12px}
.card h3{font-size:16.5px;font-weight:700;margin-bottom:8px;line-height:1.4}
.card p{font-size:13px;color:var(--sub);flex:1;display:-webkit-box;
  -webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.meta{display:flex;justify-content:space-between;margin-top:16px;padding-top:12px;
  border-top:1px solid var(--line);font-size:12px;color:var(--sub)}
.arrow{color:var(--accent);font-weight:700;transition:transform .22s}
.card:hover .arrow{transform:translateX(4px)}
.empty{grid-column:1/-1;text-align:center;padding:70px 20px;color:var(--sub);
  background:var(--card);border:1px dashed var(--line);border-radius:16px}
footer{text-align:center;margin-top:60px;padding-top:26px;border-top:1px solid var(--line);
  color:var(--sub);font-size:12.5px;grid-column:1/-1}
footer a{color:var(--accent);text-decoration:none}
@media(max-width:860px){
  .layout{grid-template-columns:1fr}
  .sidebar{position:static;display:flex;flex-wrap:wrap;gap:8px}
  .side-title{display:none}
  .cat{width:auto;padding:7px 12px;border:1px solid var(--line);border-radius:999px}
  .cat.on{border-color:var(--accent)}
  .side-tip{display:none}
}
</style>
</head>
<body>
<div class="layout">
  <aside class="sidebar" id="sidebar">
    <div class="side-title">📁 分类导航</div>
    <div id="cats"></div>
    <div class="side-tip">💡 新建分类只需在 notes/ 下新建文件夹，把笔记放进去即可自动生成分类。</div>
  </aside>
  <main>
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
      <select id="sort">
        <option value="new">🕐 最新优先</option>
        <option value="old">⏳ 最早优先</option>
        <option value="title">🔤 标题排序</option>
      </select>
    </div>
    <div id="recent-section">
      <div class="section-title">🆕 最近更新</div>
      <div class="grid" id="recent-grid"></div>
    </div>
    <div class="section-title">📚 全部笔记</div>
    <div class="grid" id="grid"></div>
    <footer>
      Generated by <a href="https://www.aipyaipy.com" target="_blank">AiPy</a> · 本地数据处理，不上传任何信息
    </footer>
  </main>
</div>
<script>
const DATA = __DATA__;
const catsEl = document.getElementById('cats');
const grid = document.getElementById('grid');
const recentGrid = document.getElementById('recent-grid');
const recentSection = document.getElementById('recent-section');
const q = document.getElementById('q');
const sortSel = document.getElementById('sort');
let curCat = 'ALL';
const counts = {};
DATA.forEach(d => counts[d.category] = (counts[d.category] || 0) + 1);
const cats = ['ALL', ...Object.keys(counts).sort()];
function esc(s){
  return String(s).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}
function renderCats(){
  catsEl.innerHTML = '';
  catsEl.appendChild(catBtn('ALL', '全部', DATA.length));
  cats.slice(1).forEach(c => catsEl.appendChild(catBtn(c, c, counts[c])));
}
function catBtn(key, label, n){
  const b = document.createElement('button');
  b.className = 'cat' + (key === curCat ? ' on' : '');
  b.innerHTML = '<span>' + esc(label) + '</span><span class="n">' + n + '</span>';
  b.onclick = () => { curCat = key; renderCats(); render(); };
  return b;
}
function card(d){
  return '<a class="card" href="notes/' + encodeURI(d.rel) + '" target="_blank">' +
    '<span class="tag">' + esc(d.category) + '</span>' +
    '<h3>' + esc(d.title) + '</h3>' +
    '<p>' + (esc(d.summary) || '暂无摘要') + '</p>' +
    '<div class="meta"><span>' + esc(d.mtime) + '</span><span class="arrow">阅读 →</span></div></a>';
}
function render(){
  const kw = q.value.trim().toLowerCase();
  let list = DATA.filter(d => {
    const okCat = curCat === 'ALL' || d.category === curCat;
    const okKw = !kw || (d.title + d.summary + d.category).toLowerCase().includes(kw);
    return okCat && okKw;
  });
  const sort = sortSel.value;
  if (sort === 'new') list.sort((a,b) => b.ts - a.ts);
  else if (sort === 'old') list.sort((a,b) => a.ts - b.ts);
  else list.sort((a,b) => a.title.localeCompare(b.title, 'zh'));
  document.getElementById('stat').textContent =
    '共 ' + DATA.length + ' 篇笔记 · ' + Object.keys(counts).length + ' 个分类' +
    (list.length !== DATA.length ? ' · 筛选出 ' + list.length + ' 篇' : '');
  grid.innerHTML = list.length
    ? list.map(card).join('')
    : '<div class="empty">没有找到匹配的笔记 🔍</div>';
  if (curCat === 'ALL' && !kw){
    const recent = [...DATA].sort((a,b) => b.ts - a.ts).slice(0, 3);
    recentGrid.innerHTML = recent.map(card).join('');
    recentSection.style.display = '';
  } else {
    recentSection.style.display = 'none';
  }
}
renderCats();
q.addEventListener('input', render);
sortSel.addEventListener('change', render);
render();
</script>
</body>
</html>
"""
if __name__ == "__main__":
    build()