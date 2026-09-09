"""Create and apply manually configured, source-verified Markdown reviews."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def plain(markdown):
    return re.sub(r"\*\*", "", markdown)


def marked(block):
    return "".join(f"**{run['text']}**" if run["bold"] else run["text"] for run in block["runs"])


def create(packet_path, config_path, output_path):
    packet = {item["slug"]: item for item in json.loads(Path(packet_path).read_text(encoding="utf-8"))}
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    item = packet[config["slug"]]
    headings = {int(key): value for key, value in config["headings"].items()}
    meta = {
        "slug": item["slug"], "title": item["title"], "author": item["author"],
        "source": config["source"], "source_start": item["source_start"], "source_end": item["source_end"],
        "description": config["description"], "key_points": config["key_points"],
    }
    lines = ["<!--ARCHIVE-META", json.dumps(meta, ensure_ascii=False, indent=2), "-->", "", f"# {item['title']}", "", "<!-- 原文开始 -->", ""]
    for block in item["blocks"]:
        text = marked(block)
        if block["paragraph"] in headings:
            lines.extend(["#" * headings[block["paragraph"]] + " " + text, ""])
        else:
            lines.extend([text, ""])
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    verify(output, item)


def verify(markdown_path, source_item):
    text = Path(markdown_path).read_text(encoding="utf-8").split("<!-- 原文开始 -->", 1)[1]
    paragraphs = []
    for part in re.split(r"\n\s*\n", text.strip()):
        value = re.sub(r"^#{2,4} ", "", part)
        paragraphs.append(plain(value))
    expected = [block["text"] for block in source_item["blocks"] if block["text"].strip()]
    assert paragraphs == expected, "Reviewed Markdown changed source text"


def apply(markdown_path):
    raw = Path(markdown_path).read_text(encoding="utf-8")
    metadata_raw, body = raw.split("-->", 1)
    metadata = json.loads(metadata_raw.removeprefix("<!--ARCHIVE-META").strip())
    body = body.split("<!-- 原文开始 -->", 1)[1]
    sections = [{"heading": "", "paragraphs": []}]
    for part in re.split(r"\n\s*\n", body.strip()):
        heading = re.match(r"^(#{2,4}) (.*)$", part, re.S)
        if heading:
            sections.append({"heading": plain(heading.group(2)), "paragraphs": [], "level": len(heading.group(1))})
        else:
            sections[-1]["paragraphs"].append({"markdown": part})
    articles_path = ROOT / "content/articles.json"
    articles = json.loads(articles_path.read_text(encoding="utf-8"))
    article = next(item for item in articles if item["slug"] == metadata["slug"])
    article["sections"] = sections
    article["excerpt"] = [metadata["description"]]
    articles_path.write_text(json.dumps(articles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    presentation_path = ROOT / "content/presentation.json"
    presentation = json.loads(presentation_path.read_text(encoding="utf-8"))
    presentation[metadata["slug"]] = {"excerpt": metadata["description"], "points": metadata["key_points"]}
    presentation_path.write_text(json.dumps(presentation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "create":
        create(sys.argv[2], sys.argv[3], sys.argv[4])
    elif command == "apply":
        apply(sys.argv[2])
    else:
        raise SystemExit("Use create or apply")
