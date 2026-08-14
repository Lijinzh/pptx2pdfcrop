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


def test_site_pages_have_valid_local_references_and_unique_ids() -> None:
    for page in (DOCS / "index.html", DOCS / "en" / "index.html"):
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
