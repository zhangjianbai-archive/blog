"""Print possible interrupted sentences for manual review; never change text."""
import json
import sys
from pathlib import Path

for path in map(Path, sys.argv[1:]):
    for article in json.loads(path.read_text(encoding='utf-8')):
        for left, right in zip(article['blocks'], article['blocks'][1:]):
            if right['text'].startswith(('”', '》', '的玄妙', '告诉我们')):
                print(article['slug'], left['paragraph'], right['paragraph'], left['text'][-65:]+' → '+right['text'][:80])
