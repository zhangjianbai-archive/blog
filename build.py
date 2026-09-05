"""Build the archive site with Python's standard library."""
import json
from pathlib import Path
from html import escape as e
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs"
BASE = "/blog"
ORIGIN = "https://zhangjianbai-archive.github.io"
NAME = "张健柏档案馆"
categories = json.loads((ROOT / "content/categories.json").read_text(encoding="utf-8"))
articles = json.loads((ROOT / "content/articles.json").read_text(encoding="utf-8"))
OUT.mkdir(exist_ok=True)
for old in OUT.rglob("*.html"):
    assert old.resolve().is_relative_to(OUT.resolve())
    old.unlink()

def link(path=""):
    return BASE + "/" + path.lstrip("/")

def page(path, title, body, active="首页", noindex=False):
    nav = "".join(
        f'<a href="{link(p)}"' + (f' aria-current="page"' if active == label else "") + f">{label}</a>"
        for label, p in [("首页", ""), ("文章目录", "articles/"), ("分类", "topics/")]
    )
    robots = '<meta name="robots" content="noindex,follow">' if noindex else ""
    html = f'''<!doctype html><html lang="zh-CN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · {NAME}</title><meta name="description" content="{e(title)}">
<link rel="canonical" href="{ORIGIN}{link(path)}"><meta name="theme-color" content="#d8d9da">{robots}
<link rel="icon" href="data:,"><link rel="stylesheet" href="{link('assets/style.css')}">
<script src="{link('assets/search.js')}" defer></script></head><body>
<a class="skip" href="#main">跳至正文</a><div class="shell">
<header><a class="brand" href="{link()}"><span>{NAME}<small>ARCHIVE / 2026</small></span></a>
<nav aria-label="主导航">{nav}</nav></header><main id="main">{body}</main>
<footer><span>{NAME}</span><span>ARCHIVE / {len(categories):02} CATEGORIES</span></footer></div></body></html>'''
    target = OUT / (path + "index.html" if path.endswith("/") or not path else path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")

def category_cards():
    return "".join(
        f'''<a class="category-card" href="{link('topics/'+c['slug']+'/')}">
        <div class="card-top"><span>{i:02}</span><span class="card-arrow">↗</span></div>
        <h3>{e(c['title'])}</h3><div class="card-bottom"><span>COLLECTION</span><b>0 篇</b></div></a>'''
        for i, c in enumerate(categories, 1)
    )

def category_sidebar():
    return '<aside class="side-nav"><div class="side-label">分类 / COLLECTIONS</div><a class="side-active" href="'+link('topics/')+'"><span>全部分类</span><b>12</b></a>'+"".join(f'<a href="{link("topics/"+c["slug"]+"/")}"><span>{e(c["title"])}</span><b>0</b></a>' for c in categories)+"</aside>"

def rows(items):
    if not items:
        return '<div class="empty-panel"><span class="empty-line"></span><h2>暂无文章</h2><p>文章整理完成后会显示在这里。</p></div>'
    return ''.join(f'''<article class="article-row" data-search="{e(a['title']+' '+a.get('author','')+' '+a.get('summary',''), quote=True)}">
      <div class="row-number">{i:02}</div><div><h2><a href="{link('articles/'+a['slug']+'/')}">{e(a['title'])}</a></h2><p>{e(a.get('author',''))} <span>·</span> {e(a.get('date',''))}</p></div><span class="row-arrow">↗</span></article>''' for i, a in enumerate(items, 1))

home_body = f'''<section class="hero-bar"><div><div class="kicker"><i></i> ARCHIVE / INDEX</div><h1>{NAME}</h1><p class="hero-meta">公开文章与相关记录的索引</p></div><div class="hero-count"><strong>{len(categories):02}</strong><span>分类</span></div></section>
<div class="stats"><div><b>{len(categories):02}</b><span>分类</span></div><div><b>{len(articles):02}</b><span>文章</span></div><div><b>2026</b><span>建立</span></div><div class="stats-note">按原合集排列</div></div>
<section class="workspace">{category_sidebar()}<div class="main-feed"><div class="feed-head"><div><span class="section-kicker">INDEX 01</span><h2>文档分类</h2></div><a class="plain-link" href="{link('articles/')}">文章目录 <span>→</span></a></div><div class="category-grid">{category_cards()}</div></div></section>'''
page("", "首页", home_body)
page("topics/", "分类", f'''<div class="page-title"><span class="section-kicker">INDEX 01 / COLLECTIONS</span><h1>文档分类</h1><p>按原合集排列</p></div><section class="workspace">{category_sidebar()}<div class="main-feed"><div class="category-grid">{category_cards()}</div></div></section>''', "分类")
page("articles/", "文章目录", f'''<div class="page-title"><span class="section-kicker">INDEX 02 / ARTICLES</span><h1>文章目录</h1></div><div class="article-toolbar"><form id="search-form" role="search"><label class="sr-only" for="search">搜索文章</label><div class="search-box"><span>⌕</span><input id="search" type="search" placeholder="搜索标题或作者" autocomplete="off"><button type="submit">搜索</button></div></form><span id="result-count" class="count" role="status">{len(articles)} 篇</span></div><div id="results">{rows(articles)}</div><div id="empty" class="empty-panel" hidden><h2 id="empty-message">没有匹配的文章</h2><button id="clear-search" class="text-button">清空搜索</button></div>''', "文章目录")
for c in categories:
    items = [a for a in articles if a.get("category") == c["slug"]]
    page("topics/"+c["slug"]+"/", c["title"], f'''<a class="back" href="{link('topics/')}">← 返回分类</a><div class="page-title"><span class="section-kicker">COLLECTION / {categories.index(c)+1:02}</span><h1>{e(c['title'])}</h1><p>0 篇文章</p></div>{rows(items)}''', "分类")
for a in articles:
    body = "".join('<section><h2>'+e(s['heading'])+'</h2>'+''.join('<p>'+e(p)+'</p>' for p in s['paragraphs'])+'</section>' for s in a['sections'])
    page("articles/"+a["slug"]+"/", a["title"], f'''<a class="back" href="{link('articles/')}">← 返回文章目录</a><div class="page-title"><span class="section-kicker">ARTICLE</span><h1>{e(a['title'])}</h1><p>{e(a.get('author',''))}</p></div><article class="prose">{body}</article>''', "文章目录")
page("404.html", "404", f'<div class="page-title"><h1>404</h1></div><a href="{link()}">返回首页</a>', noindex=True)
(OUT / ".nojekyll").touch()
urls = ["", "articles/", "topics/"] + ["topics/"+c["slug"]+"/" for c in categories] + ["articles/"+a["slug"]+"/" for a in articles]
(OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{ORIGIN}{link(p)}</loc></url>' for p in urls)+'</urlset>', encoding="utf-8")

class Links(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ("href", "src") and v and v.startswith(BASE+"/"):
                path = urlsplit(v).path
                target = OUT / path.removeprefix(BASE+"/")
                if path.endswith("/"):
                    target = target / "index.html"
                assert target.exists(), f"Broken internal link: {v}"
for p in OUT.rglob("*.html"):
    Links().feed(p.read_text(encoding="utf-8"))
assert not (OUT / "about/index.html").exists()
assert not (OUT / "articles/reading-guide/index.html").exists()
print(f"Built and checked {len(list(OUT.rglob('*.html')))} HTML pages.")
