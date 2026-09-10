"""Create and apply manually configured, source-verified Markdown reviews."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def plain(markdown):
    value = re.sub(r"(?<!\\)\*\*", "", markdown)
    return value.replace(r"\*\*", "**")


def marked(block):
    return "".join(
        f"**{run['text']}**" if run["bold"] else run["text"].replace("**", r"\*\*")
        for run in block["runs"]
    )


def split_marked(block, parts):
    """Split one source paragraph without changing text or Word bold runs."""
    assert parts and "".join(parts) == block["text"], "Paragraph splits must reproduce the source text exactly"
    boundaries = []
    offset = 0
    for part in parts:
        boundaries.append((offset, offset + len(part)))
        offset += len(part)
    result = []
    run_start = 0
    for part_start, part_end in boundaries:
        fragments = []
        run_start = 0
        for run in block["runs"]:
            run_end = run_start + len(run["text"])
            start = max(part_start, run_start)
            end = min(part_end, run_end)
            if start < end:
                value = run["text"][start - run_start:end - run_start]
                fragments.append(f"**{value}**" if run["bold"] else value.replace("**", r"\*\*"))
            run_start = run_end
        result.append("".join(fragments))
    return result


def create(packet_path, config_path, output_path):
    packet = {item["slug"]: item for item in json.loads(Path(packet_path).read_text(encoding="utf-8"))}
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    item = packet[config["slug"]]
    source_paragraphs = {block["text"] for block in item["blocks"] if block["text"].strip()}
    assert config["description"] in source_paragraphs, "Description must be one complete source paragraph"
    assert all(point["text"] in source_paragraphs for point in config["key_points"]), "Key points must be complete source paragraphs"
    headings = {int(key): value for key, value in config["headings"].items()}
    splits = {int(key): value for key, value in config.get("splits", {}).items()}
    split_headings = {int(key): value for key, value in config.get("split_headings", {}).items()}
    comments = {index: comment for comment in config.get("comments", []) for index in range(comment["start"], comment["end"] + 1)}
    meta = {
        "slug": config.get("target_slug", item["slug"]), "title": item["title"],
        "author": config.get("author", item["author"]),
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
        parts = splits.get(block["paragraph"], [block["text"]])
        marked_parts = split_marked(block, parts) if block["text"] else []
        assert not (block["paragraph"] in headings and len(marked_parts) > 1), "Heading paragraphs cannot also be split"
        levels = split_headings.get(block["paragraph"], [0] * len(marked_parts))
        assert len(levels) == len(marked_parts), "Split heading levels must match paragraph parts"
        assert not (block["paragraph"] in headings and block["paragraph"] in split_headings), "Use one heading configuration per paragraph"
        assert all(level in {0, 2, 3, 4} for level in levels), "Split heading levels must be 0 or 2-4"
        for text, level in zip(marked_parts, levels):
            if text and (block["paragraph"] in headings or level):
                lines.extend(["#" * (headings.get(block["paragraph"]) or level) + " " + text, ""])
            elif text:
                lines.extend([text, ""])
        for image in block["images"]:
            lines.extend([f"![{item['title']}：原文配图](/blog/{image})", ""])
    if active_comment is not None:
        lines.extend(["<!-- 原文评论结束 -->", ""])
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    verify(output, item, splits)


def verify(markdown_path, source_item, splits=None):
    splits = splits or {}
    text = Path(markdown_path).read_text(encoding="utf-8").split("<!-- 原文开始 -->", 1)[1]
    paragraphs = []
    markdown_paragraphs = []
    images = []
    for part in re.split(r"\n\s*\n", text.strip("\n")):
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
    expected = [part for block in source_item["blocks"] if block["text"].strip()
                for part in splits.get(block["paragraph"], [block["text"]])]
    assert paragraphs == expected, "Reviewed Markdown changed source text"
    expected_markdown = [part for block in source_item["blocks"] if block["text"].strip()
                         for part in (split_marked(block, splits[block["paragraph"]])
                                      if block["paragraph"] in splits else [marked(block)])]
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
    for part in re.split(r"\n\s*\n", body.strip("\n")):
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
