"""Validate a successful Metrics render before activating its README image."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
import os
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET


START = "<!-- METRICS:START -->"
END = "<!-- METRICS:END -->"
ACTIVE = '''<p align="center">
  <img src="./assets/metrics.svg" alt="Yilena 的 GitHub 公开活动与社区统计，由 Metrics 定期生成" width="520" />
</p>'''


class CardParser(HTMLParser):
    """Only permit an empty optional region or this script's active card."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.events: list[tuple[str, str, dict[str, str | None]]] = []

    def handle_starttag(self, tag, attrs):
        if len(attrs) != len(dict(attrs)):
            raise ValueError("Duplicate attributes in Metrics marker region")
        self.events.append(("start", tag, dict(attrs)))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag != "img":
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "img":
            raise ValueError("Unexpected closing img tag in Metrics region")
        self.events.append(("end", tag, {}))

    def handle_data(self, data):
        if data.strip():
            raise ValueError("Unexpected text in Metrics marker region")

    def handle_comment(self, data):
        raise ValueError("Unexpected comment in Metrics marker region")

    def handle_decl(self, decl):
        raise ValueError("Unexpected declaration in Metrics marker region")

    def handle_pi(self, data):
        raise ValueError("Unexpected processing instruction in Metrics region")


def validate_existing_region(region: str) -> None:
    # The primary statistics remain outside this optional supplement region.
    # An empty region is the initial state and never displays a missing image.
    if not region.strip():
        return
    parser = CardParser()
    parser.feed(region)
    parser.close()
    if len(parser.events) != 3:
        raise ValueError("Expected exactly one centered statistics image")
    first, image, last = parser.events
    if first != ("start", "p", {"align": "center"}) or last != ("end", "p", {}):
        raise ValueError("Unexpected Metrics region wrapper")
    event, tag, attrs = image
    if event != "start" or tag != "img" or set(attrs) != {"src", "alt", "width"}:
        raise ValueError("Unexpected statistics image structure")
    if attrs["width"] != "520" or not attrs["alt"]:
        raise ValueError("Unexpected statistics image attributes")
    src = attrs["src"]
    if src != "./assets/metrics.svg":
        raise ValueError("Refusing to replace other statistics in the optional Metrics region")


def validate_svg(content: bytes) -> None:
    if len(content.strip()) < 256 or len(content) > 10_000_000:
        raise ValueError("Metrics SVG is empty, incomplete, or unexpectedly large")
    if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
        raise ValueError("Unexpected XML declaration in Metrics SVG")
    root = ET.fromstring(content)
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise ValueError("The generated document is not a namespaced SVG")
    readable = " ".join(root.itertext())
    if "xie480" not in readable.lower():
        raise ValueError("Metrics SVG does not identify the intended GitHub user")
    if not any(element.tag.endswith("}foreignObject") or element.tag.endswith("}text") for element in root.iter()):
        raise ValueError("Metrics SVG has no rendered statistics content")
    for element in root.iter():
        if "error" in element.attrib.get("class", "").lower().split():
            raise ValueError("Metrics SVG contains a rendered error")
        if element.tag.endswith("}script"):
            raise ValueError("Unexpected script in Metrics SVG")


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".metrics-", delete=False) as output:
            temporary = Path(output.name)
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def activate(readme: Path, rendered: Path, target: Path) -> None:
    if readme.is_symlink() or target.is_symlink():
        raise ValueError("Refusing to replace a symlink")
    original = readme.read_bytes()
    text = original.decode("utf-8")
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError("README must contain exactly one Metrics marker pair")
    begin = text.index(START) + len(START)
    finish = text.index(END)
    if finish < begin:
        raise ValueError("Metrics markers are out of order")
    validate_existing_region(text[begin:finish])
    content = rendered.read_bytes()
    validate_svg(content)
    newline = "\r\n" if b"\r\n" in original else "\n"
    replacement = newline + ACTIVE.replace("\n", newline) + newline
    updated = (text[:begin] + replacement + text[finish:]).encode("utf-8")
    # Validate everything before either write; Git publishes both files together.
    atomic_write(target, content)
    if updated != original:
        atomic_write(readme, updated)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readme", type=Path, required=True)
    parser.add_argument("--rendered", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    args = parser.parse_args()
    try:
        activate(args.readme, args.rendered, args.target)
    except (OSError, UnicodeError, ValueError, ET.ParseError) as error:
        raise SystemExit(f"Metrics activation stopped: {error}") from error
    print("Validated Metrics SVG and README marker region.")


if __name__ == "__main__":
    main()
