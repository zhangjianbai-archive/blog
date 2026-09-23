"""Publish the four 2026-09-23 Huang Chuanke DOCX submissions.

Only presentation changes are made: Word line breaks become paragraphs, long
paragraphs may be split at sentence boundaries, and existing bold is retained.
An assertion compares every source character (ignoring whitespace) with the
published body, so editorial formatting cannot silently alter the wording.
"""

import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content/submissions/2026-09-23"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
TAG = lambda name: f"{{{W}}}{name}"

# Inbox order, newest first. CK and Caocao are intentionally not imported.
SUBMISSIONS = [
    ("钱莉拙劣的调查报告，与其说是幸福度调查，不如说是邪教传单.docx", "huang-chuanke-qianli-survey", "authority", "system"),
    ("“世界第一教育的神话，是怎么被一篇公关文编出来的.docx", "huang-chuanke-world-first-claim", "teaching", "outcomes"),
    ("悼亡诛心：一场网暴逼死的人伦惨剧，一桩三观崩塌的人间悲剧.docx", "huang-chuanke-daowang-zhuxin", "authority", "speech"),
    ("评王新昌文章.docx", "huang-chuanke-on-wang-xinchang", "authority", "system"),
]

# Light editorial emphasis, without changing the author's words.
EMPHASIS = {
    "huang-chuanke-qianli-survey": ("两组样本完全不对等，没有统计意义。", "幸福度调查太虚了，主观性太强"),
    "huang-chuanke-world-first-claim": ("这些学生本身就是经过层层筛选入学的。", "这些都是单项指标。"),
    "huang-chuanke-on-wang-xinchang": ("并不是全部参与者的随机抽样。", "不等于实际参与该教育的家庭中满意 / 不满意的人口比例。"),
}


def source_lines(path):
    """Return (text, bold spans) lines, honoring both p and manual br nodes."""
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    parents = {}
    def visit(node, ancestors=()):
        for child in node:
            parents[child] = (node, *ancestors)
            visit(child, (node, *ancestors))
    visit(root)
    body = root.find(TAG("body"))
    lines = []
    for paragraph in body.findall(TAG("p")):
        line = []
        for node in paragraph.iter():
            if node.tag == TAG("br"):
                lines.append(line)
                line = []
            elif node.tag == TAG("t"):
                # Word text nodes are always descendants of a run.
                run = next((ancestor for ancestor in parents[node] if ancestor.tag == TAG("r")), None)
                bold = run is not None and run.find(f"{TAG('rPr')}/{TAG('b')}") is not None
                line.append((node.text or "", bold))
            elif node.tag == TAG("tab"):
                line.append(("\t", False))
        lines.append(line)
    return lines


def styled_text(chunks):
    out = []
    bold = False
    for value, is_bold in chunks:
        if not value:
            continue
        if is_bold != bold:
            out.append("**")
            bold = is_bold
        out.append(value)
    if bold:
        out.append("**")
    return "".join(out).strip()


def split_long(text):
    """Break dense prose at punctuation only; never change its characters."""
    if len(text) <= 185 or "**" in text:
        return [text]
    pieces = re.split(r"(?<=[。！？])", text)
    if len(pieces) == 1:
        return [text]
    output, current = [], ""
    for piece in pieces:
        if current and len(current) + len(piece) > 165:
            output.append(current)
            current = ""
        current += piece
    if current:
        output.append(current)
    return output


def is_heading(slug, text):
    plain = text.replace("**", "").strip()
    if slug == "huang-chuanke-world-first-claim":
        return plain == "结论" or bool(re.match(r"^硬伤[一二三四]：", plain))
    if slug == "huang-chuanke-on-wang-xinchang":
        return bool(re.match(r"^[1-3]\.\s", plain))
    return bool(re.match(r"^[一二三四五六][、，]", plain))


def normalize(text):
    return re.sub(r"\s+", "", text.replace("**", ""))


def main():
    article_path = ROOT / "content/articles.json"
    catalog_path = ROOT / "content/catalog.json"
    presentation = json.loads((ROOT / "content/presentation.json").read_text(encoding="utf-8"))
    articles = json.loads(article_path.read_text(encoding="utf-8"))
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert not any(a["slug"] in {x[1] for x in SUBMISSIONS} for a in articles), "Already imported"
    audit = []
    additions = []
    entries = []
    for filename, slug, category, topic in SUBMISSIONS:
        path = SOURCE / filename
        lines = source_lines(path)
        raw = [styled_text(line) for line in lines if styled_text(line)]
        title = raw.pop(0) if slug != "huang-chuanke-on-wang-xinchang" else "评王新昌文章"
        title = title.replace("**", "")
        sections = [{"heading": "", "paragraphs": []}]
        for line in raw:
            if is_heading(slug, line):
                sections.append({"heading": line.replace("**", ""), "paragraphs": []})
            else:
                for phrase in EMPHASIS.get(slug, ()):
                    line = line.replace(phrase, f"**{phrase}**")
                for part in split_long(line):
                    sections[-1]["paragraphs"].append({"markdown": part} if "**" in part else part)
        original = "".join(normalize(line) for line in raw)
        output = "".join(normalize(s["heading"]) + "".join(normalize(p["markdown"] if isinstance(p, dict) else p) for p in s["paragraphs"]) for s in sections)
        assert original == output, f"Text mismatch: {filename}"
        article = {
            "slug": slug, "title": title, "author": "黄传科", "category": category,
            "tags": ["huang-chuanke"], "source": f"submissions/2026-09-23/{filename}",
            "summary": presentation[slug]["excerpt"], "excerpt": [presentation[slug]["excerpt"]], "sections": sections,
            "showOnHome": True,
        }
        additions.append(article)
        entries.append({
            "slug": slug, "title": title, "author": "黄传科", "category": category,
            "topic": topic, "tags": ["huang-chuanke"], "kind": "文章",
            "source": {"document": f"submissions/2026-09-23/{filename}"}, "article": slug,
        })
        audit.append({"slug": slug, "source": filename, "sourceSHA256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "bodyCharacters": len(original), "sections": len(sections), "paragraphs": sum(len(s["paragraphs"]) for s in sections)})
    article_path.write_text(json.dumps(articles + additions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    catalog_path.write_text(json.dumps(entries + catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (SOURCE / "import-audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(additions)} articles; all non-whitespace source characters verified.")


if __name__ == "__main__":
    main()
