"""Restore one verified DOCX table omitted from an imported article."""
import json
import sys
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
SLUG = "collection-03-0401"
ANCHOR = "以下为当时武道学校刘某的考勤情况："
TABLE_TITLE = "2021年12月静慧出勤表"


def text(node):
    return "".join(part.text or "" for part in node.findall(".//w:t", NS))


def main(source):
    with ZipFile(source) as archive:
        body = ET.fromstring(archive.read("word/document.xml")).find("w:body", NS)
    matches = [node for node in body.findall("w:tbl", NS) if text(node).startswith(TABLE_TITLE)]
    assert len(matches) == 1, "Expected exactly one attendance table"
    table = [[text(cell) for cell in row.findall("w:tc", NS)]
             for row in matches[0].findall("w:tr", NS)]
    assert len(table) == 20 and "".join("".join(row) for row in table) == text(matches[0])
    path = ROOT / "content/articles.json"
    articles = json.loads(path.read_text(encoding="utf-8"))
    article = next(item for item in articles if item["slug"] == SLUG)
    locations = [(section, index) for section in article["sections"]
                 for index, paragraph in enumerate(section["paragraphs"])
                 if isinstance(paragraph, dict) and paragraph.get("markdown") == ANCHOR]
    assert len(locations) == 1, "Expected exactly one insertion point"
    section, index = locations[0]
    existing = [item for part in article["sections"] for item in part["paragraphs"] if isinstance(item, dict) and "table" in item]
    if existing:
        assert existing == [{"table": table}], "Article already has a different table"
        return
    section["paragraphs"].insert(index + 1, {"table": table})
    path.write_text(json.dumps(articles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
