"""Import Zhang Chengfeng's two emailed DOCX articles without rewriting them."""

import hashlib
import json
import re
from pathlib import Path

from import_email_submissions import source_lines, styled_text, split_long, normalize

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content/submissions/2026-09-22"
SUBMISSIONS = (
    ("17. 黑社会的诞生.docx", "zhang-chengfeng-online-underworld", "authority", "speech"),
    ("18. 张健柏性压抑.docx", "zhang-chengfeng-sexual-repression", "authority", "speech"),
)


def main():
    article_path = ROOT / "content/articles.json"
    catalog_path = ROOT / "content/catalog.json"
    articles = json.loads(article_path.read_text(encoding="utf-8"))
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    presentation = json.loads((ROOT / "content/presentation.json").read_text(encoding="utf-8"))
    assert not any(a["slug"] in {x[1] for x in SUBMISSIONS} for a in articles)
    audit, additions, entries = [], [], []
    for filename, slug, category, topic in SUBMISSIONS:
        path = SOURCE / filename
        lines = [styled_text(line) for line in source_lines(path)]
        title = lines[0].replace("**", "")
        sections = [{"heading": "", "paragraphs": []}]
        image_index = {19: 1, 20: 2, 32: 3} if slug == "zhang-chengfeng-sexual-repression" else {}
        for index, line in enumerate(lines[1:], start=1):
            if index in image_index:
                number = image_index[index]
                sections[-1]["paragraphs"].append({
                    "image": f"assets/articles/zhang-chengfeng-sexual-repression/image{number}.png",
                    "alt": f"张乘风原稿配图 {number}",
                })
                continue
            if not line:
                continue
            plain = line.replace("**", "")
            if slug.endswith("sexual-repression") and plain in ("继续侃老张的情史", "颅内高潮期"):
                sections.append({"heading": plain, "paragraphs": []})
                continue
            if slug.endswith("online-underworld") and plain == "我们可以看到，2025年之后，张又明显做了几个调整：":
                sections.append({"heading": plain, "paragraphs": []})
                continue
            for part in split_long(line):
                sections[-1]["paragraphs"].append({"markdown": part} if "**" in part else part)

        source_body = "".join(normalize(line) for line in lines[1:])
        rendered_body = "".join(normalize(section["heading"]) + "".join(
            normalize(p["markdown"] if isinstance(p, dict) and "markdown" in p else p)
            for p in section["paragraphs"] if isinstance(p, str) or "markdown" in p
        ) for section in sections)
        assert source_body == rendered_body, f"Word text changed: {filename}"
        article = {
            "slug": slug, "title": title, "author": "张乘风", "category": category,
            "tags": ["zhang-chengfeng"], "source": f"submissions/2026-09-22/{filename}",
            "summary": presentation[slug]["excerpt"], "excerpt": [presentation[slug]["excerpt"]],
            "sections": sections, "showOnHome": True,
        }
        additions.append(article)
        entries.append({
            "slug": slug, "title": title, "author": "张乘风", "category": category,
            "topic": topic, "tags": ["zhang-chengfeng"], "kind": "文章",
            "source": {"document": f"submissions/2026-09-22/{filename}"}, "article": slug,
        })
        audit.append({"slug": slug, "source": filename, "sourceSHA256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "bodyCharacters": len(source_body), "sections": len(sections)})

    article_path.write_text(json.dumps(articles + additions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    catalog_path.write_text(json.dumps(entries + catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (SOURCE / "import-audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Imported 2 Zhang Chengfeng articles; source text verified.")


if __name__ == "__main__":
    main()
