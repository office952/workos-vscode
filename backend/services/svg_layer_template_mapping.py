"""Map SVG graphical layer names to ProductSystem template_code (read-only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MappingStatus = Literal[
    "mapped",
    "unmapped",
    "ambiguous",
    "unsupported",
    "suggested",
]

# Canonical ProductSystem template codes known in WorkOS seeds / production flows.
DEFAULT_KNOWN_TEMPLATE_CODES: tuple[str, ...] = (
    "TPL-BANNER-STANDARD",
    "TPL-PLEXI-PLATE",
    "TPL-VINYL-STICKER",
    "TPL-LIGHTBOX-STANDARD",
    "TPL-VOLUMETRIC-LETTERS",
    "TPL-MESH-EXTERNALIZED",
    "TPL-ACP-LIGHT-ROUTED",
    "TPL-ACM-CASSETTED-PANEL",
    "TPL-CUT-ACM-LETTERS",
)

# Secondary aliases — never canonical identity; suggest only.
SVG_LAYER_TEMPLATE_ALIASES: dict[str, str] = {
    "litere volumetrice": "TPL-VOLUMETRIC-LETTERS",
    "litere volumetrice luminoase": "TPL-VOLUMETRIC-LETTERS",
    "litere luminoase": "TPL-VOLUMETRIC-LETTERS",
    "volumetric letters": "TPL-VOLUMETRIC-LETTERS",
    "volumetric illuminated letters": "TPL-VOLUMETRIC-LETTERS",
    "product 001": "TPL-VOLUMETRIC-LETTERS",
}

VOLUMETRIC_SECONDARY_DESCRIPTION = "Litere volumetrice luminoase / Product 001"

TEMPLATE_SECONDARY_DESCRIPTIONS: dict[str, str] = {
    "TPL-VOLUMETRIC-LETTERS": VOLUMETRIC_SECONDARY_DESCRIPTION,
    "TPL-ACP-LIGHT-ROUTED": "Panou ACP iluminat / casetat",
    "TPL-LIGHTBOX-STANDARD": "Casetă luminoasă",
    "TPL-ACM-CASSETTED-PANEL": (
        "Panou ACM/Dibond casetat — fundal / suport premontaj (nu spate literă Forex)"
    ),
    "TPL-CUT-ACM-LETTERS": "Litere/forme plate tăiate ACM — nu volumetrice",
}


@dataclass(frozen=True)
class SvgLayerTemplateMapping:
    svg_layer_name: str
    mapped_template_code: str | None
    mapping_status: MappingStatus
    suggested_template_code: str | None
    human_description: str
    detected_kind: str
    blockers: tuple[str, ...]


def _normalize_layer_name(name: str) -> str:
    return " ".join(name.strip().split()).lower()


def map_svg_layer_to_template(
    svg_layer_name: str,
    *,
    known_template_codes: tuple[str, ...] | list[str] | None = None,
    active_template_codes: tuple[str, ...] | list[str] | None = None,
) -> SvgLayerTemplateMapping:
    """Primary rule: exact template_code match. Aliases suggest only."""
    raw = (svg_layer_name or "").strip()
    codes = tuple(known_template_codes or DEFAULT_KNOWN_TEMPLATE_CODES)
    code_set = {c.strip().upper() for c in codes if c and str(c).strip()}
    active_set = (
        {c.strip().upper() for c in active_template_codes if c and str(c).strip()}
        if active_template_codes is not None
        else None
    )

    if not raw:
        return SvgLayerTemplateMapping(
            svg_layer_name=raw,
            mapped_template_code=None,
            mapping_status="unsupported",
            suggested_template_code=None,
            human_description="Layer fără nume",
            detected_kind="unknown",
            blockers=("svg_layer_unnamed",),
        )

    upper = raw.upper()
    if upper in code_set:
        blockers: tuple[str, ...] = ()
        description = TEMPLATE_SECONDARY_DESCRIPTIONS.get(
            upper, f"Layer SVG mapat la {upper}"
        )
        if active_set is not None and upper not in active_set:
            blockers = ("template_inactive", "template_not_active_for_quote")
            description = (
                f"{description} — template inactiv pentru ofertă "
                "(arhivat/experimental)"
            )
        return SvgLayerTemplateMapping(
            svg_layer_name=raw,
            mapped_template_code=upper,
            mapping_status="mapped",
            suggested_template_code=None,
            human_description=description,
            detected_kind=_detect_kind(upper),
            blockers=blockers,
        )

    norm = _normalize_layer_name(raw)
    alias_target = SVG_LAYER_TEMPLATE_ALIASES.get(norm)
    if alias_target and alias_target.upper() in code_set:
        return SvgLayerTemplateMapping(
            svg_layer_name=raw,
            mapped_template_code=None,
            mapping_status="ambiguous",
            suggested_template_code=alias_target.upper(),
            human_description=(
                f"Alias '{raw}' → sugerat {alias_target} (identitate canonică: template_code)"
            ),
            detected_kind=_detect_kind(alias_target.upper()),
            blockers=("ambiguous_layer_name",),
        )

    # Known-looking template prefix but not in registry
    if upper.startswith("TPL-"):
        return SvgLayerTemplateMapping(
            svg_layer_name=raw,
            mapped_template_code=None,
            mapping_status="unmapped",
            suggested_template_code=None,
            human_description=f"Template lipsă pentru layer '{raw}'",
            detected_kind="unknown",
            blockers=("template_missing_for_svg_layer",),
        )

    return SvgLayerTemplateMapping(
        svg_layer_name=raw,
        mapped_template_code=None,
        mapping_status="unmapped",
        suggested_template_code=None,
        human_description=f"Layer '{raw}' fără mapare template",
        detected_kind="unknown",
        blockers=("svg_layer_unmapped",),
    )


def _detect_kind(template_code: str) -> str:
    if template_code == "TPL-VOLUMETRIC-LETTERS":
        return "volumetric_letters"
    if template_code in {"TPL-ACP-LIGHT-ROUTED", "TPL-ACM-CASSETTED-PANEL"}:
        return "acm_casetted_panel"
    if template_code == "TPL-CUT-ACM-LETTERS":
        return "cut_acm_letters"
    if template_code == "TPL-LIGHTBOX-STANDARD":
        return "background_panel"
    return "unknown"
