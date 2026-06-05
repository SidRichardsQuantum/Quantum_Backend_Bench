"""Documentation link integrity tests."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlparse

import pytest

ROOT = Path(__file__).resolve().parents[1]

DOCS = [
    ROOT / "README.md",
    ROOT / "USAGE.md",
    ROOT / "docs" / "RESULTS.md",
    ROOT / "docs" / "SDK_AUDITS.md",
    ROOT / "docs" / "THEORY.md",
    ROOT / "docs" / "METHODOLOGY.md",
    ROOT / "docs" / "PROBLEM.md",
    ROOT / "docs" / "SCHEMA.md",
    ROOT / "docs" / "COMPATIBILITY.md",
    ROOT / "docs" / "LIMITATIONS.md",
    ROOT / "docs" / "CIRCUIT_TRANSLATION.md",
    ROOT / "CHANGELOG.md",
    ROOT / "examples" / "README.md",
    ROOT / "examples" / "translation" / "README.md",
    ROOT / "notebooks" / "README.md",
]

LOCAL_SCHEMES = {"", None}
SKIPPED_SCHEMES = {"http", "https", "mailto"}


def test_markdown_local_links_resolve() -> None:
    for document in DOCS:
        text = document.read_text(encoding="utf-8")
        anchors_by_file = {document.resolve(): _anchors(text)}
        for target in _markdown_targets(text):
            parsed = urlparse(target)
            if parsed.scheme in SKIPPED_SCHEMES:
                continue
            if target.startswith("#"):
                assert _slug(target[1:]) in anchors_by_file[document.resolve()]
                continue
            if parsed.scheme not in LOCAL_SCHEMES:
                continue

            linked = (document.parent / unquote(parsed.path)).resolve()
            assert linked.exists(), f"{document.relative_to(ROOT)} links to missing {target}"

            if parsed.fragment and linked.suffix.lower() == ".md":
                linked_text = linked.read_text(encoding="utf-8")
                anchors = anchors_by_file.setdefault(linked, _anchors(linked_text))
                assert (
                    _slug(parsed.fragment) in anchors
                ), f"{document.relative_to(ROOT)} links to missing anchor {target}"


@pytest.mark.docs
def test_generated_site_local_links_resolve() -> None:
    pytest.importorskip("markdown")

    from docs.pages import build_site

    build_site.main()
    site = ROOT / "_site"
    for page in site.glob("*.html"):
        text = page.read_text(encoding="utf-8")
        for href in re.findall(r'href="([^"]+)"', text):
            parsed = urlparse(href)
            if parsed.scheme in SKIPPED_SCHEMES or href.startswith("#"):
                continue
            if parsed.scheme not in LOCAL_SCHEMES:
                continue
            linked = (page.parent / unquote(parsed.path)).resolve()
            assert linked.exists(), f"{page.relative_to(ROOT)} links to missing {href}"


def _markdown_targets(text: str) -> list[str]:
    inline = re.findall(r'!?\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)', text)
    references = re.findall(r"^\[[^\]]+\]:\s+(\S+)", text, flags=re.MULTILINE)
    return [target.strip("<>") for target in [*inline, *references]]


def _anchors(text: str) -> set[str]:
    return {
        _slug(match.group(2)) for match in re.finditer(r"^(#{1,6})\s+(.+)$", text, re.MULTILINE)
    }


def _slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"[^\w\- ]+", "", value)
    return re.sub(r"[-\s]+", "-", value).strip("-")


def test_generated_site_includes_circuit_translation_page() -> None:
    pytest.importorskip("markdown")

    from docs.pages import build_site

    build_site.main()
    page = ROOT / "_site" / "translation.html"
    assert page.exists()
    text = page.read_text(encoding="utf-8")
    assert "Circuit Translation" in text
    assert "translate-check" in text


def test_generated_site_includes_sdk_audits_page() -> None:
    pytest.importorskip("markdown")

    from docs.pages import build_site

    build_site.main()
    page = ROOT / "_site" / "sdk-audits.html"
    assert page.exists()
    text = page.read_text(encoding="utf-8")
    assert "SDK Audits" in text
    assert "roundtrip-audit" in text
