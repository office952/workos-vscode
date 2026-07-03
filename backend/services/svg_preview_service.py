"""Safe SVG preview text for operator UI (analysis copy only, no script execution)."""

from __future__ import annotations

import re

_SCRIPT_TAG_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
_FOREIGN_OBJECT_RE = re.compile(
    r"<foreignObject\b[^>]*>.*?</foreignObject>", re.IGNORECASE | re.DOTALL
)
_ON_EVENT_ATTR_RE = re.compile(r'\s+on[a-z]+\s*=\s*("[^"]*"|\'[^\']*\')', re.IGNORECASE)
_HREF_JS_RE = re.compile(r'(href|xlink:href)\s*=\s*"\s*javascript:[^"]*"', re.IGNORECASE)


def build_safe_svg_preview(svg_text: str) -> str | None:
    """Return SVG suitable for static preview rendering, or None if unsafe/empty."""
    if not isinstance(svg_text, str):
        return None
    text = svg_text.strip()
    if not text or "<svg" not in text.lower():
        return None

    cleaned = _SCRIPT_TAG_RE.sub("", text)
    cleaned = _FOREIGN_OBJECT_RE.sub("", cleaned)
    cleaned = _ON_EVENT_ATTR_RE.sub("", cleaned)
    cleaned = _HREF_JS_RE.sub("", cleaned)

    if "<script" in cleaned.lower() or "javascript:" in cleaned.lower():
        return None
    if _local_unsafe_dtd(cleaned):
        return None
    return cleaned.strip() or None


def _local_unsafe_dtd(text: str) -> bool:
    lowered = text.lower()
    return "<!doctype" in lowered or "<!entity" in lowered
