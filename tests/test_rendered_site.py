"""Run after build.py: preserve source text and verify reading/navigation output."""
import json
import hashlib
import re
import unittest
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, quote, parse_qs

ROOT = Path(__file__).resolve().parents[1]
ROSTER = json.loads((ROOT/'content/qingshan-roster.json').read_text(encoding='utf-8'))

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.depth = 0
        self.prose = []
        self.ids = set()
        self.fragments = []
        self.images = []
        self.visible_rows = 0
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.add(a['id'])
        if tag == 'a' and a.get('href', '').startswith('#'):
            self.fragments.append(a['href'][1:])
        if tag == 'img':
            self.images.append(a)
        if 'catalog-entry' in a.get('class', '').split() and 'hidden' not in a:
            self.visible_rows += 1
        if tag == 'div':
            if self.depth or a.get('class') == 'prose':
                self.depth += 1

    def handle_endtag(self, tag):
        if tag == 'div' and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.prose.append(data)

def normalized(text):
    return re.sub(r'\s+', '', text)

class RenderedSite(unittest.TestCase):

    def test_homepage_selection_and_verbatim_previews(self):
        expected = (
            'qingshan-university-roster', 'congying-information-cocoon',
            'zhang-chengfeng-online-underworld', 'zhang-chengfeng-sexual-repression',
            'huang-chuanke-qianli-survey', 'huang-chuanke-world-first-claim',
        )
        html = (ROOT/'docs/index.html').read_text(encoding='utf-8')
        self.assertEqual(tuple(re.findall(r'<h2 class="post-title"><a href="/blog/articles/([^/]+)/">', html)), expected)
        previews = json.loads((ROOT/'content/home-previews.json').read_text(encoding='utf-8'))
        articles = json.loads((ROOT/'content/articles.json').read_text(encoding='utf-8'))
        articles.append(ROSTER)
        for slug in expected:
            with self.subTest(slug=slug):
                source = next(a for a in articles if a['slug'] == slug)
                body = ''.join((p if isinstance(p, str) else p.get('markdown', '')).replace('**', '')
                               for section in source['sections'] for p in section['paragraphs'])
                self.assertIn(previews[slug], body)
                self.assertIn(escape(previews[slug]), html)

    def test_site_version_is_cross_platform_and_consistent(self):
        paths = [ROOT/'build.py', *sorted((ROOT/'content').glob('*')), ROOT/'docs/assets/style.css', ROOT/'docs/assets/search.js']
        source = b''.join(
            path.read_bytes().replace(b'\r\n', b'\n').replace(b'\r', b'\n')
            for path in paths if path.is_file()
        )
        expected = hashlib.sha256(source).hexdigest()[:12]
        for path in (ROOT/'docs').rglob('*.html'):
            html = path.read_text(encoding='utf-8')
            with self.subTest(path=path):
                self.assertIn(f'<meta name="site-version" content="{expected}">', html)
                self.assertIn(f'/blog/assets/style.css?v={expected}', html)
                self.assertIn(f'/blog/assets/search.js?v={expected}', html)

    def test_static_author_and_topic_pages(self):
        catalog = json.loads((ROOT/'content/catalog.json').read_text(encoding='utf-8'))
        profiles = json.loads((ROOT/'content/authors.json').read_text(encoding='utf-8'))
        self.assertEqual({p['name'] for p in profiles}, {x['author'] for x in catalog if x['author']})
        index = (ROOT/'docs/authors/index.html').read_text(encoding='utf-8')
        for profile in profiles:
                self.assertIn(escape(profile['name']), index)
                self.assertIn('href="/blog/authors/'+quote(profile['name'], safe='')+'/"', index)
        features = json.loads((ROOT/'content/features.json').read_text(encoding='utf-8'))
        sitemap = (ROOT/'docs/sitemap.xml').read_text(encoding='utf-8')
        groups = [('authors', name, [x for x in catalog if x['author'] == name]) for name in sorted({x['author'] for x in catalog if x['author']})]
        groups += [('features', f['slug'], [x for x in catalog if x['topic'] == f['slug']]) for f in features]
        for folder, key, items in groups:
            with self.subTest(folder=folder, key=key):
                html = (ROOT/'docs'/folder/key/'index.html').read_text(encoding='utf-8')
                url = 'https://zhangjianbai-archive.github.io/blog/'+folder+'/'+quote(key, safe='')+'/'
                self.assertIn('<link rel="canonical" href="'+url+'">', html)
                self.assertIn('<loc>'+url+'</loc>', sitemap)
                listing = re.search(r'<ul class="catalog-list">(.*?)</ul>', html, re.S).group(1)
                actual = re.findall(r'<li id="([^"]+)" class="catalog-entry"', listing)
                expected = [x['slug'] for x in items]
                if (folder, key) in [('authors', '大王'), ('features', 'rebuild')]:
                    expected.insert(0, ROSTER['slug'])
                self.assertEqual(actual, expected)

    def test_page_links_have_no_cache_version(self):
        for path in (ROOT/'docs').rglob('*.html'):
            html = path.read_text(encoding='utf-8')
            for href in re.findall(r'<a\b[^>]*href="([^"]+)"', html):
                url = urlsplit(unescape(href))
                if url.path.startswith('/blog/') and not url.path.startswith('/blog/assets/'):
                    self.assertNotIn('v', parse_qs(url.query), str(path))

    def test_search_titles_and_static_overviews(self):
        presentation = json.loads((ROOT/'content/presentation.json').read_text(encoding='utf-8'))
        for article in json.loads((ROOT/'content/articles.json').read_text(encoding='utf-8')):
            with self.subTest(slug=article['slug']):
                item = presentation[article['slug']]
                html = (ROOT/'docs/articles'/article['slug']/'index.html').read_text(encoding='utf-8')
                self.assertIn('<title>'+escape(item['seo_title'])+' · 张健柏档案馆</title>', html)
                heading = re.search(r'<h1\b[^>]*>(.*?)</h1>', html).group(1)
                self.assertEqual(unescape(heading), article['title'])
                schema = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))
                self.assertEqual(schema['headline'], article['title'])
                self.assertEqual(schema['description'], item['excerpt'])
                summary = re.search(r'<section class="article-summary">(.*?)</section>', html, re.S).group(1)
                for point in item['points']:
                    self.assertIn(escape(point['text']), summary)
                    self.assertIn(f'href="#section-{point["section"]}"', summary)
                    self.assertTrue(article['sections'][point['section']]['paragraphs'])

    def test_original_article_text(self):
        for article in json.loads((ROOT/'content/articles.json').read_text(encoding='utf-8')):
            expected = []
            for section in article['sections']:
                expected.append(section['heading'])
                for p in section['paragraphs']:
                    if isinstance(p, str): expected.append(p)
                    elif 'markdown' in p: expected.append(p['markdown'].replace('**', ''))
                    elif 'table' in p: expected.extend(cell for row in p['table'] for cell in row)
                for comment in section.get('comments', []):
                    for p in comment.get('paragraphs', []):
                        if isinstance(p, str): expected.append(p)
                        elif 'markdown' in p: expected.append(p['markdown'].replace('**', ''))
                        elif 'table' in p: expected.extend(cell for row in p['table'] for cell in row)
            page = Page((ROOT/'docs/articles'/article['slug']/'index.html').read_text(encoding='utf-8'))
            self.assertEqual(normalized(''.join(expected)), normalized(''.join(page.prose)), article['slug'])

    def test_fragments_and_image_dimensions(self):
        for path in (ROOT/'docs').rglob('*.html'):
            page = Page(path.read_text(encoding='utf-8'))
            self.assertTrue(set(page.fragments) <= page.ids, str(path))
            for image in page.images:
                if '/assets/articles/' in image.get('src', ''):
                    self.assertGreater(int(image['width']), 0)
                    self.assertGreater(int(image['height']), 0)

    def test_static_pagination_controls(self):
        total = 1 + len(json.loads((ROOT/'content/catalog.json').read_text(encoding='utf-8')))
        for number in range(1, (total+19)//20+1):
            path = ROOT/'docs/articles'/('index.html' if number == 1 else f'page/{number}/index.html')
            page = Page(path.read_text(encoding='utf-8'))
            self.assertTrue({'results','page-number','page-jump','prev-page','next-page','search'} <= page.ids)
            self.assertEqual(page.visible_rows, min(20, total-(number-1)*20))

if __name__ == '__main__':
    unittest.main()
