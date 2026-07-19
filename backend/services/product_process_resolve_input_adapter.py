"""Map typed ProductDefinition / Intake config → ProductProcessResolveInput.

Authority precedence (typed wins):
1. ProductDefinition canonical_values (typed bindings)
2. Typed finish_setup fields (mains_cable_length_m, power_supply_service_corner, service_screw_finish)
3. Canonical mounting_solution → support_type
4. Legacy finish_setup fallbacks (mounting_system, return_finish_type, support_type string)

Does not invent workshop process lists. Does not change CPP.
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

CONFIG_SOURCE_TYPED_PD = "typed_product_definition"
CONFIG_SOURCE_TYPED_FINISH = "typed_finish_setup"
CONFIG_SOURCE_LEGACY_FALLBACK = "legacy_finish_setup_fallback"

ALLOWED_CABLE_LENGTHS = frozenset({2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 25.0})


def template_has_modular_process_contract(template_code: str | None) -> bool:
    """Stable identity gate — template_code / alias resolution only (case-insensitive)."""
    if not template_code:
        return False
    identity = resolve_template_identity(template_code)
    return normalize_template_code(identity.canonical_template_code) == normalize_template_code(
        VOLUMETRIC_V2_TEMPLATE_CODE
    )


def _segmented_owns_service_corner_authority(finish: dict[str, Any] | None) -> bool:
    """D3: confirmed multi-panel segmented assembly owns service/electrical — not legacy corner."""
    if not isinstance(finish, dict):
        return False
    segmented = finish.get("segmented_background")
    if not isinstance(segmented, dict):
        return False
    if str(segmented.get("status") or "").strip().upper() != "CONFIRMED":
        return False
    panels = segmented.get("panels")
    return isinstance(panels, list) and len(panels) >= 2


def _segmented_electrical_authority_complete(finish: dict[str, Any] | None) -> bool:
    """D3: segmented electrical CONFIRMED with no blockers (full electrical truth)."""
    if not _segmented_owns_service_corner_authority(finish):
        return False
    assert isinstance(finish, dict)
    segmented = finish.get("segmented_background")
    assert isinstance(segmented, dict)
    panels = segmented.get("panels")
    assert isinstance(panels, list)
    electrical = segmented.get("electrical_connection_management")
    if not isinstance(electrical, dict):
        return False
    if str(electrical.get("status") or "").strip().upper() != "CONFIRMED":
        return False
    from services.acm_segmented_electrical_service import electrical_confirmation_blockers

    panel_ids = {
        str(p.get("panel_id") or "")
        for p in panels
        if isinstance(p, dict) and p.get("panel_id")
    }
    blockers = electrical_confirmation_blockers(electrical, assembly_panel_ids=panel_ids)
    return len(blockers) == 0


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        try:
            dumped = value.model_dump(mode="json")
            return dumped if isinstance(dumped, dict) else {}
        except Exception:
            return {}
    return {}


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def _map_cant_finish(return_finish_type: Any) -> str:
    raw = str(return_finish_type or "").strip().lower()
    if raw in {"oracal_wrapped", "oracal", "vinyl", "wrapped", "colantat", "cant_vinyl", "oracal_651"}:
        return "vinyl"
    if raw in {"ral", "ral_paint", "painted_ral", "vopsit_ral", "paint_ral", "painted"}:
        return "ral"
    return "standard"


def _support_from_mounting_solution(solution: Any) -> str | None:
    sol = _as_dict(solution)
    if not sol:
        return None
    kind = str(sol.get("kind") or "").strip().lower()
    template = str(sol.get("template_code") or "").strip().upper()
    if any(tok in template for tok in ("ACM", "ALUCOBOND")) or kind in {
        "acm",
        "acm_panel",
        "cased_panel",
        "alucobond_cased",
    }:
        return "alucobond_cased"
    if any(tok in template for tok in ("PREMOUNT", "METAL-PREMOUNT", "METAL_PREMOUNT")) or kind in {
        "metal_bars",
        "premount",
        "bars",
    }:
        return "metal_bars"
    if kind in {"none", "direct", "direct_wall", "installation_template", "no_support"}:
        return "none"
    if "INSTALLATION_TEMPLATE" in template or "SABLON" in template:
        return "none"
    return None


def _map_support_type(
    *,
    finish: dict[str, Any],
    canonical: dict[str, Any],
) -> tuple[str, str]:
    """Returns (support_type, source_tag)."""
    # 1) Explicit process support from PD / typed finish
    explicit = _first_present(
        canonical.get("process_support_type"),
        canonical.get("support_type"),
        finish.get("process_support_type"),
        finish.get("support_type"),
    )
    if explicit is not None:
        raw = str(explicit).strip().lower()
        if raw in {"metal_bars", "metal", "bars", "bare_metalice"}:
            return "metal_bars", CONFIG_SOURCE_TYPED_PD if "support_type" in canonical or "process_support_type" in canonical else CONFIG_SOURCE_TYPED_FINISH
        if raw in {"alucobond_cased", "alucobond", "acm_cased", "alucobond_cased_panel"}:
            return "alucobond_cased", CONFIG_SOURCE_TYPED_PD if "support_type" in canonical else CONFIG_SOURCE_TYPED_FINISH
        if raw in {"none", "no_support", "fara_suport"}:
            return "none", CONFIG_SOURCE_TYPED_PD if "support_type" in canonical else CONFIG_SOURCE_TYPED_FINISH
        if raw in {"alucobond_flat", "flat", "acm_flat"}:
            return "INVALID_ALUCOBOND_FLAT", CONFIG_SOURCE_TYPED_FINISH

    # 2) Canonical mounting_solution
    solution = _first_present(canonical.get("mounting_solution"), finish.get("mounting_solution"))
    from_sol = _support_from_mounting_solution(solution)
    if from_sol:
        return from_sol, CONFIG_SOURCE_TYPED_PD if canonical.get("mounting_solution") is not None else CONFIG_SOURCE_TYPED_FINISH

    # 3) Legacy mounting_system
    mounting = str(
        _first_present(canonical.get("mounting_system"), finish.get("mounting_system")) or ""
    ).strip().lower()
    if mounting in {"steel_bars", "aluminum_bars", "aluminium_bars", "metal_bars", "bars"}:
        return "metal_bars", CONFIG_SOURCE_LEGACY_FALLBACK
    if mounting in {"acm_panel", "alucobond_cased"} or "alucobond" in mounting:
        return "alucobond_cased", CONFIG_SOURCE_LEGACY_FALLBACK
    if mounting in {"none", "no_support", "direct_wall", "ridicare", "pickup"}:
        return "none", CONFIG_SOURCE_LEGACY_FALLBACK

    return "none", CONFIG_SOURCE_LEGACY_FALLBACK


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
            if code == "FACE":
                out.append("FACE")
            elif code in {"CANT", "RETURN-CANT", "RETURN_CANT"}:
                out.append("CANT")
            elif code in {"BACK", "FOREX"}:
                out.append("BACK")
            elif code in {"LIGHTING", "LED", "ELECTRICAL"}:
                out.append("LIGHTING")
            elif code in {"MOUNTING", "SUPPORT"}:
                if support_type == "metal_bars":
                    out.append("METAL_SUPPORT")
                elif support_type == "alucobond_cased":
                    out.append("ALUCOBOND_CASED_PANEL")
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
    product_definition_canonical_values: dict[str, Any] | None = None,
) -> tuple[ProductProcessResolveInput, list[str], list[str], dict[str, Any]]:
    """
    Build ProductProcessResolveInput with typed precedence.

    Returns (input, warnings, blockers, config_meta).

    Field map:
    | Semantic | Typed PD / finish | Legacy fallback |
    | support_type | mounting_solution / support_type | mounting_system |
    | cant_finish | return_finish_type (PD/finish) | same (existing finish truth) |
    | mains_cable_length_m | typed field | none (no invent 5m) |
    | service_corner | power_supply_service_corner | none |
    | screw_finish | service_screw_finish | default NATURAL |
    | template | mounting_template_enabled | false |
    """
    warnings: list[str] = []
    blockers: list[str] = []
    payload = workspace_payload or {}
    finish = _as_dict(payload.get("finish_setup"))
    canonical = dict(product_definition_canonical_values or {})
    quote_geometry = _as_dict(payload.get("quote_geometry"))
    offer_scope = _as_dict(payload.get("offer_scope") or payload.get("offer_scope_confirmed"))
    geom = dict(geometry_inputs or {})
    if not geom:
        geom = {
            "overall_width": _first_present(canonical.get("width_mm"), quote_geometry.get("width_mm")),
            "overall_height": _first_present(canonical.get("height_mm"), quote_geometry.get("height_mm")),
            "element_count": _first_present(canonical.get("letter_count"), quote_geometry.get("letter_count")),
            "total_face_area": _first_present(
                canonical.get("letter_face_area_m2"), quote_geometry.get("letter_face_area_m2")
            ),
            "total_perimeter": _first_present(
                canonical.get("letter_perimeter_m"), quote_geometry.get("letter_perimeter_m")
            ),
            "template_segment_count": _first_present(
                canonical.get("template_segment_count"),
                quote_geometry.get("template_segment_count"),
                finish.get("template_segment_count"),
            ),
        }

    identity = resolve_template_identity(template_code)
    if normalize_template_code(identity.canonical_template_code) == normalize_template_code(
        VOLUMETRIC_V2_TEMPLATE_CODE
    ):
        product_code = PRODUCT_TEMPLATE_CODE
    else:
        product_code = identity.canonical_template_code or PRODUCT_TEMPLATE_CODE

    # --- cant finish (existing authority: return_finish_type) ---
    return_finish = _first_present(
        canonical.get("return_finish_type"),
        finish.get("return_finish_type"),
    )
    cant_finish = _map_cant_finish(return_finish)
    cant_source = (
        CONFIG_SOURCE_TYPED_PD
        if canonical.get("return_finish_type") is not None
        else CONFIG_SOURCE_TYPED_FINISH
        if finish.get("return_finish_type") is not None
        else CONFIG_SOURCE_LEGACY_FALLBACK
    )

    support_type, support_source = _map_support_type(finish=finish, canonical=canonical)
    if support_type == "INVALID_ALUCOBOND_FLAT":
        blockers.append("alucobond_flat_not_allowed")
        support_type = "none"

    lighting_raw = _first_present(
        canonical.get("lighting_system_type"),
        finish.get("lighting_system_type"),
    )
    if lighting_raw is None and not finish and not canonical:
        illuminated = True
        warnings.append("default_illuminated_true_template_only")
    else:
        illuminated = str(lighting_raw or "led_modules").strip().lower() not in {
            "none",
            "off",
            "false",
            "0",
        }

    screw_raw = _first_present(
        canonical.get("service_screw_finish"),
        finish.get("service_screw_finish"),
        # legacy ghost key (pre-typed)
        finish.get("screw_finish"),
    )
    screw_finish, screw_defaulted = _map_screw_finish(screw_raw)
    if screw_defaulted:
        warnings.append("default_screw_finish_NATURAL")
    screw_source = (
        CONFIG_SOURCE_TYPED_PD
        if canonical.get("service_screw_finish") is not None
        else CONFIG_SOURCE_TYPED_FINISH
        if finish.get("service_screw_finish") is not None
        else CONFIG_SOURCE_LEGACY_FALLBACK
    )

    corner_raw = _first_present(
        canonical.get("power_supply_service_corner"),
        finish.get("power_supply_service_corner"),
        finish.get("transformer_service_corner"),
        finish.get("service_corner"),
    )
    corner = _map_service_corner(corner_raw)
    corner_source = (
        CONFIG_SOURCE_TYPED_PD
        if canonical.get("power_supply_service_corner") is not None
        else CONFIG_SOURCE_TYPED_FINISH
        if finish.get("power_supply_service_corner") is not None
        else CONFIG_SOURCE_LEGACY_FALLBACK
        if corner_raw is not None
        else None
    )

    cable_raw = _first_present(
        canonical.get("mains_cable_length_m"),
        finish.get("mains_cable_length_m"),
        finish.get("mains_cable_length"),
        finish.get("cable_length_m"),
    )
    cable = _map_cable_length(cable_raw)
    if cable_raw not in (None, "") and cable is None:
        blockers.append("invalid_mains_cable_length_mapping")
    if cable is not None and cable not in ALLOWED_CABLE_LENGTHS:
        # Resolver also blocks; surface early for typed path observability
        blockers.append("invalid_mains_cable_length")
    cable_source = (
        CONFIG_SOURCE_TYPED_PD
        if canonical.get("mains_cable_length_m") is not None
        else CONFIG_SOURCE_TYPED_FINISH
        if finish.get("mains_cable_length_m") is not None
        else CONFIG_SOURCE_LEGACY_FALLBACK
        if cable_raw is not None
        else None
    )
    # Explicit: never invent 5.0 when missing
    if cable is None and cable_raw in (None, ""):
        pass

    from services.mounting_scope_service import is_mounting_preparation_active

    template_raw = _first_present(
        canonical.get("mounting_template_enabled"),
        finish.get("mounting_template_enabled"),
    )
    # D5: legacy mounting_template_enabled=true under scope none is retained but inactive.
    template_selected = bool(template_raw is True) and is_mounting_preparation_active(finish)

    # Typed vs legacy conflict: if PD and finish disagree on cable, typed PD wins (already via _first_present)
    if (
        canonical.get("mains_cable_length_m") is not None
        and finish.get("mains_cable_length_m") is not None
        and float(canonical["mains_cable_length_m"]) != float(finish["mains_cable_length_m"])
    ):
        warnings.append("typed_pd_wins_over_finish_setup_cable_conflict")

    if (
        canonical.get("service_screw_finish") is not None
        and finish.get("service_screw_finish") is not None
        and str(canonical["service_screw_finish"]).upper() != str(finish["service_screw_finish"]).upper()
    ):
        warnings.append("typed_pd_wins_over_finish_setup_screw_conflict")

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

    # Overall config_source: best (most typed) among critical fields
    sources = [s for s in (support_source, cant_source, screw_source, corner_source, cable_source) if s]
    if CONFIG_SOURCE_TYPED_PD in sources:
        config_source = CONFIG_SOURCE_TYPED_PD
    elif CONFIG_SOURCE_TYPED_FINISH in sources:
        config_source = CONFIG_SOURCE_TYPED_FINISH
    else:
        config_source = CONFIG_SOURCE_LEGACY_FALLBACK

    # Strip non-geometry keys from geom
    clean_geom = {k: v for k, v in geom.items() if not str(k).startswith("_")}

    # Skip legacy corner whenever segmented multi-panel is CONFIRMED (authority transferred).
    # Incomplete ECM is a separate electrical readiness concern — not PROCESS_RESOLVER_SERVICE_CORNER.
    segmented_electrical_complete = _segmented_owns_service_corner_authority(finish)

    inp = ProductProcessResolveInput(
        product_template_code=product_code,
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
        segmented_electrical_authority_complete=segmented_electrical_complete,
        geometry=clean_geom,
    )
    config_meta = {
        "config_source": config_source,
        "support_source": support_source,
        "cable_source": cable_source,
        "corner_source": corner_source,
        "screw_source": screw_source,
        "cant_source": cant_source,
    }

    logger.info(
        "process_resolve_input_mapped template=%s support=%s(%s) cant=%s cable=%s corner=%s config_source=%s",
        product_code,
        support_type,
        support_source,
        cant_finish,
        cable,
        corner,
        config_source,
    )
    return inp, warnings, blockers, config_meta
