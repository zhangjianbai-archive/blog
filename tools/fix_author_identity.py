"""Mechanical metadata correction; never rewrite original article bodies."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD, NEW = '嘲笑鸟飞起时', '嘲笑鸟'

def metadata(value):
    if isinstance(value, list):
        return [metadata(item) for item in value]
    if isinstance(value, dict):
        # These are editorial summaries, not the source article body or its
        # provenance filename. Preserve every original quotation verbatim.
        return {key: (NEW if key in {'author', 'name'} and item == OLD else
                      item.replace(OLD, NEW) if key in {'description', 'text', 'introduction', 'summary', 'excerpt'} and isinstance(item, str) else
                      [part.replace(OLD, NEW) if isinstance(part, str) else metadata(part) for part in item] if key == 'excerpt' and isinstance(item, list) else
                      metadata(item)) for key, item in value.items()}
    return value

paths = [ROOT/'content'/name for name in ['articles.json', 'catalog.json', 'authors.json', 'presentation.json']]
paths += list((ROOT/'review').glob('*-config.json'))
for path in paths:
    original = path.read_text(encoding='utf-8')
    value = json.loads(original)
    changed = metadata(value)
    if changed != value:
        path.write_text(json.dumps(changed, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
for path in (ROOT/'content/posts').glob('*.md'):
    original = path.read_text(encoding='utf-8')
    if not original.startswith('<!--ARCHIVE-META\n'):
        continue
    header, body = original.split('-->', 1)
    value = json.loads(header.removeprefix('<!--ARCHIVE-META\n'))
    changed = metadata(value)
    if changed != value:
        path.write_text('<!--ARCHIVE-META\n'+json.dumps(changed, ensure_ascii=False, indent=2)+'\n-->'+body, encoding='utf-8')
