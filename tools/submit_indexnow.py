#!/usr/bin/env python3
"""Submit the archive's sitemap URLs to IndexNow.

The verification key is discovered from docs/<key>.txt, where the filename and
file contents must match.  Only URLs on the site's canonical host are accepted.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SITEMAP = ROOT / "docs" / "sitemap.xml"
DEFAULT_ENDPOINT = "https://api.indexnow.org/indexnow"
CANONICAL_HOST = "zhangjianbai-archive.github.io"
SITE_PREFIX = f"https://{CANONICAL_HOST}/blog/"


def discover_key_file(docs: Path) -> Path:
    candidates = []
    for path in docs.glob("*.txt"):
        key = path.read_text(encoding="utf-8").strip()
        if re.fullmatch(r"[A-Za-z0-9-]{8,128}", key) and path.stem == key:
            candidates.append(path)
    if len(candidates) != 1:
        raise ValueError(
            f"Expected exactly one IndexNow key file in {docs}, found {len(candidates)}"
        )
    return candidates[0]


def sitemap_urls(path: Path) -> list[str]:
    root = ElementTree.parse(path).getroot()
    urls = [node.text.strip() for node in root.findall("{*}url/{*}loc") if node.text]
    if not urls:
        raise ValueError(f"No URLs found in {path}")
    return urls


def validate_urls(urls: list[str]) -> list[str]:
    unique = list(dict.fromkeys(urls))
    invalid = [url for url in unique if not url.startswith(SITE_PREFIX)]
    if invalid:
        raise ValueError(f"URL is outside {SITE_PREFIX}: {invalid[0]}")
    return unique


def submit(endpoint: str, payload: dict[str, object]) -> int:
    request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        return response.status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="*", help="Specific canonical URLs; defaults to the sitemap")
    parser.add_argument("--sitemap", type=Path, default=DEFAULT_SITEMAP)
    parser.add_argument("--key-file", type=Path)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    key_file = args.key_file or discover_key_file(args.sitemap.resolve().parent)
    key = key_file.read_text(encoding="utf-8").strip()
    if key_file.stem != key:
        raise ValueError("IndexNow key filename and contents do not match")

    urls = validate_urls(args.urls or sitemap_urls(args.sitemap))
    payload = {
        "host": CANONICAL_HOST,
        "key": key,
        "keyLocation": f"{SITE_PREFIX}{key}.txt",
        "urlList": urls,
    }

    if args.dry_run:
        print(f"Validated {len(urls)} URLs for {payload['host']}")
        print(f"Key location: {payload['keyLocation']}")
        return 0

    try:
        status = submit(args.endpoint, payload)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace").strip()
        print(f"IndexNow rejected the submission: HTTP {error.code} {detail}", file=sys.stderr)
        return 1
    except URLError as error:
        print(f"IndexNow request failed: {error.reason}", file=sys.stderr)
        return 1

    if status not in (200, 202):
        print(f"Unexpected IndexNow response: HTTP {status}", file=sys.stderr)
        return 1
    print(f"IndexNow accepted {len(urls)} URLs (HTTP {status}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
