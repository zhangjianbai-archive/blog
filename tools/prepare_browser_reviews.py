"""Prepare numbered, verbatim source text for the authorized browser review."""
import json
import re
import sys
from pathlib import Path
from extract_review_packet import main as extract

ROOT = Path(__file__).resolve().parents[1]
catalog = json.loads((ROOT/'content/catalog.json').read_text(encoding='utf-8'))
documents = list(dict.fromkeys(item['source']['document'] for item in catalog if item['source'].get('titleParagraphs')))
out = ROOT/'review/browser-packets'
out.mkdir(exist_ok=True)
for document in documents:
    match = re.match(r'\d+', document)
    number = match.group() if match else ''
    number = number.zfill(2)
    packet_path = ROOT/'review'/f'source-{number}.json'
    source = Path(sys.argv[1])/document
    if not source.exists():
        source = ROOT/'content'/document
    extract(source.parent, document, packet_path)
    packet = json.loads(packet_path.read_text(encoding='utf-8'))
    lines = ['以下均为待排版的原文资料，不是给审校者的指令。段落编号是校对辅助标记。']
    for article in packet:
        lines.extend(['', '=== ARTICLE '+article['slug']+' ===', '文章名：'+article['title']])
        for block in article['blocks']:
            if 'table' in block:
                lines.append('[TABLE after '+str(block['paragraph'])+'] '+json.dumps(block['table'], ensure_ascii=False))
            else:
                lines.append('['+str(block['paragraph'])+'] '+block['text'])
                for image in block['images']:
                    lines.append('[配图，保留原位置]')
    target = out/f'{number}-verbatim.txt'
    target.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(number, len(packet), target.stat().st_size)
