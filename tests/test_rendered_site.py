"""Run after build.py: preserve source text and verify reading/navigation output."""
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

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
    def test_original_article_text(self):
        for article in json.loads((ROOT/'content/articles.json').read_text(encoding='utf-8')):
            expected = []
            for section in article['sections']:
                expected.append(section['heading'])
                for p in section['paragraphs']:
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
        total = len(json.loads((ROOT/'content/catalog.json').read_text(encoding='utf-8')))
        for number in range(1, (total+19)//20+1):
            path = ROOT/'docs/articles'/('index.html' if number == 1 else f'page/{number}/index.html')
            page = Page(path.read_text(encoding='utf-8'))
            self.assertTrue({'results','readable-only','prev-page','next-page','search'} <= page.ids)
            self.assertEqual(page.visible_rows, min(20, total-(number-1)*20))

if __name__ == '__main__':
    unittest.main()
