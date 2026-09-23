"""Check the built site's local links, fragments, and publishing allowlist."""
from __future__ import annotations

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from build_docs_site import ASSETS, GENERATED_ASSETS, PAGES, ZH_PAGES


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = []
        self.ids = set()
        self.h1_count = 0
        self.language = None
        self.language_switch = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "html":
            self.language = attributes.get("lang")
        if tag == "a" and "language-switch" in attributes.get("class", "").split():
            self.language_switch = attributes.get("href")
        if "id" in attributes:
            self.ids.add(attributes["id"])
        if tag == "h1":
            self.h1_count += 1
        for attribute in ("href", "src"):
            if attribute in attributes:
                self.links.append(attributes[attribute])


def check(root):
    assert PAGES.keys() == ZH_PAGES.keys(), "English and Chinese pages must match"
    expected = {f"{name}.html" for name in PAGES} | {f"zh/{name}.html" for name in ZH_PAGES} | {"404.html", ".nojekyll", "assets/local_first.py"} | {f"assets/{name}" for name in ASSETS + GENERATED_ASSETS}
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    assert actual == expected, f"Publish inventory differs: {actual ^ expected}"
    documents = {path: Document(path.read_text(encoding="utf-8")) for path in root.rglob("*.html")}
    count = 0
    for path, document in documents.items():
        assert document.h1_count == 1, f"Expected one h1: {path}"
        if path.name != "404.html":
            chinese = path.parent.name == "zh"
            assert document.language == ("zh-CN" if chinese else "en"), f"Wrong language: {path}"
            counterpart = root / path.name if chinese else root / "zh" / path.name
            assert document.language_switch and (path.parent / document.language_switch).resolve() == counterpart, f"Language switch loses current page: {path}"
            assert document.ids == documents[counterpart].ids, f"Language versions must preserve section anchors: {path}"
        assert "\u2014" not in path.read_text(encoding="utf-8"), f"Em dash in {path}"
        for link in document.links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue
            if parsed.path == "/wrench-slm/" and path.name == "404.html":
                continue
            assert not parsed.path.startswith("/"), f"Project Pages needs relative links: {link}"
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            assert target.is_relative_to(root), f"Link escapes site: {link}"
            assert target.is_file(), f"Missing target from {path.name}: {link}"
            if parsed.fragment:
                assert target in documents and unquote(parsed.fragment) in documents[target].ids, f"Missing fragment: {link}"
            count += 1
    receipt = json.loads((root / "assets" / "demo-receipt.json").read_text(encoding="utf-8"))
    assert receipt["fixture_unchanged"] is True
    assert [case["result"]["status"] for case in receipt["cases"]] == ["accepted", "abstain", "abstain"]
    print(f"PASS: {len(documents)} HTML pages, {count} local links and fragments, exact {len(actual)}-file publish allowlist, demo receipt.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path(__file__).resolve().parents[1] / "docs" / "gh-pages")
    check(parser.parse_args().site.resolve())
