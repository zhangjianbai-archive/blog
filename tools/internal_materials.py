"""Render reviewed internal materials separately from opinion articles."""
import json
import re
from html import escape
from html.parser import HTMLParser
from urllib.parse import quote


class SafeFragment(HTMLParser):
    """Keep document formatting, never executable or remote content."""
    allowed = {'h2', 'h3', 'h4', 'p', 'strong', 'b', 'em', 'i', 'ul', 'ol',
               'li', 'table', 'thead', 'tbody', 'tfoot', 'tr', 'td', 'th',
               'blockquote', 'br', 'hr', 'div', 'span', 'sup', 'sub', 'caption'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.allowed:
            raise ValueError(f'Unsupported document tag: {tag}')
        safe = ''
        for key, value in attrs:
            if key in {'colspan', 'rowspan'} and tag in {'td', 'th'}:
                if value and value.isdecimal() and 0 < int(value) < 1000:
                    safe += f' {key}="{value}"'
        self.parts.append(f'<{tag}{safe}>')

    def handle_endtag(self, tag):
        if tag not in self.allowed:
            raise ValueError(f'Unsupported document tag: {tag}')
        self.parts.append(f'</{tag}>')

    def handle_data(self, data):
        self.parts.append(escape(data))


def build_internal(root, page, layout, link):
    folder = root / 'content/internal'
    manifest = folder / 'manifest.json'
    records = json.loads(manifest.read_text(encoding='utf-8-sig')) if manifest.exists() else []
    published = [record for record in records if record['status'] == 'publish']
    ids = [record['id'] for record in records]
    assert len(ids) == len(set(ids)), 'Duplicate internal material ID'
    assert all(re.fullmatch(r'[a-z0-9_-]+', slug) for slug in ids)
    notice = ('资料由投稿者提供，原存于内部群。本栏目保存历史材料，不代表本站认可其中的观点、'
              '承诺或健康建议，也不将原文中的指控视为已证实事实。正文按原文整理排版；'
              '历史报名说明不作为当前报名指引。')
    groups = {}
    urls = ['internal/']
    for record in published:
        source = (folder / record['html_file']).resolve()
        assert source.is_relative_to(folder.resolve()), 'Invalid internal material path'
        parser = SafeFragment()
        parser.feed(source.read_text(encoding='utf-8-sig'))
        parser.close()
        title = escape(record['title'])
        path = f'internal/{record["id"]}/'
        year = escape(str(record.get('year') or '年份未标明'))
        category = escape(record.get('category') or '其他资料')
        files = '、'.join(escape(name) for name in record['source_files'])
        originals = [name for name in record['source_files']
                     if (root / 'docs/files/internal' / name).is_file()]
        assert originals, f'Missing original file: {record["id"]}'
        downloads = '<section class="original-downloads" aria-label="原始文件下载"><h2>下载原始文件</h2><ul>'
        for name in originals:
            url = link('files/internal/' + quote(name, safe=''))
            downloads += f'<li><a href="{url}" download="{escape(name, quote=True)}">下载原件：{escape(name)}</a></li>'
        downloads += '</ul><p class="meta">原始文件，未作转换或修改。</p></section>'
        body = (f'<article class="internal-document"><p><a href="{link("internal/")}">← 内部资料目录</a></p>'
                f'<h1 class="page-title">{title}</h1><p class="meta">{category} · {year}</p>'
                f'{downloads}<p class="internal-notice">{notice}</p><div class="prose internal-prose">'
                + ''.join(parser.parts) + f'</div><hr><p class="meta">来源文件：{files}</p></article>')
        page(path, record['title'], layout(body), '内部资料', description=record['title']+'：内部群历史资料整理。')
        urls.append(path)
        groups.setdefault(record.get('category') or '其他资料', []).append(
            f'<li><a href="{link(path)}">{title}</a><span class="meta"> · {year}</span></li>')
    listing = ''.join(f'<section><h2>{escape(category)}</h2><ul class="catalog-list">'+''.join(items)+'</ul></section>'
                      for category, items in groups.items())
    body = (f'<h1 class="page-title">内部资料</h1><p>{notice}</p>'
            f'<p class="meta">已整理 {len(published)} 项资料。与评论文章分开收录。</p>'+listing)
    page('internal/', '内部资料', layout(body), '内部资料', description='课程规则、报名说明、问答与教学材料等内部群历史资料。')
    return urls
