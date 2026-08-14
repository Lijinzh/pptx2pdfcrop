from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

DOCS = Path(__file__).parents[1] / "docs"


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.references: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"] or "")
        for name in ("href", "src"):
            if values.get(name):
                self.references.append(values[name] or "")


SITE_PAGES = (
    DOCS / "index.html",
    DOCS / "en" / "index.html",
    DOCS / "guide" / "index.html",
    DOCS / "en" / "guide" / "index.html",
)


def test_site_pages_have_valid_local_references_and_unique_ids() -> None:
    for page in SITE_PAGES:
        parser = SiteParser()
        parser.feed(page.read_text(encoding="utf-8"))

        assert len(parser.ids) == len(set(parser.ids))
        for reference in parser.references:
            parts = urlsplit(reference)
            if parts.scheme or parts.netloc or reference.startswith(("#", "mailto:")):
                continue
            target = (page.parent / parts.path).resolve()
            if reference.endswith("/") or not target.suffix:
                target /= "index.html"
            assert target.exists(), f"{page}: missing local reference {reference}"


def test_homepages_lead_with_platform_and_codex_installation() -> None:
    chinese = (DOCS / "index.html").read_text(encoding="utf-8")
    english = (DOCS / "en" / "index.html").read_text(encoding="utf-8")

    assert "目前仅支持 Windows 10 / 11" in chinese
    assert "复制一句话，交给 Codex" in chinese
    assert 'data-copy-target="codex-command"' in chinese
    assert "Currently supports Windows 10 / 11 only" in english
    assert "Copy one sentence. Give it to Codex." in english
    assert 'data-copy-target="codex-command"' in english


def test_documentation_covers_architecture_and_contributing() -> None:
    for page in (DOCS / "guide" / "index.html", DOCS / "en" / "guide" / "index.html"):
        text = page.read_text(encoding="utf-8")
        assert 'id="architecture"' in text
        assert 'id="contributing"' in text
        assert "pipeline.py" in text
        assert "CONTRIBUTING.md" in text


def test_generated_hero_asset_exists() -> None:
    hero = DOCS / "assets" / "hero-export.png"
    webp = DOCS / "assets" / "hero-export.webp"
    assert hero.is_file()
    assert hero.stat().st_size > 100_000
    assert webp.is_file()
    assert webp.stat().st_size > 50_000
    assert webp.stat().st_size < hero.stat().st_size
