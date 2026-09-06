"""Build the archive with Python's standard library."""
import json
import re
from pathlib import Path
from html import escape as e
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs"
BASE = "/blog"
ORIGIN = "https://zhangjianbai-archive.github.io"
NAME = "张健柏档案馆"
articles = json.loads((ROOT / "content/articles.json").read_text(encoding="utf-8"))
categories = json.loads((ROOT / "content/categories.json").read_text(encoding="utf-8"))
tags = json.loads((ROOT / "content/tags.json").read_text(encoding="utf-8"))
for entries in (categories, tags, articles):
    slugs = [entry["slug"] for entry in entries]
    assert len(slugs) == len(set(slugs)), "Duplicate slug"
    assert all(re.fullmatch(r"[a-z0-9-]+", slug) for slug in slugs), "Invalid slug"
OUT.mkdir(exist_ok=True)
# These HTML files are generated output; clearing them removes obsolete routes.
for old in OUT.rglob("*.html"):
    assert old.resolve().is_relative_to(OUT.resolve())
    old.unlink()

def link(path=""):
    return BASE + "/" + path.lstrip("/")

def page(path, title, body, active="", noindex=False):
    nav = "".join(
        f'<a href="{link(p)}"' + (' aria-current="page"' if active == label else "") + f">{label}</a>"
        for label, p in [("首页", ""), ("文章目录", "articles/"), ("分类与标签", "topics/")]
    )
    robots = '<meta name="robots" content="noindex,follow">' if noindex else ""
    html = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · {NAME}</title><meta name="description" content="{e(title)}">
<link rel="canonical" href="{ORIGIN}{link(path)}"><meta name="theme-color" content="#d9dde0">
{robots}<link rel="icon" href="data:,">
<link rel="stylesheet" href="{link('assets/style.css')}"><script src="{link('assets/search.js')}" defer></script></head>
<body><a class="skip" href="#main">跳至正文</a><div class="shell">
<header><a class="brand" href="{link()}"><span>{NAME}<small>ZHANG JIANBAI ARCHIVE</small></span></a><nav aria-label="主导航">{nav}</nav></header>
<main id="main">{body}</main>
<footer><span>{NAME}</span><span class="muted">© 2026</span></footer></div></body></html>'''
    target = OUT / (path + "index.html" if not path or path.endswith("/") else path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")

def row(a):
    search = e(" ".join([a["title"], a.get("author", ""), a.get("summary", ""), a.get("type", "")]), quote=True)
    metadata = (f'<span class="tag">{e(a["type"])}</span>' if a.get("type") else "")
    metadata += (f'<span>{e(a["date"])}</span>' if a.get("date") else "")
    summary = f'<p>{e(a["summary"])}</p>' if a.get("summary") else ""
    return f'''<article class="article-row" data-search="{search}">
<div class="row-meta">{metadata}</div>
<h3><a href="{link('articles/'+a['slug']+'/')}">{e(a['title'])}<span aria-hidden="true">↗</span></a></h3>
{summary}<div class="byline">{e(a.get('author', ''))}</div></article>'''

def sidebar():
    entries = "".join(
        f'<a class="explore" href="{link("topics/"+c["slug"]+"/")}"><span>{i:02}</span><h3>{e(c["title"])}</h3><b aria-hidden="true">↗</b></a>'
        for i, c in enumerate(categories, 1)
    )
    return f'<aside class="sidebar"><h2>分类</h2>{entries}<h2 class="tags-heading">标签</h2>{tag_links()}</aside>'

def tag_links():
    return '<div class="tags">' + ''.join(f'<a class="tag-link" href="{link("tags/"+t["slug"]+"/")}">{e(t["title"])}</a>' for t in tags) + '</div>'

def empty():
    return '<div class="empty"><p>暂无文章</p></div>'

page("", "首页", f'''
<section class="hero"><div><h1>张健柏<br>档案馆</h1><a class="button" href="{link('articles/')}">浏览文章目录 <span aria-hidden="true">↗</span></a></div>
<form class="home-search" action="{link('articles/')}" method="get" role="search">
<label for="home-query">搜索文章</label><div class="search-box"><input id="home-query" name="q" type="search" placeholder="标题、作者或关键词" autocomplete="off"><button type="submit">搜索</button></div>
</form></section>
<section class="home-grid"><section><div class="section-title"><h2>最新文章</h2><a href="{link('articles/')}">全部文章 →</a></div>
{''.join(row(a) for a in articles) if articles else empty()}</section>{sidebar()}</section>''', "首页")

page("articles/", "文章目录", f'''<div class="page-heading"><h1>文章目录</h1></div>
<div class="catalog"><section><form role="search" id="search-form"><label for="search">查找文章</label><div class="search-box">
<input id="search" name="q" type="search" placeholder="标题、作者或关键词" autocomplete="off"><button type="submit">搜索</button></div></form>
<p class="result-count" id="result-count" role="status">{len(articles)} 篇</p><div id="results">{''.join(row(a) for a in articles)}</div>
<div id="empty" class="empty" {'hidden' if articles else ''}><p id="empty-message">暂无文章</p><button id="clear-search" class="button" hidden>清空搜索</button></div>
</section>{sidebar()}</div>''', "文章目录")

cards = "".join(
    f'<a class="topic" href="{link("topics/"+c["slug"]+"/")}"><span class="topic-number">{i:02}</span><h2>{e(c["title"])}</h2><span class="topic-arrow" aria-hidden="true">↗</span></a>'
    for i, c in enumerate(categories, 1)
)
page("topics/", "分类与标签", '<div class="page-heading"><h1>分类</h1></div><div class="topic-grid">'+cards+'</div><section class="tag-section"><h2>标签</h2>'+tag_links()+"</section>", "分类与标签")

for c in categories:
    items = [a for a in articles if a.get("category") == c["slug"]]
    page("topics/"+c["slug"]+"/", c["title"],
         f'<a class="backlink" href="{link("topics/")}">← 分类</a><div class="page-heading"><h1>{e(c["title"])}</h1></div>'
         +f'<div class="catalog"><section>{''.join(row(a) for a in items) if items else empty()}</section>{sidebar()}</div>', "分类与标签")

for t in tags:
    items = [a for a in articles if t["slug"] in a.get("tags", [])]
    page("tags/"+t["slug"]+"/", t["title"],
         f'<a class="backlink" href="{link("topics/")}">← 标签</a><div class="page-heading"><h1>{e(t["title"])}</h1></div>'
         +f'<div class="catalog"><section>{''.join(row(a) for a in items) if items else empty()}</section>{sidebar()}</div>', "分类与标签")

for a in articles:
    sections = "".join(
        f'<section><h2 id="section-{i}">{e(s["heading"])}</h2>'+''.join(f'<p>{e(p)}</p>' for p in s["paragraphs"])+"</section>"
        for i, s in enumerate(a["sections"])
    )
    toc = "".join(f'<a href="#section-{i}">{e(s["heading"])}</a>' for i, s in enumerate(a["sections"]))
    page("articles/"+a["slug"]+"/", a["title"],
         f'<a class="backlink" href="{link("articles/")}">← 文章目录</a><div class="article-heading"><h1>{e(a["title"])}</h1><div class="article-meta">{e(a.get("author", ""))}</div></div>'
         +f'<div class="reading-layout"><article class="prose">{sections}</article><aside class="toc">{toc}</aside></div>', "文章目录")

page("404.html", "页面未找到", f'<div class="page-heading"><h1>页面未找到</h1><a class="button" href="{link()}">返回首页 →</a></div>', noindex=True)
(OUT / ".nojekyll").touch()
urls = ["", "articles/", "topics/"] + ["topics/"+c["slug"]+"/" for c in categories] + ["articles/"+a["slug"]+"/" for a in articles]
urls += ["tags/"+t["slug"]+"/" for t in tags]
(OUT/"sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{ORIGIN}{link(p)}</loc></url>' for p in urls)+"</urlset>", encoding="utf-8")

class Links(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ("href", "src", "action") and v and v.startswith(BASE+"/"):
                path = urlsplit(v).path
                target = OUT / path.removeprefix(BASE+"/")
                if path.endswith("/"):
                    target = target / "index.html"
                assert target.exists(), f"Broken internal link: {v}"
for p in OUT.rglob("*.html"):
    Links().feed(p.read_text(encoding="utf-8"))
assert not (OUT/"about/index.html").exists()
assert not (OUT/"articles/reading-guide/index.html").exists()
print(f"Built and checked {len(list(OUT.rglob('*.html')))} HTML pages.")
