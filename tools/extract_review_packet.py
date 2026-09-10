"""Extract one catalogued DOCX into lossless paragraph-level review packets.

This is intentionally a review aid, not an automatic editor. It preserves the
visible paragraph text and records Word bold runs, paragraph styles, hyperlinks,
and image anchors so a human can decide the Markdown structure.
"""
import json
import hashlib
import sys
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "v": "urn:schemas-microsoft-com:vml",
}


def visible_text(node):
    return "".join(part.text or "" for part in node.findall(".//w:t", NS))


def run_fragments(paragraph):
    fragments = []
    for run in paragraph.findall(".//w:r", NS):
        value = visible_text(run)
        if not value:
            continue
        bold = run.find("w:rPr/w:b", NS)
        fragments.append({
            "text": value,
            "bold": bold is not None and bold.get(f"{{{NS['w']}}}val", "1") not in {"0", "false"},
        })
    return fragments


def main(source_dir, document_name, output):
    catalog = json.loads((ROOT / "content/catalog.json").read_text(encoding="utf-8"))
    entries = sorted(
        [item for item in catalog if item["source"]["document"] == document_name],
        key=lambda item: item["source"]["titleParagraphs"][0],
    )
    with ZipFile(Path(source_dir) / document_name) as archive:
        body = ET.fromstring(archive.read("word/document.xml")).find("w:body", NS)
        paragraphs = body.findall("w:p", NS)
        relationships = {
            node.attrib["Id"]: node.attrib
            for node in ET.fromstring(archive.read("word/_rels/document.xml.rels"))
        }
        packet = []
        for position, item in enumerate(entries):
            title_ids = set(item["source"]["titleParagraphs"])
            start = min(title_ids)
            end = entries[position + 1]["source"]["titleParagraphs"][0] if position + 1 < len(entries) else len(paragraphs)
            blocks = []
            for index in range(start, end):
                paragraph = paragraphs[index]
                if index in title_ids:
                    continue
                value = visible_text(paragraph)
                embeds = [node.get(f"{{{NS['r']}}}embed") for node in paragraph.findall(".//a:blip", NS)]
                embeds += [node.get(f"{{{NS['r']}}}id") for node in paragraph.findall(".//v:imagedata", NS)]
                images = []
                for relationship_id in [value for value in embeds if value]:
                    target = relationships[relationship_id]["Target"]
                    member = target.lstrip("/") if target.startswith("/") else str(PurePosixPath("word") / target)
                    data = archive.read(member)
                    suffix = Path(member).suffix.lower().replace(".jpeg", ".jpg")
                    relative = f"assets/articles/docx/{hashlib.sha256(data).hexdigest()[:24]}{suffix}"
                    destination = ROOT / "docs" / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    if destination.exists():
                        assert destination.read_bytes() == data, f"Image hash collision: {relative}"
                    else:
                        destination.write_bytes(data)
                    images.append(relative)
                if not value.strip() and not any(embeds):
                    continue
                style = paragraph.find("w:pPr/w:pStyle", NS)
                blocks.append({
                    "paragraph": index,
                    "style": style.get(f"{{{NS['w']}}}val") if style is not None else "",
                    "text": value,
                    "runs": run_fragments(paragraph),
                    "images": images,
                })
            packet.append({
                "slug": item["slug"],
                "title": item["title"],
                "author": item["author"],
                "source_start": start,
                "source_end": end,
                "blocks": blocks,
            })
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(packet)} articles to {output}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
