"""Build the blog with Python's standard library."""
import json
import re
from pathlib import Path
from html import escape as e, unescape
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
for article in articles:
    assert article["category"] in {c["slug"] for c in categories}
    assert set(article.get("tags", [])) <= {t["slug"] for t in tags}
OUT.mkdir(exist_ok=True)
# Only generated HTML is removed; assets and source documents remain untouched.
for old in OUT.rglob("*.html"):
    assert old.resolve().is_relative_to(OUT.resolve())
    old.unlink()

def link(path=""):
    return BASE + "/" + path.lstrip("/")

def page(path, title, body, active="", noindex=False):
    nav = "".join(
        f'<a href="{link(p)}"' + (' aria-current="page"' if active == label else "") + f">{label}</a>"
        for label, p in [("首页", ""), ("文章目录", "articles/"), ("分类与标签", "topics/"), ("关于", "about/")]
    )
    robots = '<meta name="robots" content="noindex,follow">' if noindex else ""
    html = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · {NAME}</title><meta name="description" content="{e(title)}">
<link rel="canonical" href="{ORIGIN}{link(path)}"><meta name="theme-color" content="#e9ebed">
{robots}<link rel="icon" href="data:,">
<link rel="stylesheet" href="{link('assets/style.css')}"><script src="{link('assets/search.js')}" defer></script></head>
<body><a class="skip" href="#main">跳至正文</a><div class="shell">
<header class="site-header"><div class="site-identity"><a class="brand" href="{link()}">{NAME}</a>
<form class="header-search" action="{link('articles/')}" method="get" role="search" aria-label="站内搜索">
<label class="sr-only" for="header-query">搜索文章</label><input id="header-query" name="q" type="search" placeholder="搜索文章" autocomplete="off"><button type="submit">搜索</button></form>
</div><nav aria-label="主导航">{nav}</nav></header>
<main id="main">{body}</main>
<footer><span>{NAME}</span><a href="https://github.com/zhangjianbai-archive/blog">GitHub</a></footer></div></body></html>'''
    target = OUT / (path + "index.html" if not path or path.endswith("/") else path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")

def count(kind, slug):
    return sum(a.get("category") == slug if kind == "topics" else slug in a.get("tags", []) for a in articles)

def taxonomy(entries, kind):
    return '<ul class="link-list">' + "".join(
        f'<li><a href="{link(kind+"/"+t["slug"]+"/")}" title="{e(t["title"], quote=True)}">{e(t.get("label", t["title"]))}</a><span class="count">({count(kind,t["slug"])})</span></li>'
        for t in entries
    ) + '</ul>'

def sidebar(toc=""):
    return f'''<aside class="sidebar" aria-label="博客侧栏">
{('<section class="toc"><h2>文章目录</h2>'+toc+'</section>') if toc else ""}
<section><h2>分类</h2>{taxonomy(categories, "topics")}</section>
<section><h2>标签</h2>{taxonomy(tags, "tags")}</section>
</aside>'''

def layout(content, toc=""):
    return f'<div class="blog-layout"><div class="main-column">{content}</div>{sidebar(toc)}</div>'

def metadata(a):
    category = next(c for c in categories if c["slug"] == a["category"])
    parts = [e(a.get("author", ""))]
    if a.get("date"):
        parts.append(f'{e(a.get("dateLabel", ""))} <time datetime="{e(a["date"])}">{e(a.get("updatedAt",a["date"]))}</time>')
    parts.append(f'<a href="{link("topics/"+category["slug"]+"/")}">{e(category["title"])}</a>')
    return '<div class="article-meta">' + '<span class="separator">·</span>'.join(parts) + '</div>'

def article_tags(a):
    selected = [t for t in tags if t["slug"] in a.get("tags", [])]
    return '<div class="post-tags">标签：' + '、'.join(
        f'<a href="{link("tags/"+t["slug"]+"/")}">{e(t["title"])}</a>' for t in selected
    ) + '</div>'

def row(a, preview=False):
    text = [a["title"], a.get("author", ""), a.get("summary", "")]
    text += [c["title"] for c in categories if c["slug"] == a["category"]]
    text += [t["title"] for t in tags if t["slug"] in a.get("tags", [])]
    text += [p for s in a["sections"] for p in [s["heading"], *s["paragraphs"]]]
    search = e(" ".join(text), quote=True)
    url = link("articles/"+a["slug"]+"/")
    excerpt = "".join(f'<p>{e(p)}</p>' for p in a.get("excerpt", [a.get("summary","")])) if preview else ""
    return f'''<article class="post" data-search="{search}">
<h2 class="post-title"><a href="{url}">{e(a["title"])}</a></h2>
{metadata(a)}{('<div class="excerpt">'+excerpt+'</div>') if preview else ""}
{('<a class="read-more" href="'+url+'">阅读全文 »</a>') if preview else ""}{article_tags(a)}</article>'''

def empty():
    return '<p class="empty">暂无文章</p>'

page("", "首页", layout(''.join(row(a, preview=True) for a in articles) if articles else empty()), "首页")

page("articles/", "文章目录", layout(f'''<h1 class="page-title">文章目录</h1>
<form role="search" id="search-form" class="catalog-search"><label class="sr-only" for="search">查找文章</label>
<input id="search" name="q" type="search" placeholder="标题、作者或关键词" autocomplete="off"><button type="submit">搜索</button></form>
<p class="result-count" id="result-count" role="status">{len(articles)} 篇</p><div id="results">{''.join(row(a) for a in articles)}</div>
<div id="empty" class="empty" {'hidden' if articles else ''}><p id="empty-message">暂无文章</p><button id="clear-search" hidden>清空搜索</button></div>'''), "文章目录")

groups = []
for c in categories:
    items = [a for a in articles if a["category"] == c["slug"]]
    item_links = '<ul class="entry-list">' + "".join(f'<li><a href="{link("articles/"+a["slug"]+"/")}">{e(a["title"])}</a><span>{e(a["author"])}</span></li>' for a in items) + '</ul>' if items else ''
    groups.append(f'<section class="category-group"><h2><a href="{link("topics/"+c["slug"]+"/")}">{e(c["title"])}</a><span class="count">({len(items)})</span></h2>{item_links}</section>')
page("topics/", "分类与标签", layout('<h1 class="page-title">分类与标签</h1>' + ''.join(groups)), "分类与标签")

for entries, kind in [(categories, "topics"), (tags, "tags")]:
    for entry in entries:
        items = [a for a in articles if a["category"] == entry["slug"]] if kind == "topics" else [a for a in articles if entry["slug"] in a.get("tags", [])]
        page(kind+"/"+entry["slug"]+"/", entry["title"],
             layout(f'<h1 class="page-title">{e(entry["title"])}<span class="count">({len(items)})</span></h1>' + (''.join(row(a) for a in items) if items else empty())),
             "分类与标签")

for a in articles:
    sections = "".join(
        f'<section><h2 id="section-{i}">{e(s["heading"])}</h2>'+''.join(f'<p>{e(p)}</p>' for p in s["paragraphs"])+"</section>"
        for i, s in enumerate(a["sections"])
    )
    toc = "".join(f'<a href="#section-{i}">{e(s["heading"])}</a>' for i, s in enumerate(a["sections"]))
    article_body = f'<article><h1 class="post-title article-title">{e(a["title"])}</h1>{metadata(a)}<div class="prose">{sections}</div>{article_tags(a)}</article>'
    page("articles/"+a["slug"]+"/", a["title"], layout(article_body, toc), "文章目录")

def inline_markdown(text):
    # Render the Markdown constructs used in the original introduction, without editing its source.
    text = re.sub(r"\\([&~])", r"\1", text)
    text = e(unescape(text))
    text = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text

def introduction():
    result, paragraph, list_kind = [], [], None
    def flush():
        if paragraph:
            result.append("<p>" + inline_markdown(" ".join(paragraph)) + "</p>")
            paragraph.clear()
    for line in (ROOT / "README.md").read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^(#{1,6}) (.+)$", line)
        item = re.match(r"^(- |\d+\. )(.+)$", line)
        if not item and list_kind:
            result.append(f"</{list_kind}>")
            list_kind = None
        if heading:
            flush()
            level = len(heading[1])
            result.append(f"<h{level}>" + inline_markdown(heading[2]) + f"</h{level}>")
        elif item:
            flush()
            kind = "ul" if item[1].startswith("-") else "ol"
            if list_kind != kind:
                if list_kind:
                    result.append(f"</{list_kind}>")
                result.append(f"<{kind}>")
                list_kind = kind
            result.append("<li>" + inline_markdown(item[2]) + "</li>")
        elif line.strip() == "---":
            flush()
            result.append("<hr>")
        elif not line.strip():
            flush()
        else:
            paragraph.append(line.removesuffix("\\"))
    flush()
    if list_kind:
        result.append(f"</{list_kind}>")
    return "".join(result)

page("about/", "关于", layout('<article class="prose introduction">'+introduction()+'</article>'), "关于")
page("404.html", "页面未找到", layout(f'<h1 class="page-title">页面未找到</h1><p><a href="{link()}">返回首页</a></p>'), noindex=True)
(OUT / ".nojekyll").touch()
urls = ["", "articles/", "topics/", "about/"] + ["topics/"+c["slug"]+"/" for c in categories] + ["articles/"+a["slug"]+"/" for a in articles]
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
assert (OUT/"about/index.html").exists()
assert not (OUT/"articles/reading-guide/index.html").exists()
print(f"Built and checked {len(list(OUT.rglob('*.html')))} HTML pages.")
