"""Safe SVG sanitization for analysis copies (CorelDRAW DOCTYPE exports).

Original uploaded SVG content is never modified in storage; sanitization produces a
separate analysis copy only. Parser security is unchanged — no DTD fetch, no entity expansion.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from typing import Any

WARN_SVG_SANITIZED_DOCTYPE_REMOVED = "svg_sanitized_doctype_removed"
SANITIZATION_REASON_DOCTYPE_REMOVED = "svg_doctype_removed"

ERROR_SVG_UNSAFE_ENTITY_DECLARATION = "svg_unsafe_entity_declaration"
ERROR_SVG_UNSAFE_DTD_DECLARATION = "svg_unsafe_dtd_declaration"

OPERATOR_MESSAGE_SVG_UNSUPPORTED_XML = (
    "SVG-ul conține declarații XML nesigure. Exportă SVG fără entități/DTD sau contactează administratorul."
)

_DOCTYPE_RE = re.compile(r"<!DOCTYPE[^>]*>", re.IGNORECASE)
_ENTITY_DECL_RE = re.compile(r"<!ENTITY\b", re.IGNORECASE)
_INTERNAL_DTD_SUBSET_RE = re.compile(r"<!DOCTYPE[^>]*\[", re.IGNORECASE | re.DOTALL)
_REMAINING_DTD_DECL_RE = re.compile(
    r"<!(?:DOCTYPE|ENTITY|ATTLIST|ELEMENT|NOTATION)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SvgSanitizationMetadata:
    original_file_has_doctype: bool
    analysis_sanitized: bool
    sanitization_reason: str | None = None
    source_file_name: str | None = None
    source_content_hash: str | None = None
    analysis_content_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _content_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def has_unsafe_svg_declarations(svg_text: str) -> bool:
    """True when content contains DTD/ENTITY declarations blocked by the safe parser."""
    lowered = svg_text.lower()
    return "<!doctype" in lowered or "<!entity" in lowered


def has_entity_declaration(svg_text: str) -> bool:
    return bool(_ENTITY_DECL_RE.search(svg_text))


def has_internal_dtd_subset(svg_text: str) -> bool:
    return bool(_INTERNAL_DTD_SUBSET_RE.search(svg_text))


@dataclass(frozen=True)
class SvgSafeParsePreparation:
    ok: bool
    svg_text: str | None = None
    error_code: str | None = None
    error_detail: str | None = None
    operator_message: str | None = None
    sanitization: SvgSanitizationMetadata | None = None
    warnings: list[str] = field(default_factory=list)


def sanitize_svg_for_safe_geometry_parse(
    svg_text: str,
    *,
    source_file_name: str | None = None,
) -> SvgSafeParsePreparation:
    """Sanitize CorelDRAW-style standard SVG DOCTYPE before safe geometry parsing."""
    return prepare_svg_text_for_safe_geometry_parsing(
        svg_text,
        source_file_name=source_file_name,
    )


def prepare_svg_text_for_safe_geometry_parsing(
    svg_text: str,
    *,
    source_file_name: str | None = None,
) -> SvgSafeParsePreparation:
    """Sanitize standard SVG DOCTYPE only; fail closed on ENTITY/internal DTD subsets."""
    if not isinstance(svg_text, str) or not svg_text.strip():
        return SvgSafeParsePreparation(
            ok=False,
            error_code="empty_input",
            error_detail="SVG content is empty",
            operator_message=OPERATOR_MESSAGE_SVG_UNSUPPORTED_XML,
        )

    if has_entity_declaration(svg_text):
        return SvgSafeParsePreparation(
            ok=False,
            error_code=ERROR_SVG_UNSAFE_ENTITY_DECLARATION,
            error_detail="ENTITY declarations are not allowed",
            operator_message=OPERATOR_MESSAGE_SVG_UNSUPPORTED_XML,
        )

    if has_internal_dtd_subset(svg_text):
        return SvgSafeParsePreparation(
            ok=False,
            error_code=ERROR_SVG_UNSAFE_DTD_DECLARATION,
            error_detail="Internal DTD subsets are not allowed",
            operator_message=OPERATOR_MESSAGE_SVG_UNSUPPORTED_XML,
        )

    if not has_unsafe_svg_declarations(svg_text):
        return SvgSafeParsePreparation(ok=True, svg_text=svg_text)

    sanitized, meta = sanitize_svg_for_analysis(
        svg_text,
        source_file_name=source_file_name,
    )
    if sanitized is None or meta is None:
        return SvgSafeParsePreparation(
            ok=False,
            error_code=ERROR_SVG_UNSAFE_DTD_DECLARATION,
            error_detail="SVG DTD declarations could not be sanitized safely",
            operator_message=OPERATOR_MESSAGE_SVG_UNSUPPORTED_XML,
        )

    return SvgSafeParsePreparation(
        ok=True,
        svg_text=sanitized,
        sanitization=meta,
        warnings=[WARN_SVG_SANITIZED_DOCTYPE_REMOVED],
    )


def sanitize_svg_for_analysis(
    svg_text: str,
    *,
    source_file_name: str | None = None,
) -> tuple[str | None, SvgSanitizationMetadata | None]:
    """Build a sanitized analysis copy by stripping DTD/ENTITY declarations only.

    Returns (sanitized_text, metadata). sanitized_text is None when sanitization
    cannot produce safe analysis content.
    """
    if not isinstance(svg_text, str) or not svg_text.strip():
        return None, None

    if has_entity_declaration(svg_text) or has_internal_dtd_subset(svg_text):
        return None, None

    original_has_doctype = "<!doctype" in svg_text.lower()
    if not has_unsafe_svg_declarations(svg_text):
        return None, None

    sanitized = _DOCTYPE_RE.sub("", svg_text)

    if _REMAINING_DTD_DECL_RE.search(sanitized):
        return None, None

    if has_unsafe_svg_declarations(sanitized):
        return None, None

    if sanitized == svg_text:
        return None, None

    meta = SvgSanitizationMetadata(
        original_file_has_doctype=original_has_doctype,
        analysis_sanitized=True,
        sanitization_reason=SANITIZATION_REASON_DOCTYPE_REMOVED,
        source_file_name=(source_file_name.strip() if source_file_name else None),
        source_content_hash=_content_sha256(svg_text),
        analysis_content_hash=_content_sha256(sanitized),
    )
    return sanitized, meta
