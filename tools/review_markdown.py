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
    source_paragraphs = {block["text"] for block in item["blocks"] if block["text"].strip()}
    assert config["description"] in source_paragraphs, "Description must be one complete source paragraph"
    assert all(point["text"] in source_paragraphs for point in config["key_points"]), "Key points must be complete source paragraphs"
    headings = {int(key): value for key, value in config["headings"].items()}
    comments = {index: comment for comment in config.get("comments", []) for index in range(comment["start"], comment["end"] + 1)}
    meta = {
        "slug": config.get("target_slug", item["slug"]), "title": item["title"], "author": item["author"],
        "source": config["source"], "source_start": item["source_start"], "source_end": item["source_end"],
        "description": config["description"], "key_points": config["key_points"],
    }
    lines = ["<!--ARCHIVE-META", json.dumps(meta, ensure_ascii=False, indent=2), "-->", "", f"# {item['title']}", "", "<!-- 原文开始 -->", ""]
    active_comment = None
    for index, block in enumerate(item["blocks"]):
        comment = comments.get(index)
        if comment != active_comment:
            if active_comment is not None:
                lines.extend(["<!-- 原文评论结束 -->", ""])
            if comment is not None:
                payload = {key: value for key, value in comment.items() if key not in {"start", "end"}}
                lines.extend([f"<!-- 原文评论开始 {json.dumps(payload, ensure_ascii=False)} -->", ""])
            active_comment = comment
        text = marked(block)
        if text and block["paragraph"] in headings:
            lines.extend(["#" * headings[block["paragraph"]] + " " + text, ""])
        elif text:
            lines.extend([text, ""])
        for image in block["images"]:
            lines.extend([f"![{item['title']}：原文配图](/blog/{image})", ""])
    if active_comment is not None:
        lines.extend(["<!-- 原文评论结束 -->", ""])
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    verify(output, item)


def verify(markdown_path, source_item):
    text = Path(markdown_path).read_text(encoding="utf-8").split("<!-- 原文开始 -->", 1)[1]
    paragraphs = []
    markdown_paragraphs = []
    images = []
    for part in re.split(r"\n\s*\n", text.strip()):
        if part.startswith("<!-- 原文评论"):
            continue
        value = re.sub(r"^#{2,4} ", "", part)
        if value.startswith("!["):
            image = re.fullmatch(r"!\[.*\]\(/blog/(assets/articles/docx/[a-z0-9]+\.(?:png|jpg|webp))\)", value)
            assert image, "Invalid reviewed image"
            images.append(image.group(1))
        else:
            markdown_paragraphs.append(value)
            paragraphs.append(plain(value))
    expected = [block["text"] for block in source_item["blocks"] if block["text"].strip()]
    assert paragraphs == expected, "Reviewed Markdown changed source text"
    expected_markdown = [marked(block) for block in source_item["blocks"] if block["text"].strip()]
    assert markdown_paragraphs == expected_markdown, "Reviewed Markdown changed source bold formatting"
    expected_images = [image for block in source_item["blocks"] for image in block["images"]]
    assert images == expected_images, "Reviewed Markdown changed source image order"


def apply(markdown_path):
    raw = Path(markdown_path).read_text(encoding="utf-8")
    metadata_raw, body = raw.split("-->", 1)
    metadata = json.loads(metadata_raw.removeprefix("<!--ARCHIVE-META").strip())
    body = body.split("<!-- 原文开始 -->", 1)[1]
    sections = [{"heading": "", "paragraphs": []}]
    active_comment = None
    for part in re.split(r"\n\s*\n", body.strip()):
        comment_start = re.fullmatch(r"<!-- 原文评论开始 (\{.*\}) -->", part, re.S)
        if comment_start:
            active_comment = {**json.loads(comment_start.group(1)), "paragraphs": []}
            sections[-1]["comments"] = sections[-1].get("comments", []) + [active_comment]
            continue
        if part == "<!-- 原文评论结束 -->":
            active_comment = None
            continue
        heading = re.match(r"^(#{2,4}) (.*)$", part, re.S)
        if heading:
            sections.append({"heading": plain(heading.group(2)), "paragraphs": [], "level": len(heading.group(1))})
        elif part.startswith("!["):
            image = re.fullmatch(r"!\[(.*)\]\(/blog/(assets/articles/docx/[a-z0-9]+\.(?:png|jpg|webp))\)", part)
            assert image, "Invalid reviewed image"
            target = active_comment["paragraphs"] if active_comment is not None else sections[-1]["paragraphs"]
            target.append({"image": image.group(2), "alt": image.group(1)})
        else:
            target = active_comment["paragraphs"] if active_comment is not None else sections[-1]["paragraphs"]
            target.append({"markdown": part})
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
