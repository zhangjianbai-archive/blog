"""Build the archive with Python standard library only: python build.py."""
import json
from pathlib import Path
from html import escape as e
from urllib.parse import urlsplit
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'docs'
BASE = '/blog'
ORIGIN = 'https://zhangjianbai-archive.github.io'
NAME = '张健柏档案馆'
articles = json.loads((ROOT / 'content/articles.json').read_text(encoding='utf-8'))
OUT.mkdir(exist_ok=True)

def link(path):
    return BASE + '/' + path.lstrip('/')

def page(path, title, description, body, active='', sample=False):
    nav = ''.join(f'<a href="{link(p)}"'+(' aria-current="page"' if active == label else '')+f'>{label}</a>' for label,p in [('首页',''),('文章目录','articles/'),('专题','topics/'),('关于','about/')])
    html = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · {NAME}</title><meta name="description" content="{e(description)}">
<link rel="canonical" href="{ORIGIN}{link(path)}"><meta name="theme-color" content="#f5f3ed">
{'<meta name="robots" content="noindex,follow">' if sample else ''}
<link rel="icon" href="{link('assets/icon.svg')}" type="image/svg+xml">
<link rel="stylesheet" href="{link('assets/style.css')}"><script src="{link('assets/search.js')}" defer></script></head>
<body><a class="skip" href="#main">跳至正文</a><div class="shell">
<header><a class="brand" href="{link('')}"><span class="seal" aria-hidden="true">档</span><span>{NAME}<small>ZHANG JIANBAI ARCHIVE</small></span></a><nav aria-label="主导航">{nav}</nav></header>
<main id="main">{body}</main>
<footer><span>{NAME}<small>公开资料 · 来源索引 · 持续整理</small></span><div><a href="{link('about/#corrections')}">来源与更正</a><span class="muted">© 2026</span></div></footer></div></body></html>'''
    target = OUT / (path + 'index.html' if path.endswith('/') or not path else path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding='utf-8')

def row(a):
    search = e(' '.join([a['title'],a['author'],a['summary'],a['type']]), quote=True)
    return f'''<article class="article-row" data-search="{search}"><div class="row-meta"><span class="tag">{e(a['type'])}</span>{'<span class="sample">示例</span>' if a.get('sample') else ''}<span>{e(a['date'])}</span></div><h3><a href="{link('articles/'+a['slug']+'/')}">{e(a['title'])}<span aria-hidden="true">↗</span></a></h3><p>{e(a['summary'])}</p><div class="byline">{e(a['author'])}</div></article>'''

page('', '首页', '张健柏相关公开资料、个人回忆与评论的整理索引。', f'''
<section class="hero"><div><div class="eyebrow"><span></span> 一座持续整理的资料档案馆</div><h1>留下记录，<br>让资料有迹可循。</h1><p class="intro">整理张健柏相关的公开资料、个人回忆与评论。<br class="desktop">从不同记录出发，回到材料本身。</p><a class="button" href="{link('articles/')}">浏览文章目录 <span aria-hidden="true">↗</span></a></div><aside class="archive-art" aria-hidden="true"><div class="folder back"></div><div class="folder mid"></div><div class="folder front"><div class="folder-top">公开资料档案<span>NO. 001</span></div><div class="folder-title">记录<br>与回望</div><div class="folder-bottom">DOCUMENTS & PERSPECTIVES<br><span>张健柏档案馆</span></div></div></aside></section>
<div class="notice"><span class="dot"></span><p><strong>档案馆正在搭建中</strong>　目前仅展示站务示例，文档合集尚未上线。</p></div>
<section class="home-grid"><div><div class="section-title"><h2>开始阅读</h2><a href="{link('articles/')}">全部条目 →</a></div>{''.join(row(a) for a in articles)}</div><aside class="sidebar"><div class="eyebrow">阅读路径 / EXPLORE</div><a class="explore" href="{link('articles/')}"><span>01</span><div><h3>文章目录</h3><p>按标题、作者与关键词查找</p></div><b>↗</b></a><a class="explore" href="{link('topics/')}"><span>02</span><div><h3>专题索引</h3><p>围绕同一主题，连接不同记录</p></div><b>↗</b></a><a class="explore" href="{link('about/')}"><span>03</span><div><h3>关于档案馆</h3><p>了解资料来源与整理方式</p></div><b>↗</b></a></aside></section>''', '首页')

page('articles/', '文章目录', '浏览与检索档案馆文章。', f'''<div class="page-heading"><div class="eyebrow">INDEX / 文章目录</div><h1>从一篇记录开始。</h1><p>按标题、作者或关键词，找到你想阅读的条目。</p></div><div class="catalog"><section><form role="search" id="search-form"><label for="search">查找文章</label><div class="search-box"><input id="search" type="search" placeholder="输入标题、作者或关键词…" autocomplete="off"><button type="submit">搜索</button></div></form><p class="result-count" id="result-count" role="status">共 {len(articles)} 个条目 · 含站务示例</p><div id="results">{''.join(row(a) for a in articles)}</div><div id="empty" class="empty" hidden><h2>没有找到相关条目</h2><p>试试其他关键词，或清空搜索查看全部内容。</p><button id="clear-search" class="button">清空搜索</button></div></section><aside class="sidebar"><h2>关于当前目录</h2><p>资料仍在整理中。目前仅有一篇站务示例，已有文档合集尚未导入。</p><p>正式文章上线后，将在这里展示作者、来源与发表时间。</p></aside></div>''', '文章目录')

page('topics/', '专题索引', '按主题阅读档案资料。', '''<div class="page-heading"><div class="eyebrow">COLLECTIONS / 专题索引</div><h1>把相关记录，放在一起。</h1><p>从多个来源理解同一主题，保留各自的背景与视角。</p></div><div class="topic-grid">'''+''.join(f'<section class="topic"><span class="topic-number">0{i}</span><h2>{t}</h2><p>{d}</p><span class="pending">待整理 · 暂无条目</span></section>' for i,t,d in [(1,'个人经历与回忆','收录作者对自身学习、工作与生活经历的记录。'),(2,'公开言论与声明','整理公开发言、声明及其原始出处与上下文。'),(3,'事件与资料','汇集围绕具体事件的文件、报道与相关记录。')])+'''</div><p class="topics-note">专题将在相关资料整理完成后开放阅读。</p>''', '专题')

page('about/', '关于档案馆', '本站的整理范围、来源标注与更正方式。', f'''<div class="page-heading"><div class="eyebrow">ABOUT / 关于档案馆</div><h1>资料有出处，阅读有依据。</h1><p>一份持续更新的公开资料索引。</p></div><div class="reading-layout"><article class="prose"><h2 id="purpose">这是什么网站</h2><p>{NAME}由 Klein 发起，用于整理相关公开资料、个人回忆与评论，方便读者检索、阅读并追溯来源。</p><p>当前版本为网站框架。现有文档合集尚未导入，目录中的站务示例仅用于展示页面结构。</p><h2 id="sources">我们如何呈现资料</h2><p>正式条目将保留原始标题与署名，注明原始链接、发表时间和本站收录时间。未知信息明确标注；编者说明与原文分别呈现。</p><p>个人回忆、评论、公开声明与原始文件将区分标注。收录一篇文章不代表本站已经独立证实其中每一项说法。</p><h2 id="corrections">来源与更正</h2><p>发现引用、署名或事实信息有误时，可以在项目仓库提交更正建议。请提供条目网址、具体位置及可核对的来源。</p><p>公开反馈中请勿提交身份证件、联系方式或其他私人材料。专用联系渠道尚在准备中。</p><p><a href="https://github.com/zhangjianbai-archive/blog/issues">前往 GitHub 提交更正建议 ↗</a></p><h2 id="copyright">转载与引用</h2><p>正式上线前逐篇确认转载情况，保留作者署名与来源。本站的页面代码与收录文章分别管理，代码仓库公开不表示第三方文章可以任意转载。</p></article><aside class="toc"><div class="eyebrow">本页目录</div><a href="#purpose">这是什么网站</a><a href="#sources">资料如何呈现</a><a href="#corrections">来源与更正</a><a href="#copyright">转载与引用</a></aside></div>''', '关于')

for a in articles:
    sections = ''.join(f'<section><h2 id="section-{i}">{e(s["heading"])}</h2>'+''.join(f'<p>{e(p)}</p>' for p in s['paragraphs'])+'</section>' for i,s in enumerate(a['sections']))
    toc = ''.join(f'<a href="#section-{i}">{e(s["heading"])}</a>' for i,s in enumerate(a['sections']))
    page('articles/'+a['slug']+'/', a['title'], a['summary'], f'''<a class="backlink" href="{link('articles/')}">← 返回文章目录</a><div class="article-heading"><div class="eyebrow">{e(a['type'])} / 示例页面</div><h1>{e(a['title'])}</h1><div class="article-meta">{e(a['author'])}<span>·</span><time datetime="{a['date']}">{a['date']}</time></div></div><div class="reading-layout"><article class="prose"><div class="reading-note">这是一篇框架示例，用于展示文章阅读体验。</div>{sections}<div class="source-note"><strong>来源说明</strong><p>本站原创站务说明，无外部文档摘录。</p></div><a class="backlink" href="{link('articles/')}">← 继续浏览文章</a></article><aside class="toc"><div class="eyebrow">文章目录</div>{toc}</aside></div>''', '文章目录', sample=a.get('sample',False))

page('404.html', '页面未找到', '页面不存在或已移动。', f'<div class="page-heading"><div class="eyebrow">404 / PAGE NOT FOUND</div><h1>这份记录不在这里。</h1><p>链接可能有误，或页面已经移动。</p><a class="button" href="{link("articles/")}">返回文章目录 →</a></div>', sample=True)
(OUT / '.nojekyll').touch()
urls = ['', 'articles/', 'topics/', 'about/'] + ['articles/'+a['slug']+'/' for a in articles if not a.get('sample')]
(OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{ORIGIN}{link(p)}</loc></url>' for p in urls)+'</urlset>',encoding='utf-8')
# Validate every internal link and asset against the generated project-site paths.
class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ('href','src') and v and v.startswith(BASE+'/'):
                target=OUT/urlsplit(v).path.removeprefix(BASE+'/')
                if v.endswith('/'): target=target/'index.html'
                assert target.exists(), f'Broken internal link: {v}'
for p in OUT.rglob('*.html'):
    Links().feed(p.read_text(encoding='utf-8'))
print(f'Built and checked {len(list(OUT.rglob("*.html")))} HTML pages.')
