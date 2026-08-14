from __future__ import annotations

from collections.abc import Iterable

from .errors import SlideSelectionError


def parse_slide_spec(spec: str) -> list[int] | None:
    """Parse a 1-based slide expression such as ``1,3-5``.

    ``all`` returns ``None`` and is resolved once the presentation slide count is known.
    Duplicate slide numbers are removed and the result is returned in presentation order.
    """

    normalized = spec.strip().lower()
    if normalized == "all":
        return None
    if not normalized:
        raise SlideSelectionError("Slide selection cannot be empty.")

    result: list[int] = []
    seen: set[int] = set()
    for token in normalized.split(","):
        token = token.strip()
        if not token:
            raise SlideSelectionError(f"Invalid slide selection: {spec!r}")

        if "-" in token:
            parts = token.split("-")
            if len(parts) != 2 or not all(part.strip().isdigit() for part in parts):
                raise SlideSelectionError(f"Invalid slide range: {token!r}")
            start, end = (int(part.strip()) for part in parts)
            if start < 1 or end < 1 or start > end:
                raise SlideSelectionError(f"Invalid slide range: {token!r}")
            values: Iterable[int] = range(start, end + 1)
        else:
            if not token.isdigit() or int(token) < 1:
                raise SlideSelectionError(f"Invalid slide number: {token!r}")
            values = (int(token),)

        for value in values:
            if value not in seen:
                seen.add(value)
                result.append(value)

    return sorted(result)


def resolve_slides(selection: list[int] | None, slide_count: int) -> list[int]:
    if slide_count < 1:
        raise SlideSelectionError("The presentation does not contain any slides.")
    if selection is None:
        return list(range(1, slide_count + 1))

    invalid = [number for number in selection if number > slide_count]
    if invalid:
        rendered = ", ".join(str(number) for number in invalid)
        raise SlideSelectionError(
            f"Requested slide(s) {rendered}, but the presentation has only {slide_count} slides."
        )
    return selection


def compact_slide_label(slides: list[int]) -> str:
    """Return a filesystem-friendly label while keeping the requested order visible."""

    if len(slides) == 1:
        return f"slide-{slides[0]}"
    return "slides-" + "_".join(str(number) for number in slides)
