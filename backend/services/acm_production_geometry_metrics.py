"""AcmPanel production geometry metrics contract + quantity resolution.

Owns path quantity truth for Pricing consumers. Does not own rates.
Extends Slice C face/assembly logic; replaces perimeter proxy only when safe.
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional

from services.acm_aci_semantic_mapping import ACM_ACI_SEMANTIC_MAPPING_VERSION
from services.acm_assembly_extent import (
    compute_acm_assembly_extent,
    inject_assembly_extent_keys,
    read_panels_for_assembly_extent,
)
from services.acm_quote_input_helpers import _fold_length_mm

ACM_PRODUCTION_GEOMETRY_METRICS_SCHEMA = "acm_panel_production_geometry_metrics_v1"
ACM_ASSEMBLY_GEOMETRY_METRICS_SCHEMA = "acm_panel_assembly_geometry_metrics_v1"


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


def _construction_from_instance(acm_instance: Mapping[str, Any] | None) -> dict[str, Any]:
    cfg = {}
    if isinstance(acm_instance, Mapping):
        raw = acm_instance.get("configuration")
        if isinstance(raw, Mapping):
            cfg = dict(raw)
    fold_count = cfg.get("fold_count")
    try:
        fold_count_i = int(fold_count) if fold_count is not None else None
    except (TypeError, ValueError):
        fold_count_i = None
    l1 = _num(cfg.get("l1_mm")) or _num(cfg.get("finished_depth_mm"))
    l2 = _num(cfg.get("l2_mm"))
    if fold_count_i == 1:
        construction = "single_fold"
    elif fold_count_i == 2 or (l2 is not None and l2 > 0):
        construction = "double_fold"
    elif l2 is None or l2 == 0:
        # Unknown fold_count with L2 absent — treat as single-fold candidate for proxy gating.
        construction = "single_fold"
    else:
        construction = "unknown"
    return {
        "construction_type": construction,
        "fold_count": fold_count_i,
        "l1_mm": l1,
        "l2_mm": l2 if l2 is not None else 0.0,
    }


def proxy_rectangular_eligible(
    *,
    construction_type: str,
    l2_mm: float | None,
    fold_sides: str,
    has_cutouts: bool,
    has_special_corners: bool,
    irregular_contour: bool,
) -> bool:
    if construction_type != "single_fold":
        return False
    if l2_mm is not None and l2_mm > 0:
        return False
    sides = str(fold_sides).strip().lower().replace("-", "_").replace(" ", "_")
    if sides not in {"all", "toate", "toate_laturile"}:
        return False
    if has_cutouts or has_special_corners or irregular_contour:
        return False
    return True


def build_panel_metrics_from_measured(
    measured: Mapping[str, Any],
    *,
    panel_id: str,
    active_width_mm: float | None,
    active_height_mm: float | None,
    l1_mm: float | None,
    l2_mm: float | None,
    construction_type: str,
) -> dict[str, Any]:
    aw = active_width_mm
    ah = active_height_mm
    face = None
    if aw is not None and ah is not None and aw > 0 and ah > 0:
        face = round((aw * ah) / 1_000_000.0, 6)
    blank = None
    l1 = l1_mm or 0.0
    l2 = l2_mm or 0.0
    if aw is not None and ah is not None and (l1 > 0 or l2 > 0):
        bw = aw + 2.0 * (l1 + l2)
        bh = ah + 2.0 * (l1 + l2)
        blank = round((bw * bh) / 1_000_000.0, 6)
    return {
        "schema": ACM_PRODUCTION_GEOMETRY_METRICS_SCHEMA,
        "panel_id": panel_id,
        "construction_type": construction_type,
        "active_width_mm": aw,
        "active_height_mm": ah,
        "l1_mm": l1_mm,
        "l2_mm": l2_mm if l2_mm is not None else 0.0,
        "active_face_area_m2": face,
        "blank_area_m2": blank,
        "cut_length_ml": measured.get("cut_length_ml"),
        "v_groove_l1_ml": measured.get("v_groove_l1_ml"),
        "v_groove_l2_ml": measured.get("v_groove_l2_ml"),
        "v_groove_total_ml": measured.get("v_groove_total_ml"),
        "measurement_source": measured.get("measurement_source") or "imported_dxf",
        "measurement_status": measured.get("measurement_status") or "measured",
        "semantic_mapping_version": measured.get("semantic_mapping_version")
        or ACM_ACI_SEMANTIC_MAPPING_VERSION,
        "warnings": list(measured.get("warnings") or []),
    }


def build_proxy_panel_metrics(
    *,
    panel_id: str,
    width_mm: float,
    height_mm: float,
    l1_mm: float | None,
    fold_sides: str,
) -> dict[str, Any]:
    """Explicit rectangular single-fold proxy (Slice C perimeter equivalence)."""
    cut_ml = round(2.0 * (width_mm + height_mm) / 1000.0, 6)
    fold_mm = _fold_length_mm(width_mm, height_mm, fold_sides)
    v_total = round((fold_mm or 0.0) / 1000.0, 6)
    face = round((width_mm * height_mm) / 1_000_000.0, 6)
    l1 = l1_mm or 0.0
    blank = None
    if l1 > 0:
        blank = round(((width_mm + 2 * l1) * (height_mm + 2 * l1)) / 1_000_000.0, 6)
    return {
        "schema": ACM_PRODUCTION_GEOMETRY_METRICS_SCHEMA,
        "panel_id": panel_id,
        "construction_type": "single_fold",
        "active_width_mm": width_mm,
        "active_height_mm": height_mm,
        "l1_mm": l1_mm,
        "l2_mm": 0.0,
        "active_face_area_m2": face,
        "blank_area_m2": blank,
        "cut_length_ml": cut_ml,
        "v_groove_l1_ml": v_total,
        "v_groove_l2_ml": 0.0,
        "v_groove_total_ml": v_total,
        "measurement_source": "proxy_rectangular",
        "measurement_status": "proxy_rectangular",
        "semantic_mapping_version": ACM_ACI_SEMANTIC_MAPPING_VERSION,
        "warnings": ["quantity_source=provisional_rectangular_single_fold_proxy"],
    }


def aggregate_assembly_metrics(
    panels: list[Mapping[str, Any]],
    *,
    assembly_width_mm: float | None,
    assembly_height_mm: float | None,
    joint_count: int = 0,
) -> dict[str, Any]:
    warnings: list[str] = []
    statuses = [str(p.get("measurement_status") or "") for p in panels]
    if any(s == "stale" for s in statuses):
        status = "stale"
    elif any(s == "unavailable" for s in statuses):
        status = "unavailable"
    elif panels and all(s in {"measured", "measured_with_warnings"} for s in statuses):
        status = (
            "measured_with_warnings"
            if any(s == "measured_with_warnings" for s in statuses)
            else "measured"
        )
    elif panels and all(s == "proxy_rectangular" for s in statuses):
        status = "proxy_rectangular"
    elif panels:
        status = "partial"
    else:
        status = "unavailable"

    def _sum(key: str) -> float | None:
        vals = []
        for p in panels:
            n = _num(p.get(key))
            if n is None:
                return None
            vals.append(n)
        return round(sum(vals), 6) if vals else None

    face_sum = _sum("active_face_area_m2")
    # Prefer assembly extent face when present (multi-panel overall).
    if assembly_width_mm and assembly_height_mm and assembly_width_mm > 0 and assembly_height_mm > 0:
        face_assembly = round((assembly_width_mm * assembly_height_mm) / 1_000_000.0, 6)
    else:
        face_assembly = face_sum

    cut = _sum("cut_length_ml")
    v1 = _sum("v_groove_l1_ml")
    v2 = _sum("v_groove_l2_ml")
    vtot = _sum("v_groove_total_ml")
    if vtot is None and v1 is not None and v2 is not None:
        vtot = round(v1 + v2, 6)

    for p in panels:
        for w in p.get("warnings") or []:
            if w not in warnings:
                warnings.append(str(w))

    if status == "proxy_rectangular":
        warnings.append("cut_v_quantity_source=proxy_rectangular")
    if status == "unavailable":
        warnings.append("quantity_unavailable")

    sources = sorted({str(p.get("measurement_source") or "") for p in panels if p.get("measurement_source")})

    return {
        "schema": ACM_ASSEMBLY_GEOMETRY_METRICS_SCHEMA,
        "assembly_width_mm": assembly_width_mm,
        "assembly_height_mm": assembly_height_mm,
        "panel_count": len(panels),
        "joint_count": joint_count,
        "panels": [dict(p) for p in panels],
        "total_active_face_area_m2": face_assembly,
        "total_blank_area_m2": _sum("blank_area_m2"),
        "total_cut_length_ml": cut,
        "total_v_groove_l1_ml": v1,
        "total_v_groove_l2_ml": v2,
        "total_v_groove_ml": vtot,
        "measurement_status": status,
        "measurement_source": sources[0] if len(sources) == 1 else ("mixed" if sources else None),
        "semantic_mapping_version": ACM_ACI_SEMANTIC_MAPPING_VERSION,
        "warnings": warnings,
    }


def resolve_production_geometry_metrics(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve assembly production metrics from measured DXF/metrics or gated proxy."""
    from services.acm_dxf_path_measurement import measure_dxf_production_paths

    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), Mapping) else {}
    acm_instance = _coalesce_acm_instance(payload)
    construction = _construction_from_instance(acm_instance)
    fold_sides = _read_fold_sides(payload, acm_instance)

    scratch: dict[str, Any] = dict(payload)
    inject_assembly_extent_keys(
        scratch,
        finish=finish if finish else payload,
        acm_instance=acm_instance,
    )
    panels_raw, assembly_dimensions, envelope_w, envelope_h = read_panels_for_assembly_extent(
        finish if finish else payload,
        acm_instance,
    )
    extent = compute_acm_assembly_extent(
        panels=panels_raw,
        assembly_dimensions=assembly_dimensions,
        envelope_width_mm=envelope_w if envelope_w is not None else scratch.get("assembly_width_mm"),
        envelope_height_mm=envelope_h,
    )
    aw = _num(scratch.get("assembly_width_mm")) or _num(extent.get("assembly_width_mm"))
    ah = _num(scratch.get("assembly_height_mm")) or _num(extent.get("assembly_height_mm"))

    joint_count = 0
    if isinstance(acm_instance, Mapping):
        geom = acm_instance.get("geometry") if isinstance(acm_instance.get("geometry"), Mapping) else {}
        joints = geom.get("joints") if isinstance(geom.get("joints"), list) else []
        joint_count = len(joints)

    # Build panel list early (attachment resolve + proxy)
    valid_panels: list[tuple[str, float, float]] = []
    for idx, p in enumerate(panels_raw or []):
        if not isinstance(p, Mapping):
            continue
        pw = _num(p.get("width_mm"))
        ph = _num(p.get("height_mm"))
        if pw is not None and ph is not None and pw > 0 and ph > 0:
            pid = str(p.get("panel_id") or f"p{idx + 1}")
            valid_panels.append((pid, pw, ph))

    if not valid_panels and aw and ah:
        valid_panels = [("assembly", aw, ah)]

    # Precomputed metrics on payload win only when explicitly provided for tests.
    precomputed = payload.get("acm_panel_production_geometry_metrics")
    if isinstance(precomputed, Mapping) and precomputed.get("schema") in {
        ACM_ASSEMBLY_GEOMETRY_METRICS_SCHEMA,
        ACM_PRODUCTION_GEOMETRY_METRICS_SCHEMA,
    }:
        if precomputed.get("schema") == ACM_ASSEMBLY_GEOMETRY_METRICS_SCHEMA:
            return dict(precomputed)
        return aggregate_assembly_metrics(
            [precomputed],
            assembly_width_mm=aw,
            assembly_height_mm=ah,
            joint_count=joint_count,
        )

    # Component-owned production_geometry attachments (live binding).
    from services.acm_production_geometry_attachment import resolve_metrics_from_attachments

    attached = resolve_metrics_from_attachments(
        payload,
        acm_instance=acm_instance,
        assembly_width_mm=aw,
        assembly_height_mm=ah,
        panels=valid_panels,
        construction=construction,
        joint_count=joint_count,
    )
    stale_attachment_warnings: list[str] = []
    if attached is not None:
        att_status = str(attached.get("measurement_status") or "")
        if att_status in {"measured", "measured_with_warnings"}:
            return attached
        if att_status == "stale":
            # Do not consume stale quantities; allow proxy fallback when eligible.
            stale_attachment_warnings = list(attached.get("warnings") or [])
            stale_attachment_warnings.append("production_geometry_stale")
        else:
            # invalid / semantic_mapping_required / unavailable from attachments
            return attached

    # Dev/test filesystem path (not operator SoT).
    dxf_path = (
        payload.get("acm_production_dxf_path")
        or (finish.get("acm_production_dxf_path") if isinstance(finish, Mapping) else None)
        or (
            (acm_instance or {}).get("production_dxf_path")
            if isinstance(acm_instance, Mapping)
            else None
        )
    )
    if isinstance(dxf_path, str) and dxf_path.strip():
        measured = measure_dxf_production_paths(dxf_path.strip())
        face_w = aw or envelope_w
        face_h = ah or envelope_h
        panel = build_panel_metrics_from_measured(
            measured,
            panel_id="dxf_import",
            active_width_mm=face_w,
            active_height_mm=face_h,
            l1_mm=construction["l1_mm"],
            l2_mm=construction["l2_mm"],
            construction_type=construction["construction_type"],
        )
        return aggregate_assembly_metrics(
            [panel],
            assembly_width_mm=aw or face_w,
            assembly_height_mm=ah or face_h,
            joint_count=joint_count,
        )

    has_cutouts = bool(payload.get("has_cutouts") or (finish or {}).get("has_cutouts"))
    has_special_corners = bool(
        payload.get("has_special_corners") or (finish or {}).get("has_special_corners")
    )
    irregular = bool(payload.get("irregular_contour") or (finish or {}).get("irregular_contour"))

    eligible = proxy_rectangular_eligible(
        construction_type=str(construction["construction_type"]),
        l2_mm=construction["l2_mm"],
        fold_sides=fold_sides,
        has_cutouts=has_cutouts,
        has_special_corners=has_special_corners,
        irregular_contour=irregular,
    )

    panel_metrics: list[dict[str, Any]] = []
    if eligible and valid_panels:
        for pid, pw, ph in valid_panels:
            panel_metrics.append(
                build_proxy_panel_metrics(
                    panel_id=pid,
                    width_mm=pw,
                    height_mm=ph,
                    l1_mm=construction["l1_mm"],
                    fold_sides=fold_sides,
                )
            )
    else:
        reasons = []
        if construction["construction_type"] == "double_fold":
            reasons.append("double_fold_proxy_forbidden")
        if construction["l2_mm"] and construction["l2_mm"] > 0:
            reasons.append("l2_active_proxy_forbidden")
        if not eligible:
            reasons.append("proxy_rectangular_not_eligible")
        reasons.append("quantity_unavailable")
        for pid, pw, ph in valid_panels or [("unknown", 0.0, 0.0)]:
            face = round((pw * ph) / 1_000_000.0, 6) if pw and ph else None
            panel_metrics.append(
                {
                    "schema": ACM_PRODUCTION_GEOMETRY_METRICS_SCHEMA,
                    "panel_id": pid,
                    "construction_type": construction["construction_type"],
                    "active_width_mm": pw or None,
                    "active_height_mm": ph or None,
                    "l1_mm": construction["l1_mm"],
                    "l2_mm": construction["l2_mm"],
                    "active_face_area_m2": face,
                    "blank_area_m2": None,
                    "cut_length_ml": None,
                    "v_groove_l1_ml": None,
                    "v_groove_l2_ml": None,
                    "v_groove_total_ml": None,
                    "measurement_source": "unavailable",
                    "measurement_status": "unavailable",
                    "semantic_mapping_version": ACM_ACI_SEMANTIC_MAPPING_VERSION,
                    "warnings": list(reasons),
                }
            )

    result = aggregate_assembly_metrics(
        panel_metrics,
        assembly_width_mm=aw,
        assembly_height_mm=ah,
        joint_count=joint_count,
    )
    if stale_attachment_warnings:
        warnings = list(result.get("warnings") or [])
        for w in stale_attachment_warnings:
            if w not in warnings:
                warnings.append(w)
        result["warnings"] = warnings
        if result.get("measurement_status") == "proxy_rectangular":
            # Proxy used after stale measured attachment — be explicit.
            result["measurement_source"] = "proxy_rectangular_after_stale"
    return result


def apply_production_metrics_to_commercial_payload(
    payload: MutableMapping[str, Any],
    *,
    commercial_face_area_m2: float | None,
    return_depth_mm: float,
) -> dict[str, Any]:
    """Apply resolved metrics onto CPP alias keys. Returns assembly metrics dict."""
    metrics = resolve_production_geometry_metrics(payload)
    payload["acm_panel_production_geometry_metrics"] = metrics

    # Face: prefer assembly commercial face (Slice C) when provided
    face = commercial_face_area_m2
    if face is None:
        face = _num(metrics.get("total_active_face_area_m2"))
    if face is not None:
        payload["commercial_face_area_m2"] = face
        payload["panel_area_m2"] = face

    status = str(metrics.get("measurement_status") or "")
    cut = _num(metrics.get("total_cut_length_ml"))
    vtot = _num(metrics.get("total_v_groove_ml"))

    consumable = status in {"measured", "measured_with_warnings", "proxy_rectangular"}
    if consumable and cut is not None:
        payload["commercial_cut_length_m"] = cut
        payload["panel_perimeter_m"] = cut
    else:
        # Do not leave stale perimeter proxy when unavailable/stale
        payload.pop("commercial_cut_length_m", None)
        payload.pop("panel_perimeter_m", None)

    if consumable and vtot is not None:
        payload["commercial_fold_length_m"] = vtot
        payload["fold_length_m"] = vtot
    else:
        payload.pop("commercial_fold_length_m", None)
        payload.pop("fold_length_m", None)

    # Return strip: blank-face when measured blank exists; else fold*depth when V available
    blank = _num(metrics.get("total_blank_area_m2"))
    if blank is not None and face is not None and blank >= face:
        payload["commercial_return_strip_area_m2"] = round(blank - face, 6)
        payload["return_strip_area_m2"] = payload["commercial_return_strip_area_m2"]
    elif vtot is not None and return_depth_mm > 0:
        area = round(vtot * (return_depth_mm / 1000.0), 6)
        payload["commercial_return_strip_area_m2"] = area
        payload["return_strip_area_m2"] = area

    payload["acm_path_quantity_status"] = status
    payload["acm_path_quantity_source"] = metrics.get("measurement_source")
    warnings = list(metrics.get("warnings") or [])
    if warnings:
        existing = payload.get("acm_commercial_geometry_warnings")
        merged = list(existing) if isinstance(existing, list) else []
        for w in warnings:
            if w not in merged:
                merged.append(w)
        payload["acm_commercial_geometry_warnings"] = merged
    return metrics
