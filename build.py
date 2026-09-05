"""Build GitHub Pages using Python standard library."""
import json
from pathlib import Path
from html import escape as e
from html.parser import HTMLParser
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'docs'
BASE='/blog'
ORIGIN='https://zhangjianbai-archive.github.io'
NAME='张健柏档案馆'
categories=json.loads((ROOT/'content/categories.json').read_text(encoding='utf-8'))
articles=json.loads((ROOT/'content/articles.json').read_text(encoding='utf-8'))
OUT.mkdir(exist_ok=True)
for old in OUT.rglob('*.html'):
    assert old.resolve().is_relative_to(OUT.resolve())
    old.unlink()
def link(path=''):
    return BASE+'/'+path.lstrip('/')
def page(path,title,body,active='首页',noindex=False):
    nav=''.join(f'<a href="{link(p)}"'+(' aria-current="page"' if active==label else '')+f'>{label}</a>' for label,p in [('首页',''),('文章目录','articles/'),('分类','topics/')])
    html=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)} · {NAME}</title><meta name="description" content="{e(title)}"><link rel="canonical" href="{ORIGIN}{link(path)}"><meta name="theme-color" content="#dcdedf">{'<meta name="robots" content="noindex,follow">' if noindex else ''}<link rel="icon" href="data:,"><link rel="stylesheet" href="{link('assets/style.css')}"><script src="{link('assets/search.js')}" defer></script></head><body><a class="skip" href="#main">跳至正文</a><div class="shell"><header><a class="brand" href="{link()}">{NAME}</a><nav aria-label="主导航">{nav}</nav></header><main id="main">{body}</main><footer>© 2026 {NAME}</footer></div></body></html>'''
    target=OUT/(path+'index.html' if path.endswith('/') or not path else path)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(html,encoding='utf-8')
def category_list():
    return '<ol class="category-list">'+''.join(f'<li><a href="{link("topics/"+c["slug"]+"/")}"><span class="number">{i:02}</span><span>{e(c["title"])}</span><span class="arrow" aria-hidden="true">→</span></a></li>' for i,c in enumerate(categories,1))+'</ol>'
def rows(items):
    return ''.join(f'<article class="article-row" data-search="{e(a["title"]+" "+a["author"]+" "+a.get("summary",""),quote=True)}"><h2><a href="{link("articles/"+a["slug"]+"/")}">{e(a["title"])}</a></h2><p>{e(a["author"])}</p></article>' for a in items)
page('','首页','<div class="heading"><h1>文档分类</h1></div>'+category_list())
page('topics/','分类','<div class="heading"><h1>文档分类</h1></div>'+category_list(),'分类')
page('articles/','文章目录',f'''<div class="heading"><h1>文章目录</h1></div><form id="search-form" role="search"><label class="sr-only" for="search">搜索文章</label><div class="search-box"><input id="search" type="search" placeholder="搜索标题、作者" autocomplete="off"><button type="submit">搜索</button></div></form><p id="result-count" class="count" role="status">{len(articles)} 篇</p><div id="results">{rows(articles)}</div><div id="empty" class="empty" {'hidden' if articles else ''}><p id="empty-message">暂无文章</p><button id="clear-search" class="text-button" hidden>清空搜索</button></div>''','文章目录')
for c in categories:
    items=[a for a in articles if a.get('category')==c['slug']]
    page('topics/'+c['slug']+'/',c['title'],f'<a class="back" href="{link("topics/")}">← 分类</a><div class="heading"><h1>{e(c["title"])}</h1></div>'+(rows(items) if items else '<p class="empty">暂无文章</p>'),'分类')
for a in articles:
    body=''.join('<section><h2>'+e(s['heading'])+'</h2>'+''.join('<p>'+e(p)+'</p>' for p in s['paragraphs'])+'</section>' for s in a['sections'])
    page('articles/'+a['slug']+'/',a['title'],f'<a class="back" href="{link("articles/")}">← 文章目录</a><div class="heading"><h1>{e(a["title"])}</h1><p>{e(a["author"])}</p></div><article class="prose">{body}</article>','文章目录')
page('404.html','404',f'<div class="heading"><h1>404</h1></div><a href="{link()}">返回首页</a>',noindex=True)
(OUT/'.nojekyll').touch()
urls=['','articles/','topics/']+['topics/'+c['slug']+'/' for c in categories]+['articles/'+a['slug']+'/' for a in articles]
(OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{ORIGIN}{link(p)}</loc></url>' for p in urls)+'</urlset>',encoding='utf-8')
class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ('href','src') and v and v.startswith(BASE+'/'):
                path=urlsplit(v).path
                target=OUT/path.removeprefix(BASE+'/')
                if path.endswith('/'): target=target/'index.html'
                assert target.exists(),f'Broken internal link: {v}'
for p in OUT.rglob('*.html'): Links().feed(p.read_text(encoding='utf-8'))
assert not (OUT/'about/index.html').exists()
assert not (OUT/'articles/reading-guide/index.html').exists()
print(f'Built and checked {len(list(OUT.rglob("*.html")))} HTML pages.')
