"""Map active workspace / ProductDefinition-shaped config → ProductProcessResolveInput.

Does not invent workshop process lists. Does not change Intake schema.
Uses stable template identity gates only (no display-name matching).
"""

from __future__ import annotations

import logging
from typing import Any

from data.product_process.volumetric_letters_v1 import CONTRACT_VERSION, PRODUCT_TEMPLATE_CODE
from schemas.product_process_contract import ProductProcessResolveInput
from services.template_architecture_scope import (
    VOLUMETRIC_V2_TEMPLATE_CODE,
    normalize_template_code,
    resolve_template_identity,
)

logger = logging.getLogger(__name__)

PROCESS_GRAPH_SOURCE_MODULAR = "modular_resolver"
PROCESS_GRAPH_SOURCE_LEGACY = "dossier_legacy"


def template_has_modular_process_contract(template_code: str | None) -> bool:
    """Stable identity gate — template_code / alias resolution only (case-insensitive)."""
    if not template_code:
        return False
    identity = resolve_template_identity(template_code)
    # resolve_template_identity uppercases; VOLUMETRIC_V2_TEMPLATE_CODE uses `_v2` casing.
    return normalize_template_code(identity.canonical_template_code) == normalize_template_code(
        VOLUMETRIC_V2_TEMPLATE_CODE
    )


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _map_cant_finish(return_finish_type: Any) -> str:
    raw = str(return_finish_type or "").strip().lower()
    if raw in {"oracal_wrapped", "oracal", "vinyl", "wrapped", "colantat", "cant_vinyl"}:
        return "vinyl"
    if raw in {"ral", "ral_paint", "painted_ral", "vopsit_ral", "paint_ral"}:
        return "ral"
    return "standard"


def _map_support_type(finish: dict[str, Any]) -> str:
    explicit = str(finish.get("support_type") or "").strip().lower()
    if explicit in {"metal_bars", "metal", "bars", "bare_metalice"}:
        return "metal_bars"
    if explicit in {"alucobond_cased", "alucobond", "acm_cased", "alucobond_cased_panel"}:
        return "alucobond_cased"
    if explicit in {"none", "no_support", "fara_suport"}:
        return "none"

    mounting = str(finish.get("mounting_system") or "").strip().lower()
    if mounting in {"steel_bars", "aluminum_bars", "aluminium_bars", "metal_bars", "bars"}:
        return "metal_bars"
    if "alucobond" in mounting or mounting in {"acm_cased", "cased_panel"}:
        return "alucobond_cased"
    if mounting in {"none", "no_support", "direct_wall", "ridicare", "pickup"}:
        return "none"
    # Canonical default when mounting unspecified: no support fabrication branch
    return "none"


def _map_screw_finish(raw: Any) -> tuple[str, bool]:
    """Returns (finish, used_default)."""
    if raw is None or str(raw).strip() == "":
        return "NATURAL", True
    text = str(raw).strip().upper()
    if text in {"NATURAL", "NATUR", "NONE"}:
        return "NATURAL", False
    if text in {"PAINTED_TO_MATCH_CANT", "PAINTED", "VOPSITE", "MATCH_CANT"}:
        return "PAINTED_TO_MATCH_CANT", False
    return "NATURAL", True


def _map_service_corner(raw: Any) -> str | None:
    if raw is None or str(raw).strip() == "":
        return None
    text = str(raw).strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "TOP_LEFT": "TOP_LEFT",
        "TOP_RIGHT": "TOP_RIGHT",
        "BOTTOM_LEFT": "BOTTOM_LEFT",
        "BOTTOM_RIGHT": "BOTTOM_RIGHT",
        "MANUAL_CONFIRMED": "MANUAL_CONFIRMED",
        "STANGA_SUS": "TOP_LEFT",
        "DREAPTA_SUS": "TOP_RIGHT",
        "STANGA_JOS": "BOTTOM_LEFT",
        "DREAPTA_JOS": "BOTTOM_RIGHT",
        "TL": "TOP_LEFT",
        "TR": "TOP_RIGHT",
        "BL": "BOTTOM_LEFT",
        "BR": "BOTTOM_RIGHT",
    }
    return aliases.get(text)


def _map_cable_length(raw: Any) -> float | None:
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _map_active_components(
    *,
    finish: dict[str, Any],
    offer_scope: dict[str, Any],
    support_type: str,
    illuminated: bool,
    template_selected: bool,
) -> list[str]:
    sold = offer_scope.get("sold_modules") or offer_scope.get("active_modules") or []
    if isinstance(sold, list) and sold:
        out: list[str] = []
        for item in sold:
            code = str(item).strip().upper()
            if code in {"FACE", "CANT", "RETURN-CANT", "RETURN_CANT"}:
                out.append("FACE" if code == "FACE" else "CANT")
            elif code in {"BACK", "FOREX"}:
                out.append("BACK")
            elif code in {"LIGHTING", "LED", "ELECTRICAL"}:
                out.append("LIGHTING")
            elif code in {"MOUNTING", "SUPPORT"}:
                if support_type == "metal_bars":
                    out.append("METAL_SUPPORT")
                elif support_type == "alucobond_cased":
                    out.append("ALUCOBOND_CASED_PANEL")
        # Dedupe preserve order
        seen: set[str] = set()
        ordered: list[str] = []
        for c in out:
            if c not in seen:
                seen.add(c)
                ordered.append(c)
        if ordered:
            if template_selected and "INSTALLATION_TEMPLATE" not in ordered:
                ordered.append("INSTALLATION_TEMPLATE")
            return ordered

    # Default full letter product composition (documented canonical default)
    comps = ["FACE", "CANT", "BACK"]
    if illuminated:
        comps.append("LIGHTING")
    if support_type == "metal_bars":
        comps.append("METAL_SUPPORT")
    elif support_type == "alucobond_cased":
        comps.append("ALUCOBOND_CASED_PANEL")
    if template_selected:
        comps.append("INSTALLATION_TEMPLATE")
    _ = finish
    return comps


def build_resolve_input_from_active_config(
    *,
    template_code: str,
    workspace_payload: dict[str, Any] | None = None,
    geometry_inputs: dict[str, Any] | None = None,
) -> tuple[ProductProcessResolveInput, list[str], list[str]]:
    """
    Returns (input, warnings, blockers) for mapping only (resolver may add more).

    Field map (live → resolver):
    | Field | Live source | Default | Missing |
    | product_template_code | template identity | TPL-VOLUMETRIC-LETTERS_v2 | blocker if non-pilot |
    | cant_finish | finish_setup.return_finish_type | standard | default |
    | support_type | finish_setup.support_type / mounting_system | none | default |
    | illuminated | finish_setup.lighting_system_type | True if missing/non-none | default True |
    | screw_finish | finish_setup.screw_finish | NATURAL | warning |
    | service_corner | finish_setup.power_supply_service_corner | None | blocker if alucobond |
    | mains_cable_length_m | finish_setup.mains_cable_length_m | None | no INSTALL_MAINS |
    | template_selected | finish_setup.mounting_template_enabled | False | inactive isolation |
    | geometry | quote_geometry / geometry_inputs | {} | warning if empty |
    """
    warnings: list[str] = []
    blockers: list[str] = []
    payload = workspace_payload or {}
    finish = _as_dict(payload.get("finish_setup"))
    quote_geometry = _as_dict(payload.get("quote_geometry"))
    offer_scope = _as_dict(payload.get("offer_scope") or payload.get("offer_scope_confirmed"))
    geom = dict(geometry_inputs or {})
    if not geom:
        geom = {
            "overall_width": quote_geometry.get("width_mm"),
            "overall_height": quote_geometry.get("height_mm"),
            "element_count": quote_geometry.get("letter_count"),
            "total_face_area": quote_geometry.get("letter_face_area_m2"),
            "total_perimeter": quote_geometry.get("letter_perimeter_m"),
            "template_segment_count": quote_geometry.get("template_segment_count")
            or finish.get("template_segment_count"),
        }

    identity = resolve_template_identity(template_code)
    # Prefer stable pilot code casing for resolver contract checks.
    if normalize_template_code(identity.canonical_template_code) == normalize_template_code(
        VOLUMETRIC_V2_TEMPLATE_CODE
    ):
        canonical = PRODUCT_TEMPLATE_CODE
    else:
        canonical = identity.canonical_template_code or PRODUCT_TEMPLATE_CODE

    cant_finish = _map_cant_finish(finish.get("return_finish_type"))
    support_type = _map_support_type(finish)
    lighting_raw = finish.get("lighting_system_type")
    if lighting_raw is None and not finish:
        illuminated = True
        warnings.append("default_illuminated_true_template_only")
    else:
        illuminated = str(lighting_raw or "led_modules").strip().lower() not in {
            "none",
            "off",
            "false",
            "0",
        }

    screw_finish, screw_defaulted = _map_screw_finish(finish.get("screw_finish"))
    if screw_defaulted:
        warnings.append("default_screw_finish_NATURAL")

    corner = _map_service_corner(
        finish.get("power_supply_service_corner")
        or finish.get("transformer_service_corner")
        or finish.get("service_corner")
    )
    cable = _map_cable_length(
        finish.get("mains_cable_length_m")
        or finish.get("mains_cable_length")
        or finish.get("cable_length_m")
    )
    if finish.get("mains_cable_length_m") not in (None, "") and cable is None:
        blockers.append("invalid_mains_cable_length_mapping")

    template_selected = bool(finish.get("mounting_template_enabled") is True)

    led_layout_confirmed = True
    if illuminated and finish.get("led_layout_confirmed") is False:
        led_layout_confirmed = False

    geometry_confirmed = True
    if quote_geometry.get("confirmed") is False:
        geometry_confirmed = False
        warnings.append("geometry_not_operator_confirmed")

    if not any(geom.get(k) for k in ("overall_width", "overall_height", "total_perimeter", "element_count")):
        if workspace_payload:
            warnings.append("geometry_fields_empty")

    active_components = _map_active_components(
        finish=finish,
        offer_scope=offer_scope,
        support_type=support_type,
        illuminated=illuminated,
        template_selected=template_selected,
    )

    inp = ProductProcessResolveInput(
        product_template_code=canonical,
        contract_version=CONTRACT_VERSION,
        active_components=active_components,
        cant_finish=cant_finish,  # type: ignore[arg-type]
        support_type=support_type,  # type: ignore[arg-type]
        screw_finish=screw_finish,  # type: ignore[arg-type]
        power_supply_service_corner=corner,  # type: ignore[arg-type]
        mains_cable_length_m=cable,
        template_selected=template_selected,
        illuminated=illuminated,
        geometry_confirmed=geometry_confirmed,
        led_layout_confirmed=led_layout_confirmed,
        geometry=geom,
    )
    logger.info(
        "process_resolve_input_mapped template=%s support=%s cant=%s cable=%s corner=%s",
        canonical,
        support_type,
        cant_finish,
        cable,
        corner,
    )
    return inp, warnings, blockers
