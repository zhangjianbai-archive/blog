"""Build the blog with Python's standard library."""
import json
import hashlib
import re
from pathlib import Path
from html import escape as e, unescape
from html.parser import HTMLParser
from urllib.parse import urlsplit, urlencode

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs"
BASE = "/blog"
ORIGIN = "https://zhangjianbai-archive.github.io"
NAME = "张健柏档案馆"
VERSION = hashlib.sha256(b"".join(p.read_bytes() for p in [ROOT / "build.py", *sorted((ROOT / "content").glob("*")), ROOT / "docs/assets/style.css", ROOT / "docs/assets/search.js"] if p.is_file())).hexdigest()[:12]
articles = json.loads((ROOT / "content/articles.json").read_text(encoding="utf-8"))
catalog = json.loads((ROOT / "content/catalog.json").read_text(encoding="utf-8"))
categories = json.loads((ROOT / "content/categories.json").read_text(encoding="utf-8"))
tags = json.loads((ROOT / "content/tags.json").read_text(encoding="utf-8"))
presentation = json.loads((ROOT / "content/presentation.json").read_text(encoding="utf-8"))
features = json.loads((ROOT / "content/features.json").read_text(encoding="utf-8"))
for entries in (categories, tags, articles, catalog, features):
    slugs = [entry["slug"] for entry in entries]
    assert len(slugs) == len(set(slugs)), "Duplicate slug"
    assert all(re.fullmatch(r"[a-z0-9-]+", slug) for slug in slugs), "Invalid slug"
for article in articles:
    assert article["category"] in {c["slug"] for c in categories}
    assert set(article.get("tags", [])) <= {t["slug"] for t in tags}
    assert set(article.get("relatedCategories", [])) <= {c["slug"] for c in categories}
for item in catalog:
    # Catalog entries must never carry unpublished text or images into the output.
    assert set(item) <= {"slug", "title", "author", "authorSource", "category", "topic", "tags", "kind", "source", "article"}
    feature = next(f for f in features if f["slug"] == item["topic"])
    assert item["category"] == feature["category"]
    assert set(item["tags"]) <= {t["slug"] for t in tags}
    if item.get("article"):
        assert item["article"] in {a["slug"] for a in articles}
assert {item["article"] for item in catalog if item.get("article")} == {a["slug"] for a in articles}
OUT.mkdir(exist_ok=True)
# Only generated HTML is removed; assets and source documents remain untouched.
for old in OUT.rglob("*.html"):
    assert old.resolve().is_relative_to(OUT.resolve())
    old.unlink()

def link(path=""):
    return BASE + "/" + path.lstrip("/")

def filter_link(key, value, label, css=""):
    return f'<a class="{css}" data-filter="{key}" data-value="{e(value, quote=True)}" href="{link("articles/")}?{e(urlencode({key:value}), quote=True)}">{e(label)}</a>'

def page(path, title, body, active="", noindex=False):
    nav = "".join(
        f'<a href="{link(p)}"' + (' aria-current="page"' if active == label else "") + f">{label}</a>"
        for label, p in [("首页", ""), ("张健柏是谁？", "who-is-zhang-jianbai/"), ("文章目录", "articles/"), ("分类", "topics/"), ("作者介绍", "authors/"), ("关于", "about/")]
    )
    robots = '<meta name="robots" content="noindex,follow">' if noindex else ""
    html = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · {NAME}</title><meta name="description" content="{e(title)}">
<link rel="canonical" href="{ORIGIN}{link(path)}"><meta name="site-version" content="{VERSION}"><meta name="theme-color" content="#e9ebed">
{robots}<link rel="icon" href="data:,">
<link rel="stylesheet" href="{link('assets/style.css')}?v={VERSION}"><script src="{link('assets/search.js')}?v={VERSION}" defer></script></head>
<body><a class="skip" href="#main">跳至正文</a><div class="shell">
<header class="site-header"><div class="site-identity"><a class="brand" href="{link()}">{NAME}</a>
<form id="search-form" class="header-search" action="{link('articles/')}" method="get" role="search" aria-label="站内搜索">
<input type="hidden" name="v" value="{VERSION}"><label class="sr-only" for="search">搜索文章</label><input id="search" name="q" type="search" placeholder="搜索文章" autocomplete="off"><button type="submit">搜索</button></form>
</div><nav aria-label="主导航">{nav}</nav></header>
<main id="main">{body}</main>
<footer><span>{NAME}</span><a href="https://github.com/zhangjianbai-archive/blog">GitHub</a></footer></div></body></html>'''
    def version_link(match):
        prefix, url = match.groups()
        parsed = urlsplit(unescape(url))
        if parsed.path.startswith(BASE + "/") and not parsed.path.startswith(BASE + "/assets/"):
            url += ("&amp;" if "?" in url else "?") + "v=" + VERSION
        return prefix + url + '"'
    html = re.sub(r'(<a\b[^>]*?href=")([^"#]+)"', version_link, html)
    target = OUT / (path + "index.html" if not path or path.endswith("/") else path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")

def in_category(a, slug):
    return slug in [a["category"], *a.get("relatedCategories", [])]

def count(kind, slug):
    return sum(in_category(a, slug) if kind == "topics" else slug in a.get("tags", []) for a in catalog)

def count_label(number):
    return f'<span class="count">({number})</span>' if number else ''

def taxonomy(entries, kind):
    return '<ul class="link-list '+('category-links' if kind == 'topics' else 'tag-links')+'">' + "".join(
        f'<li>{filter_link("category" if kind == "topics" else "tag",t["slug"],t.get("label",t["title"]))}{count_label(count(kind,t["slug"]))}</li>'
        for t in entries
    ) + '</ul>'

def sidebar():
    groups = []
    home_slugs = {a["slug"] for a in articles[:5]}
    for c in categories:
        selected = []
        for a in articles:
            if a["category"] == c["slug"] and a["slug"] not in home_slugs and a.get("author") not in {x.get("author") for x in selected}:
                selected.append(a)
            if len(selected) == 2:
                break
        links = ''.join(f'<li><a href="{link("articles/"+a["slug"]+"/")}">{e(a["title"])}</a></li>' for a in selected)
        groups.append(f'<section><h2>{e(c["title"])}</h2><ul class="sidebar-bullets">{links}</ul></section>')
    return f'''<aside class="sidebar" aria-label="博客侧栏">
<div class="sidebar-image-slot" role="img" aria-label="预留博客图片位置"><svg aria-hidden="true" width="36" height="30" viewBox="0 0 36 30" fill="none"><rect x="1" y="1" width="34" height="28" stroke="currentColor"/><circle cx="11" cy="9" r="3" stroke="currentColor"/><path d="M2 25L13 15L20 21L26 13L34 23" stroke="currentColor"/></svg></div>
<section><h2>博客主要内容</h2><ul class="sidebar-bullets"><li>追问教育承诺与实际成果</li><li>呈现学堂里的学习与生活</li><li>讨论权威、服从与精神控制</li><li>记录质疑、删帖与舆论交锋</li><li>回望离开学堂后的经历</li><li>对照张健柏的言论与行动</li></ul></section>
{''.join(groups)}
<details class="sidebar-tags"><summary>合集标签</summary>{taxonomy(tags, "tags")}</details>
</aside>'''

def layout(content, article_sidebar=None):
    side = sidebar() if article_sidebar is None else article_sidebar
    return f'<div class="blog-layout{ " reading-layout" if article_sidebar is not None else ""}"><div class="main-column">{content}</div>{side}</div>'

def summary_html(a):
    points = presentation.get(a["slug"], {}).get("points", [])
    if not points:
        return ""
    return '<section class="article-summary"><h2>原文提要</h2><p class="summary-credit">摘自原文</p><ul>'+''.join(f'<li>{e(point["text"])} <a href="#section-{point["section"]}" aria-label="阅读对应段落">↗</a></li>' for point in points)+'</ul></section>'

def metadata(a):
    category = next(c for c in categories if c["slug"] == a["category"])
    parts = [filter_link("author",a["author"],a["author"])] if a.get("author") else []
    if a.get("date"):
        parts.append(f'{e(a.get("dateLabel", ""))} <time datetime="{e(a["date"])}">{e(a.get("updatedAt",a["date"]))}</time>')
    parts.append(filter_link("category",category["slug"],category["title"]))
    return '<div class="article-meta">' + '<span class="separator">·</span>'.join(parts) + '</div>'

def article_tags(a):
    selected = [t for t in tags if t["slug"] in a.get("tags", [])]
    return '<div class="post-tags">标签：' + '、'.join(
        filter_link("tag",t["slug"],t["title"]) for t in selected
    ) + '</div>'

def row(a, preview=False):
    text = [a["title"], a.get("author", ""), a.get("summary", "")]
    text += [c["title"] for c in categories if in_category(a, c["slug"])]
    text += [t["title"] for t in tags if t["slug"] in a.get("tags", [])]
    text += [p if isinstance(p, str) else p.get("alt", "") for s in a["sections"] for p in [s["heading"], *s["paragraphs"]]]
    search = e(" ".join(text), quote=True)
    url = link("articles/"+a["slug"]+"/")
    excerpt = "".join(f'<p>{e(p)}</p>' for p in ([presentation[a["slug"]]["excerpt"]] if a["slug"] in presentation else a.get("excerpt", [a.get("summary","")])) ) if preview else ""
    return f'''<article class="post" data-search="{search}">
<h2 class="post-title"><a href="{url}">{e(a["title"])}</a></h2>
{metadata(a)}{('<div class="excerpt">'+excerpt+'</div>') if preview else ""}
<div class="post-footer">{('<a class="read-more" href="'+url+'">阅读全文 »</a>') if preview else ""}{article_tags(a)}</div></article>'''

def empty():
    return '<p class="empty">暂无文章</p>'

page("", "首页", layout((''.join(row(a, preview=True) for a in articles[:5])+f'<a class="more-posts" href="{link("articles/")}?readable=1">全部已上架文章 →</a>') if articles else empty()), "首页")

def title_row(item, searchable=False):
    search = [item["title"], item["author"], item["kind"]]
    search += [c["title"] for c in categories if in_category(item, c["slug"])]
    search += [f["title"] for f in features if f["slug"] == item["topic"]]
    search += [t["title"] for t in tags if t["slug"] in item["tags"]]
    title = e(item["title"])
    if item.get("article"):
        title = f'<a href="{link("articles/"+item["article"]+"/")}">{title}</a>'
    author = filter_link("author",item["author"],item["author"],"entry-author") if item["author"] else ''
    tag = next(t for t in tags if t["slug"] in item["tags"])
    tag_link = filter_link("tag",tag["slug"],tag.get("label",tag["title"]),"entry-tag")
    if item["author"] == tag.get("label", tag["title"]):
        tag_link = ''
    status = '<span class="entry-status readable">可阅读全文</span>' if item.get("article") else '<span class="entry-status">仅标题</span>'
    kind = f'<span class="entry-kind">{e(item["kind"])}</span>' if item["kind"] != '文章' else ''
    attrs = f' data-search="{e(" ".join(search),quote=True)}" data-readable="{str(bool(item.get("article"))).lower()}"' if searchable else ''
    if searchable:
        attrs += f' data-category="{e(item["category"],quote=True)}" data-topic="{e(item["topic"],quote=True)}" data-tag="{e(" ".join(item["tags"]),quote=True)}" data-author="{e(item["author"],quote=True)}"'
    return f'<li id="{item["slug"]}" class="catalog-entry"{attrs}><div class="entry-heading">{title}</div><div class="entry-meta">{author}{tag_link}{kind}{status}</div></li>'

def topic_groups(items, searchable=False, category_headings=True):
    groups = []
    for c in categories:
        selected = [a for a in items if in_category(a, c["slug"])]
        if not selected:
            continue
        subgroups = []
        for feature in features:
            entries = [a for a in selected if a["topic"] == feature["slug"]]
            if not entries:
                continue
            level = 3 if category_headings else 2
            subgroups.append(f'<section class="topic-group" id="{feature["slug"]}" data-filter-group><h{level} class="topic-title">{e(feature["title"])}</h{level}><ul class="catalog-list">'+''.join(title_row(a, searchable) for a in entries)+'</ul></section>')
        heading = f'<h2 class="category-title"><a href="{link("topics/"+c["slug"]+"/")}">{e(c["title"])}</a></h2>' if category_headings else ''
        groups.append(f'<section class="category-group" id="{c["slug"]}" data-filter-group>{heading}'+''.join(subgroups)+'</section>')
    return ''.join(groups)

def category_jumps():
    return '<div class="category-jumps" aria-label="按议题筛选">'+filter_link("category","","全部")+''.join(filter_link("category",c["slug"],c["title"]) for c in categories)+'</div>'

page("articles/", "文章目录", layout(f'''<h1 class="page-title">文章目录</h1>
<div class="catalog-toolbar"><p class="result-count" id="result-count" role="status">{len(catalog)} 个标题 · {len(articles)} 篇可阅读全文</p><label><input type="checkbox" id="readable-only"> 只看已上架</label></div>
{category_jumps()}<details class="filter-picker"><summary>专题、合集与作者</summary><div class="filter-options"><label>专题<select data-select="topic"><option value="">全部专题</option>{''.join(f'<option value="{f["slug"]}">{e(f["title"])}</option>' for f in features)}</select></label><label>合集<select data-select="tag"><option value="">全部合集</option>{''.join(f'<option value="{t["slug"]}">{e(t["title"])}</option>' for t in tags)}</select></label><label>作者<select data-select="author"><option value="">全部作者</option>{''.join(f'<option value="{e(a,quote=True)}">{e(a)}</option>' for a in sorted({a["author"] for a in catalog if a["author"]}))}</select></label></div></details>
<div class="active-filters" id="active-filters" aria-label="当前筛选"></div><button id="clear-search" hidden>清空筛选</button>
<div id="results"><ul class="catalog-list">{''.join(title_row(a, searchable=True) for a in catalog)}</ul></div>
<div id="empty" class="empty" hidden><p>没有匹配的文章，请调整筛选条件。</p></div><nav class="pagination" aria-label="结果分页"><button id="prev-page">上一页</button><span id="page-count" role="status"></span><button id="next-page">下一页</button></nav>'''), "文章目录")

topic_index = ''.join('<section class="topic-index"><h2>'+filter_link("category",c["slug"],c["title"])+'</h2><ul>'+''.join('<li>'+filter_link("topic",f["slug"],f["title"])+'</li>' for f in features if f['category']==c['slug'])+'</ul></section>' for c in categories)
page("topics/", "分类", layout('<h1 class="page-title">分类</h1>'+topic_index+'<section class="topic-index"><h2>合集标签</h2>'+taxonomy(tags,"tags")+'</section>'), "分类")

for entries, kind in [(categories, "topics"), (tags, "tags")]:
    for entry in entries:
        items = [a for a in catalog if in_category(a, entry["slug"])] if kind == "topics" else [a for a in catalog if entry["slug"] in a.get("tags", [])]
        listing = topic_groups(items, category_headings=False) if kind == "topics" else '<ul class="catalog-list">'+''.join(title_row(a) for a in items)+'</ul>'
        page(kind+"/"+entry["slug"]+"/", entry["title"],
             layout(f'<h1 class="page-title">{e(entry["title"])}{count_label(len(items))}</h1>' + (listing if items else empty())),
             "分类")

def paragraph_html(p):
    if isinstance(p, str):
        return f'<p>{e(p)}</p>'
    if 'markdown' in p:
        # Reviewed Markdown supports only explicit inline emphasis. Escaping is
        # applied first so imported source text cannot create arbitrary HTML.
        value = e(p['markdown'])
        value = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', value)
        return f'<p>{value}</p>'
    if 'table' in p:
        return '<div class="table-scroll"><table>'+''.join('<tr>'+''.join('<td>'+e(cell)+'</td>' for cell in row)+'</tr>' for row in p['table'])+'</table></div>'
    assert re.fullmatch(r'assets/articles/[a-z0-9/-]+\.(png|jpg|webp)', p['image'])
    return f'<figure><a href="{link(p["image"])}"><img src="{link(p["image"])}" alt="{e(p["alt"], quote=True)}" loading="lazy"></a></figure>'

for a in articles:
    sections = "".join(
        f'<section id="section-{i}">'+(f'<h{min(4,max(2,s.get("level",2)))}>{e(s["heading"])}</h{min(4,max(2,s.get("level",2)))}>' if s["heading"] else '')+('<blockquote>' if s.get('quotation') else '')+''.join(paragraph_html(p) for p in s["paragraphs"])+('</blockquote>' if s.get('quotation') else '')+"</section>"
        for i, s in enumerate(a["sections"])
    )
    toc = "".join(f'<a href="#section-{i}">{e(s["heading"])}</a>' for i, s in enumerate(a["sections"]) if s["heading"]) or '<a href="#section-0">正文</a>'
    summary = summary_html(a)
    reading_side = '<aside class="sidebar article-sidebar" aria-label="本文侧栏"><section class="toc"><h2>目录</h2>'+toc+'</section>'+summary+'</aside>'
    back = f'<a class="back-results" href="{link("articles/")}">返回文章目录</a>'
    article_body = f'<article>{back}<h1 class="post-title article-title">{e(a["title"])}</h1>{metadata(a)}'+f'<div class="prose">{sections}</div>{article_tags(a)}<div class="reading-footer">{back} · <a href="#main">回到顶部 ↑</a></div></article>'
    page("articles/"+a["slug"]+"/", a["title"], layout(article_body, reading_side), "文章目录")

def inline_markdown(text):
    # Render the Markdown constructs used in the original introduction, without editing its source.
    text = re.sub(r"\\([&~])", r"\1", text)
    text = e(unescape(text))
    text = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text

def introduction(source="README.md"):
    result, paragraph, list_kind = [], [], None
    def flush():
        if paragraph:
            result.append("<p>" + inline_markdown(" ".join(paragraph)) + "</p>")
            paragraph.clear()
    for line in (ROOT / source).read_text(encoding="utf-8").splitlines():
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

page("who-is-zhang-jianbai/", "张健柏是谁？", layout('<article class="prose introduction">'+introduction("content/who-is-zhang-jianbai.md")+'</article>'), "张健柏是谁？")
page("about/", "关于", layout('<article class="prose introduction">'+introduction("content/blog-introduction.md")+'</article>'), "关于")
author_profiles = json.loads((ROOT / "content/authors.json").read_text(encoding="utf-8"))
author_blocks = []
for profile in author_profiles:
    selected = [a for a in articles if a.get("author") == profile["name"]]
    assert selected, "Author profile must have matching articles"
    examples = ''.join(f'<li><a href="{link("articles/"+a["slug"]+"/")}">{e(a["title"])}</a></li>' for a in selected[:2])
    author_blocks.append(f'<section class="author-profile"><h2>{e(profile["name"])}</h2><p>{e(profile["introduction"])}</p><ul>{examples}</ul><p class="author-more">{filter_link("author",profile["name"],f"查看全部文章（{len(selected)}） →")}</p></section>')
page("authors/", "作者介绍", layout('<h1 class="page-title">作者介绍</h1><div class="author-profiles">'+''.join(author_blocks)+'</div>'), "作者介绍")
page("404.html", "页面未找到", layout(f'<h1 class="page-title">页面未找到</h1><p><a href="{link()}">返回首页</a></p>'), noindex=True)
(OUT / ".nojekyll").touch()
urls = ["", "articles/", "topics/", "about/", "who-is-zhang-jianbai/", "authors/"] + ["topics/"+c["slug"]+"/" for c in categories] + ["articles/"+a["slug"]+"/" for a in articles]
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
