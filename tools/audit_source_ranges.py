"""Read-only source comparison; flags are review leads, not automatic fixes."""
import json
import difflib
import re
import sys
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def text(node):
    return ''.join(t.text or '' for t in node.findall('.//w:t', NS))

def norm(s):
    return re.sub(r'\s+|\*\*', '', s)

def body(article, editorial_headings=()):
    values = []
    for section in article['sections']:
        if section['heading'] not in editorial_headings:
            values.append(section['heading'])
        for item in [*section['paragraphs'], *[p for c in section.get('comments', []) for p in c['paragraphs']]]:
            if isinstance(item, str):
                values.append(item)
            elif 'markdown' in item:
                values.append(re.sub(r'\[([^]]+)\]\([^)]+\)', r'\1', item['markdown']))
            elif 'table' in item:
                values.extend(cell for row in item['table'] for cell in row)
    return norm(''.join(values))

def run(directory):
    catalog = [a for a in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf-8')) if a['source'].get('titleParagraphs')]
    articles = {a['slug']: a for a in json.loads((ROOT/'content/articles.json').read_text(encoding='utf-8'))}
    docs = sorted({a['source'].get('document') for a in catalog if a['source'].get('document')})
    report = []
    for document in docs:
        source = directory/document
        if not source.exists():
            source = ROOT/'content'/document
        with ZipFile(source) as archive:
            nodes = ET.fromstring(archive.read('word/document.xml')).find('w:body', NS)
            paragraphs = nodes.findall('w:p', NS)
            entries = sorted([a for a in catalog if a['source'].get('document') == document], key=lambda a: min(a['source']['titleParagraphs']))
            for pos, entry in enumerate(entries):
                titles = entry['source']['titleParagraphs']
                start = min(titles)
                end = min(entries[pos+1]['source']['titleParagraphs']) if pos+1 < len(entries) else len(paragraphs)
                blocks = []; index = -1
                for node in nodes:
                    if node.tag == '{'+NS['w']+'}p':
                        index += 1
                    if start <= index < end and index not in titles:
                        value = text(node)
                        if value.strip():
                            blocks.append({'paragraph': index, 'text': value})
                article = articles.get(entry.get('article'))
                expected = norm(''.join(b['text'] for b in blocks))
                markdown = ROOT/'content/posts'/f'{entry.get("article", entry["slug"])}.md'
                editorial_headings = []
                if markdown.exists():
                    editorial_headings = [json.loads(value)['text'] for value in re.findall(r'<!-- 编辑目录标题 (\{.*?\}) -->', markdown.read_text(encoding='utf-8'))]
                actual = body(article, editorial_headings) if article else ''
                row = {'slug': entry['slug'], 'document': document, 'start': start, 'end': end,
                       'source_chars': len(expected), 'site_chars': len(actual), 'text_matches': expected == actual,
                       'last_blocks': blocks[-3:]}
                if article:
                    row['long_headings'] = [{'section': i, 'text': s['heading']} for i,s in enumerate(article['sections']) if len(s['heading']) > 60]
                row['editorial_headings'] = editorial_headings
                if expected != actual:
                    row['differences'] = [{'kind': tag, 'source': expected[i:j], 'site': actual[k:l], 'context': expected[max(0,i-25):i]}
                        for tag,i,j,k,l in difflib.SequenceMatcher(None, expected, actual, autojunk=False).get_opcodes() if tag != 'equal']
                report.append(row)
    target = ROOT/'review/source-range-audit.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'{len(report)} ranges audited; {sum(r["text_matches"] for r in report)} exact normalized text matches; {sum(not r["text_matches"] for r in report)} require examination.')

if __name__ == '__main__':
    run(Path(sys.argv[1]))
