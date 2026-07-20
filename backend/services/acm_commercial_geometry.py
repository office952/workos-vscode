"""AcmPanel commercial geometry adapter (Slice C + production metrics).

Face area from assembly_*.
CUT/V quantities from production geometry metrics (measured DXF) or
explicit single-fold rectangular proxy — never silent double-fold perimeter.
Never remaps panel_width_mm/panel_height_mm to assembly dimensions.
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional, Sequence

from services.acm_assembly_extent import (
    compute_acm_assembly_extent,
    inject_assembly_extent_keys,
    read_panels_for_assembly_extent,
)

ACM_COMMERCIAL_GEOMETRY_VERSION = "acm_commercial_geometry_v1"


def _num(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        n = float(value)
        return n if n == n and abs(n) != float("inf") else None
    if isinstance(value, str) and value.strip():
        try:
            n = float(value)
        except ValueError:
            return None
        return n if n == n and abs(n) != float("inf") else None
    return None


def _panel_wh(panel: Mapping[str, Any]) -> tuple[Optional[float], Optional[float]]:
    return _num(panel.get("width_mm")), _num(panel.get("height_mm"))


def _coalesce_acm_instance(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), Mapping) else {}
    inst = payload.get("acm_panel_instance")
    if not isinstance(inst, Mapping):
        inst = finish.get("acm_panel_instance") if isinstance(finish, Mapping) else None
    if not isinstance(inst, Mapping):
        ms = finish.get("mounting_solution") if isinstance(finish, Mapping) else None
        cfg = ms.get("configuration") if isinstance(ms, Mapping) else None
        if isinstance(cfg, Mapping) and isinstance(cfg.get("acm_panel_instance"), Mapping):
            inst = cfg.get("acm_panel_instance")
    if isinstance(inst, Mapping) and inst.get("schema") == "acm_panel_component_instance_v1":
        if str(inst.get("component_instance_id") or "").strip():
            return dict(inst)
    return None


def _read_return_depth_mm(payload: Mapping[str, Any], acm_instance: Mapping[str, Any] | None) -> float:
    for source in (
        payload.get("return_depth_mm"),
        (payload.get("finish_setup") or {}).get("return_depth_mm")
        if isinstance(payload.get("finish_setup"), Mapping)
        else None,
    ):
        n = _num(source)
        if n is not None and n > 0:
            return n
    ms = None
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), Mapping) else {}
    if isinstance(finish, Mapping):
        ms = finish.get("mounting_solution")
    if isinstance(ms, Mapping):
        cfg = ms.get("configuration") if isinstance(ms.get("configuration"), Mapping) else {}
        n = _num(cfg.get("return_depth_mm"))
        if n is not None and n > 0:
            return n
    if isinstance(acm_instance, Mapping):
        cfg = acm_instance.get("configuration") if isinstance(acm_instance.get("configuration"), Mapping) else {}
        n = _num(cfg.get("finished_depth_mm")) or _num(cfg.get("l1_mm"))
        if n is not None and n > 0:
            return n
    return 60.0


def _read_fold_sides(payload: Mapping[str, Any], acm_instance: Mapping[str, Any] | None) -> str:
    if payload.get("fold_sides") is not None and str(payload.get("fold_sides")).strip():
        return str(payload.get("fold_sides")).strip()
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), Mapping) else {}
    ms = finish.get("mounting_solution") if isinstance(finish, Mapping) else None
    cfg = ms.get("configuration") if isinstance(ms, Mapping) else None
    if isinstance(cfg, Mapping) and cfg.get("fold_sides") is not None and str(cfg.get("fold_sides")).strip():
        return str(cfg.get("fold_sides")).strip()
    if isinstance(acm_instance, Mapping):
        icfg = acm_instance.get("configuration") if isinstance(acm_instance.get("configuration"), Mapping) else {}
        if icfg.get("fold_sides"):
            return str(icfg.get("fold_sides")).strip()
    return "all"


def compute_acm_commercial_geometry(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Return commercial quantity keys + geometry summary (does not mutate payload)."""
    warnings: list[str] = []
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), Mapping) else {}
    acm_instance = _coalesce_acm_instance(payload)

    scratch: dict[str, Any] = dict(payload)
    inject_assembly_extent_keys(
        scratch,
        finish=finish if finish else payload,
        acm_instance=acm_instance,
    )

    panels, assembly_dimensions, envelope_w, envelope_h = read_panels_for_assembly_extent(
        finish if finish else payload,
        acm_instance,
    )
    if not panels and isinstance(scratch.get("segmented_background_proposal"), Mapping):
        prop = scratch["segmented_background_proposal"]
        if isinstance(prop.get("panels"), list):
            panels = [p for p in prop["panels"] if isinstance(p, Mapping)]
        if assembly_dimensions is None and isinstance(prop.get("assembly_dimensions"), Mapping):
            assembly_dimensions = prop.get("assembly_dimensions")

    extent = compute_acm_assembly_extent(
        panels=panels,
        assembly_dimensions=assembly_dimensions,
        envelope_width_mm=envelope_w if envelope_w is not None else scratch.get("assembly_width_mm"),
        envelope_height_mm=envelope_h,
    )
    # Prefer inject results when present
    aw = _num(scratch.get("assembly_width_mm")) or _num(extent.get("assembly_width_mm"))
    ah = _num(scratch.get("assembly_height_mm")) or _num(extent.get("assembly_height_mm"))
    for w in extent.get("warnings") or []:
        warnings.append(str(w))

    valid_panels: list[tuple[float, float]] = []
    for p in panels or []:
        if not isinstance(p, Mapping):
            continue
        pw, ph = _panel_wh(p)
        if pw is not None and ph is not None and pw > 0 and ph > 0:
            valid_panels.append((pw, ph))

    fold_sides = _read_fold_sides(payload, acm_instance)
    return_depth = _read_return_depth_mm(payload, acm_instance)

    # Face / assembly extent only — CUT/V resolved by production metrics (measured|proxy|unavailable).
    commercial_face_area_m2: Optional[float] = None
    assembly_exterior_perimeter_m: Optional[float] = None
    mode = "none"

    if aw is not None and ah is not None and aw > 0 and ah > 0:
        commercial_face_area_m2 = round((aw * ah) / 1_000_000.0, 6)
        assembly_exterior_perimeter_m = round(2.0 * (aw + ah) / 1000.0, 6)

    if len(valid_panels) >= 2:
        mode = "multi_panel"
        if (
            commercial_face_area_m2 is not None
            and envelope_w is not None
            and abs((envelope_w * (ah or 0)) / 1_000_000.0 - commercial_face_area_m2) > 1e-6
        ):
            warnings.append("envelope_not_used_for_commercial_face_area")
    elif len(valid_panels) == 1:
        mode = "single_panel"
        pw, ph = valid_panels[0]
        if commercial_face_area_m2 is None:
            commercial_face_area_m2 = round((pw * ph) / 1_000_000.0, 6)
            aw = pw
            ah = ph
    elif aw is not None and ah is not None:
        mode = "assembly_fallback"
        warnings.append("missing_panel_list_assembly_face_only")

    joint_count = 0
    if isinstance(acm_instance, Mapping):
        geom = acm_instance.get("geometry") if isinstance(acm_instance.get("geometry"), Mapping) else {}
        joints = geom.get("joints") if isinstance(geom.get("joints"), list) else []
        joint_count = len(joints)
    if joint_count == 0 and isinstance(finish, Mapping):
        seg = finish.get("segmented_background")
        if isinstance(seg, Mapping) and isinstance(seg.get("joints"), list):
            joint_count = len(seg["joints"])

    if joint_count > 0:
        warnings.append("segmentation_joints_no_commercial_rate")

    return {
        "version": ACM_COMMERCIAL_GEOMETRY_VERSION,
        "mode": mode,
        "assembly_width_mm": aw,
        "assembly_height_mm": ah,
        "envelope_width_mm": envelope_w,
        "envelope_height_mm": envelope_h,
        "panel_count": len(valid_panels),
        "joint_count": joint_count,
        "commercial_face_area_m2": commercial_face_area_m2,
        "assembly_exterior_perimeter_m": assembly_exterior_perimeter_m,
        "return_depth_mm": return_depth,
        "fold_sides": fold_sides,
        "warnings": warnings,
        "envelope_ignored_for_multi_panel": bool(
            scratch.get("assembly_extent_envelope_ignored")
            or extent.get("envelope_ignored_for_multi_panel")
        ),
    }


def apply_acm_commercial_geometry(payload: MutableMapping[str, Any]) -> list[str]:
    """Mutate payload: set commercial_* and alias CPP quantity keys. Returns warnings.

    Does not overwrite panel_width_mm / panel_height_mm with assembly dims.
    CUT/V come from production metrics (measured or gated proxy), not universal perimeter.
    """
    from services.acm_production_geometry_metrics import apply_production_metrics_to_commercial_payload

    geom = compute_acm_commercial_geometry(payload)
    warnings = list(geom.get("warnings") or [])

    if geom.get("assembly_width_mm") is not None:
        payload["assembly_width_mm"] = geom["assembly_width_mm"]
    if geom.get("assembly_height_mm") is not None:
        payload["assembly_height_mm"] = geom["assembly_height_mm"]

    # Clear legacy derive perimeter/fold before metrics resolve (avoid silent stale proxy).
    for key in (
        "panel_perimeter_m",
        "fold_length_m",
        "commercial_cut_length_m",
        "commercial_fold_length_m",
        "return_strip_area_m2",
        "commercial_return_strip_area_m2",
    ):
        payload.pop(key, None)

    metrics = apply_production_metrics_to_commercial_payload(
        payload,
        commercial_face_area_m2=geom.get("commercial_face_area_m2"),
        return_depth_mm=float(geom.get("return_depth_mm") or 60.0),
    )
    warnings.extend(list(metrics.get("warnings") or []))

    if geom.get("assembly_exterior_perimeter_m") is not None:
        payload["assembly_exterior_perimeter_m"] = geom["assembly_exterior_perimeter_m"]

    payload["acm_commercial_geometry"] = {
        k: geom[k]
        for k in (
            "version",
            "mode",
            "assembly_width_mm",
            "assembly_height_mm",
            "envelope_width_mm",
            "envelope_height_mm",
            "panel_count",
            "joint_count",
            "commercial_face_area_m2",
            "assembly_exterior_perimeter_m",
            "envelope_ignored_for_multi_panel",
        )
        if k in geom
    }
    payload["acm_commercial_geometry"]["commercial_cut_length_m"] = payload.get(
        "commercial_cut_length_m"
    )
    payload["acm_commercial_geometry"]["commercial_fold_length_m"] = payload.get(
        "commercial_fold_length_m"
    )
    payload["acm_commercial_geometry"]["commercial_return_strip_area_m2"] = payload.get(
        "commercial_return_strip_area_m2"
    )
    payload["acm_commercial_geometry"]["path_measurement_status"] = metrics.get(
        "measurement_status"
    )
    payload["acm_commercial_geometry"]["path_measurement_source"] = metrics.get(
        "measurement_source"
    )
    payload["acm_commercial_geometry"]["v_groove_l1_ml"] = metrics.get("total_v_groove_l1_ml")
    payload["acm_commercial_geometry"]["v_groove_l2_ml"] = metrics.get("total_v_groove_l2_ml")
    payload["acm_commercial_geometry"]["v_groove_total_ml"] = metrics.get("total_v_groove_ml")

    payload["acm_commercial_geometry_version"] = ACM_COMMERCIAL_GEOMETRY_VERSION
    if warnings:
        existing = payload.get("acm_commercial_geometry_warnings")
        merged = list(existing) if isinstance(existing, list) else []
        for w in warnings:
            if w not in merged:
                merged.append(w)
        payload["acm_commercial_geometry_warnings"] = merged
    return warnings


def build_acm_panel_authority_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Authority gates for AcmPanel provisional pricing (read-only projection)."""
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), Mapping) else {}
    inst = _coalesce_acm_instance(payload) or {}
    seg = finish.get("segmented_background") if isinstance(finish, Mapping) else None
    seg_status = str((seg or {}).get("status") or "").upper() if isinstance(seg, Mapping) else None

    tech = str(inst.get("technical_configuration_status") or "").strip().lower()
    assoc = str(inst.get("association_status") or "").strip().lower()
    composition = str(inst.get("composition_status") or "").strip().lower()

    field_authority = {}
    cfg = inst.get("configuration") if isinstance(inst.get("configuration"), Mapping) else {}
    if isinstance(cfg.get("field_authority"), Mapping):
        field_authority = dict(cfg["field_authority"])
    elif isinstance(finish, Mapping):
        ms = finish.get("mounting_solution")
        mcfg = ms.get("configuration") if isinstance(ms, Mapping) else None
        if isinstance(mcfg, Mapping) and isinstance(mcfg.get("field_authority"), Mapping):
            field_authority = dict(mcfg["field_authority"])

    catalog_defaults = [
        k
        for k, v in field_authority.items()
        if str(v).strip().lower() == "catalog_default"
    ]

    composition_inconsistent = composition in {"unconfirmed", "inconsistent", "blocked"}
    # Prefer explicit composition inconsistency signal when present
    if isinstance(finish, Mapping) and finish.get("acm_panel_composition_inconsistent") is True:
        composition_inconsistent = True

    technical_confirmed = tech == "confirmed"
    segmented_confirmed = seg_status == "CONFIRMED"

    warnings: list[str] = []
    blockers: list[str] = []
    if not technical_confirmed:
        warnings.append("technical_configuration_unconfirmed")
    if catalog_defaults:
        warnings.append("construction_catalog_defaults")
    if seg_status == "PROPOSED":
        warnings.append("segmentation_proposed")
    if composition_inconsistent or composition == "unconfirmed":
        warnings.append("composition_inconsistent_or_unconfirmed")
        composition_inconsistent = True

    final_eligible = (
        technical_confirmed
        and segmented_confirmed
        and not composition_inconsistent
        and not catalog_defaults
    )
    offer_eligible = final_eligible
    execution_eligible = False  # hard boundary this slice

    if not final_eligible:
        blockers.append("final_price_unavailable")
        blockers.append("offer_ferm_unavailable")
    blockers.append("execution_blocked")

    status = "unavailable"
    if inst:
        status = "provisional_with_warnings" if warnings else "provisional_ready"
        if final_eligible:
            status = "official_ready"

    return {
        "status": status,
        "association_status": assoc or None,
        "technical_configuration_status": tech or None,
        "composition_status": composition or None,
        "segmented_status": seg_status,
        "catalog_default_fields": catalog_defaults,
        "technical_confirmed": technical_confirmed,
        "segmented_confirmed": segmented_confirmed,
        "composition_inconsistent": composition_inconsistent,
        "final_eligibility": final_eligible,
        "offer_eligibility": offer_eligible,
        "execution_eligibility": execution_eligible,
        "warnings": warnings,
        "blockers": blockers,
    }
