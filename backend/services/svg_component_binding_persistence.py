"""Unified SVG → Product System component bindings for FinishSetup / ProductDefinition.

Single persistence authority for Intake component-aware assignment.
No DB migration — JSON document fields on finish_setup.
"""

from __future__ import annotations

from typing import Any

from data.product_system.svg_component_binding_contract import (
    ACM_BOXED_SUPPORT,
    FACE_COMPONENT,
    GEOMETRY_ROLE_LETTER_VECTOR_SET,
    GEOMETRY_ROLE_LOGO_VECTOR_SET,
    GEOMETRY_ROLE_SUPPORT_CONTOUR,
    LOGO_PRODUCT,
    STALE_BOND_CASETAT,
)

SVG_COMPONENT_BINDINGS_SCHEMA = "svg_component_bindings_v1"
BINDING_STATUS_CONFIRMED = "CONFIRMED"
BINDING_STATUS_RECONFIRM = "RECONFIRM_REQUIRED"
BINDING_STATUS_DRAFT = "DRAFT"


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def read_svg_component_bindings(finish: dict[str, Any] | None) -> list[dict[str, Any]]:
    finish = finish or {}
    raw = finish.get("svg_component_bindings")
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict) and item.get("component_template_code"):
            out.append(dict(item))
    return out


def validate_bindings_for_new_selection(bindings: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    support_count = 0
    codes: set[str] = set()
    for b in bindings:
        code = str(b.get("component_template_code") or "").strip()
        if code == STALE_BOND_CASETAT:
            blockers.append("TPL-BOND-CASETAT is legacy and cannot be used for new selection.")
        if code == ACM_BOXED_SUPPORT or str(b.get("geometry_role") or "") == GEOMETRY_ROLE_SUPPORT_CONTOUR:
            if str(b.get("status") or "") in {BINDING_STATUS_CONFIRMED, BINDING_STATUS_DRAFT}:
                support_count += 1
        if code in codes and code:
            # Allow overwrite of same component; duplicate distinct rows blocked below for ACP
            pass
        codes.add(code)
        role = str(b.get("geometry_role") or "")
        if role == GEOMETRY_ROLE_SUPPORT_CONTOUR and code == FACE_COMPONENT:
            blockers.append("SUPPORT_CONTOUR cannot bind to letters face component.")
        if role == GEOMETRY_ROLE_LETTER_VECTOR_SET and code == ACM_BOXED_SUPPORT:
            blockers.append("LETTER_VECTOR_SET cannot bind to Alucobond support component.")
    if support_count > 1:
        blockers.append("V1 allows at most one SUPPORT_CONTOUR / ACP binding.")
    return blockers


def sync_support_selection_from_bindings(finish: dict[str, Any]) -> dict[str, Any]:
    """Ensure svg_support_selection mirrors confirmed SUPPORT_CONTOUR binding (legacy adapters)."""
    bindings = read_svg_component_bindings(finish)
    support = next(
        (
            b
            for b in bindings
            if str(b.get("component_template_code") or "") == ACM_BOXED_SUPPORT
            or str(b.get("geometry_role") or "") == GEOMETRY_ROLE_SUPPORT_CONTOUR
        ),
        None,
    )
    if not support:
        return finish
    status = str(support.get("status") or "").strip()
    geom = _as_dict(support.get("selected_geometry"))
    config = _as_dict(support.get("configuration"))
    if status == BINDING_STATUS_RECONFIRM:
        finish["svg_support_selection"] = {
            "schema": "svg_support_selection_v1",
            "status": "reconfirm_required",
            "contour_id": (geom.get("element_ids") or [None])[0],
            "geometry_hash": (geom.get("geometry_hashes") or [None])[0],
            "svg_source_hash": geom.get("source_svg_hash"),
        }
        return finish
    if status != BINDING_STATUS_CONFIRMED:
        return finish
    existing = _as_dict(finish.get("svg_support_selection"))
    element_ids = [str(x) for x in _as_list(geom.get("element_ids")) if x]
    hashes = [str(x) for x in _as_list(geom.get("geometry_hashes")) if x]
    contour_id = element_ids[0] if element_ids else support.get("contour_id") or existing.get("contour_id")
    finish["svg_support_selection"] = {
        "schema": "svg_support_selection_v1",
        "status": "confirmed",
        "role": "ALUCOBOND_CASED_PANEL",
        "contour_id": contour_id,
        "svg_support_element_id": support.get("svg_support_element_id")
        or existing.get("svg_support_element_id")
        or contour_id,
        "geometry_hash": hashes[0]
        if hashes
        else support.get("geometry_hash") or existing.get("geometry_hash"),
        "svg_source_hash": geom.get("source_svg_hash")
        or support.get("svg_source_hash")
        or existing.get("svg_source_hash"),
        "panel_geometry": support.get("panel_geometry")
        or config.get("panel_geometry")
        or existing.get("panel_geometry"),
        "casing_profile": {
            "fold_count": config.get("fold_count"),
            "l1_mm": config.get("l1_mm"),
            "l2_mm": config.get("l2_mm"),
            "finished_depth_mm": config.get("finished_depth_mm") or config.get("l1_mm"),
        }
        if config.get("fold_count") is not None
        else support.get("casing_profile") or existing.get("casing_profile"),
        "service_corner": config.get("service_corner")
        or support.get("service_corner")
        or existing.get("service_corner"),
        "internal_frame_enabled": bool(
            config.get(
                "internal_frame_enabled",
                support.get("internal_frame_enabled", existing.get("internal_frame_enabled")),
            )
        ),
        "candidate_explanation": support.get("candidate_explanation")
        or existing.get("candidate_explanation")
        or [],
        "unit_ambiguity": bool(support.get("unit_ambiguity", existing.get("unit_ambiguity"))),
        "confirmed_at": support.get("confirmed_at") or existing.get("confirmed_at"),
        "component_template_code": ACM_BOXED_SUPPORT,
        "geometry_role": GEOMETRY_ROLE_SUPPORT_CONTOUR,
    }
    return finish


def hydrate_bindings_from_legacy_support(finish: dict[str, Any]) -> list[dict[str, Any]]:
    """If only svg_support_selection exists, project a SUPPORT_CONTOUR binding for read compatibility."""
    existing = read_svg_component_bindings(finish)
    if existing:
        return existing
    selection = _as_dict(finish.get("svg_support_selection"))
    if selection.get("schema") != "svg_support_selection_v1":
        return []
    status_raw = str(selection.get("status") or "")
    if status_raw == "confirmed" and selection.get("role") == "ALUCOBOND_CASED_PANEL":
        status = BINDING_STATUS_CONFIRMED
    elif status_raw == "reconfirm_required":
        status = BINDING_STATUS_RECONFIRM
    else:
        return []
    casing = _as_dict(selection.get("casing_profile"))
    return [
        {
            "schema": SVG_COMPONENT_BINDINGS_SCHEMA,
            "binding_id": f"bind_support_{selection.get('contour_id') or 'legacy'}",
            "geometry_role": GEOMETRY_ROLE_SUPPORT_CONTOUR,
            "component_template_code": ACM_BOXED_SUPPORT,
            "selection_mode": "CLOSED_CONTOUR",
            "selected_geometry": {
                "layer_ids": [],
                "group_ids": [],
                "element_ids": [selection.get("contour_id")] if selection.get("contour_id") else [],
                "geometry_hashes": [selection.get("geometry_hash")]
                if selection.get("geometry_hash")
                else [],
                "source_svg_hash": selection.get("svg_source_hash"),
            },
            "configuration": {
                "fold_count": casing.get("fold_count"),
                "l1_mm": casing.get("l1_mm"),
                "l2_mm": casing.get("l2_mm"),
                "finished_depth_mm": casing.get("finished_depth_mm"),
                "service_corner": selection.get("service_corner"),
                "internal_frame_enabled": bool(selection.get("internal_frame_enabled")),
            },
            "panel_geometry": selection.get("panel_geometry"),
            "status": status,
            "provenance": "legacy_svg_support_selection",
        }
    ]


def build_svg_component_instances(finish: dict[str, Any] | None) -> list[dict[str, Any]]:
    """ProductDefinition projection: concrete component instances from bindings."""
    finish = finish or {}
    bindings = read_svg_component_bindings(finish) or hydrate_bindings_from_legacy_support(finish)
    instances: list[dict[str, Any]] = []
    for b in bindings:
        status = str(b.get("status") or "")
        if status not in {BINDING_STATUS_CONFIRMED, BINDING_STATUS_RECONFIRM}:
            continue
        code = str(b.get("component_template_code") or "").strip()
        if not code or code == STALE_BOND_CASETAT:
            continue
        geom = _as_dict(b.get("selected_geometry"))
        ids = [str(x) for x in _as_list(geom.get("element_ids")) if x]
        ids.extend(str(x) for x in _as_list(geom.get("layer_ids")) if x)
        instance = {
            "component_template_code": code,
            "geometry_role": b.get("geometry_role"),
            "selection_mode": b.get("selection_mode"),
            "selected_geometry_ids": ids,
            "geometry_hashes": list(_as_list(geom.get("geometry_hashes"))),
            "source_svg_hash": geom.get("source_svg_hash"),
            "configuration": _as_dict(b.get("configuration")),
            "status": status,
            "binding_id": b.get("binding_id"),
        }
        if code == FACE_COMPONENT or b.get("geometry_role") == GEOMETRY_ROLE_LETTER_VECTOR_SET:
            instance["legacy_layer_role"] = "face"
        if code == LOGO_PRODUCT or b.get("geometry_role") == GEOMETRY_ROLE_LOGO_VECTOR_SET:
            instance["legacy_layer_role"] = "printed_artwork"
        instances.append(instance)
    return instances
