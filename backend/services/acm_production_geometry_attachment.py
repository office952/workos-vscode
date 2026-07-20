"""AcmPanel production DXF attachment — V6 workspace disk storage + instance binding.

Owner: AcmPanel component instance (JSON-on-instance). Workspace provides namespace only.
Does not use Work Intake Intake_requests work-file ownership.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Optional

from fastapi import HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from services.acm_aci_semantic_mapping import ACM_ACI_SEMANTIC_MAPPING_VERSION
from services.acm_dxf_path_measurement import measure_dxf_production_paths
from services.acm_production_geometry_metrics import (
    ACM_ASSEMBLY_GEOMETRY_METRICS_SCHEMA,
    ACM_PRODUCTION_GEOMETRY_METRICS_SCHEMA,
    _coalesce_acm_instance,
    _construction_from_instance,
    _num,
    _read_fold_sides,
    aggregate_assembly_metrics,
    build_panel_metrics_from_measured,
)

logger = logging.getLogger(__name__)

STORAGE_ROOT = Path(__file__).resolve().parent.parent / "storage" / "intake_v6_production_geometry"
MAX_DXF_BYTES = 50 * 1024 * 1024
MAX_ENTITY_COUNT = 50_000
MAX_ABS_COORD_MM = 1.0e7
MIN_ENTITY_LENGTH_MM = 1.0e-6

PRODUCTION_GEOMETRY_BUNDLE_SCHEMA = "acm_panel_production_geometry_bundle_v1"
PRODUCTION_GEOMETRY_ATTACHMENT_SCHEMA = "acm_panel_production_geometry_attachment_v1"
MEASUREMENT_SERVICE_VERSION = "acm_dxf_path_measurement_v1"

GEOMETRY_ROLE_PRODUCTION = "production_geometry"
ELIGIBLE_GEOMETRY_ROLES = frozenset({GEOMETRY_ROLE_PRODUCTION, "cut_v_paths"})

MEASUREMENT_STATUSES = frozenset(
    {
        "no_attachment",
        "uploaded",
        "validating",
        "invalid",
        "semantic_mapping_required",
        "measured",
        "measured_with_warnings",
        "stale",
        "replaced",
        "archived",
        "proxy_rectangular",
        "unavailable",
    }
)

CONSUMABLE_MEASUREMENT_STATUSES = frozenset({"measured", "measured_with_warnings"})


def sanitize_dxf_filename(raw_name: str) -> str:
    raw = (raw_name or "").strip()
    if ".." in raw.replace("\\", "/"):
        raise ValueError("Filename is not valid")
    base = raw.replace("\\", "/").split("/")[-1]
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
    suffix = Path(base).suffix.lower()
    if suffix != ".dxf":
        raise ValueError("Extensie neacceptată. Doar .dxf este permis pentru geometrie de producție.")
    if base in {"", ".", ".."} or ".." in base:
        raise ValueError("Filename is not valid")
    return base


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _looks_like_dxf(raw: bytes) -> bool:
    head = raw[:4096]
    if b"SECTION" in head.upper() or b"0\r\nSECTION" in head or b"0\nSECTION" in head:
        return True
    # ASCII DXF often starts with "  0"
    text = head.decode("latin-1", errors="ignore").lstrip()
    return text.startswith("0") and "SECTION" in text.upper()[:200]


def validate_dxf_bytes(raw: bytes, *, filename: str) -> dict[str, Any]:
    """Validate DXF bytes before store. Returns validation outcome dict."""
    warnings: list[str] = []
    if not raw:
        return {"outcome": "rejected", "code": "empty_file", "warnings": warnings}
    if len(raw) > MAX_DXF_BYTES:
        return {
            "outcome": "rejected",
            "code": "oversized",
            "warnings": warnings,
            "detail": f"max_bytes={MAX_DXF_BYTES}",
        }
    # Reject ZIP/archives by magic before DXF signature heuristics.
    if raw[:2] == b"PK":
        return {"outcome": "rejected", "code": "archive_not_allowed", "warnings": warnings}
    try:
        sanitize_dxf_filename(filename)
    except ValueError as exc:
        return {"outcome": "rejected", "code": "invalid_filename", "warnings": warnings, "detail": str(exc)}
    if not _looks_like_dxf(raw):
        return {"outcome": "rejected", "code": "invalid_signature", "warnings": warnings}
    return {"outcome": "accepted", "code": "ok", "warnings": warnings}


def compute_config_fingerprint(
    *,
    payload: Mapping[str, Any],
    acm_instance: Mapping[str, Any] | None = None,
) -> str:
    """Stable fingerprint of construction/geometry inputs that invalidate measured DXF."""
    from services.acm_assembly_extent import (
        compute_acm_assembly_extent,
        inject_assembly_extent_keys,
        read_panels_for_assembly_extent,
    )

    inst = acm_instance if isinstance(acm_instance, Mapping) else _coalesce_acm_instance(payload)
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), Mapping) else {}
    construction = _construction_from_instance(inst)
    fold_sides = _read_fold_sides(payload, inst)

    scratch: dict[str, Any] = dict(payload)
    inject_assembly_extent_keys(scratch, finish=finish if finish else payload, acm_instance=inst)
    panels_raw, assembly_dimensions, envelope_w, envelope_h = read_panels_for_assembly_extent(
        finish if finish else payload,
        inst,
    )
    extent = compute_acm_assembly_extent(
        panels=panels_raw,
        assembly_dimensions=assembly_dimensions,
        envelope_width_mm=envelope_w if envelope_w is not None else scratch.get("assembly_width_mm"),
        envelope_height_mm=envelope_h,
    )
    aw = _num(scratch.get("assembly_width_mm")) or _num(extent.get("assembly_width_mm"))
    ah = _num(scratch.get("assembly_height_mm")) or _num(extent.get("assembly_height_mm"))

    panel_rows: list[dict[str, Any]] = []
    for idx, p in enumerate(panels_raw or []):
        if not isinstance(p, Mapping):
            continue
        pos = p.get("position") if isinstance(p.get("position"), Mapping) else {}
        panel_rows.append(
            {
                "panel_id": str(p.get("panel_id") or f"p{idx + 1}"),
                "width_mm": _num(p.get("width_mm")),
                "height_mm": _num(p.get("height_mm")),
                "x_mm": _num(pos.get("x_mm")) if pos else None,
                "y_mm": _num(pos.get("y_mm")) if pos else None,
                "order": p.get("order"),
            }
        )
    panel_rows.sort(key=lambda r: (str(r.get("panel_id") or ""),))

    geom = inst.get("geometry") if isinstance(inst, Mapping) else {}
    geom = geom if isinstance(geom, Mapping) else {}
    cfg = inst.get("configuration") if isinstance(inst, Mapping) else {}
    cfg = cfg if isinstance(cfg, Mapping) else {}

    cutout_state = bool(payload.get("has_cutouts") or finish.get("has_cutouts"))
    irregular = bool(payload.get("irregular_contour") or finish.get("irregular_contour"))
    special = bool(payload.get("has_special_corners") or finish.get("has_special_corners"))

    body = {
        "active_width_mm": aw,
        "active_height_mm": ah,
        "l1_mm": construction.get("l1_mm"),
        "l2_mm": construction.get("l2_mm"),
        "construction_type": construction.get("construction_type"),
        "panel_count": len(panel_rows),
        "panel_dimensions": [
            {"panel_id": r["panel_id"], "width_mm": r["width_mm"], "height_mm": r["height_mm"]}
            for r in panel_rows
        ],
        "panel_positions": [
            {"panel_id": r["panel_id"], "x_mm": r["x_mm"], "y_mm": r["y_mm"]} for r in panel_rows
        ],
        "fold_sides": fold_sides,
        "corner_method": cfg.get("service_corner"),
        "cutout_state": {"has_cutouts": cutout_state, "irregular": irregular, "special_corners": special},
        "segmentation_version": {
            "geometry_hash": geom.get("geometry_hash"),
            "joint_count": len(geom.get("joints") or []) if isinstance(geom.get("joints"), list) else 0,
        },
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _storage_dir(workspace_id: str) -> Path:
    safe_ws = re.sub(r"[^A-Za-z0-9._-]+", "_", (workspace_id or "").strip())
    if not safe_ws or safe_ws in {".", ".."}:
        raise HTTPException(status_code=400, detail={"error": "invalid_workspace_id"})
    return STORAGE_ROOT / safe_ws


def resolve_attachment_disk_path(workspace_id: str, storage_reference: str) -> Path:
    """Resolve and assert path stays under workspace storage root."""
    root = _storage_dir(workspace_id).resolve()
    name = Path(str(storage_reference or "").replace("\\", "/")).name
    if not name or name in {".", ".."} or ".." in name:
        raise HTTPException(status_code=400, detail={"error": "invalid_storage_reference"})
    path = (root / name).resolve()
    if not str(path).startswith(str(root)):
        raise HTTPException(status_code=400, detail={"error": "path_traversal_blocked"})
    return path


def measure_and_guard_dxf(path: Path) -> dict[str, Any]:
    """Measure DXF with entity-count / extreme-coordinate guards."""
    try:
        measured = measure_dxf_production_paths(path)
    except Exception as exc:
        return {
            "measurement_status": "invalid",
            "warnings": [f"dxf_parse_failed:{type(exc).__name__}"],
            "cut_length_ml": None,
            "v_groove_l1_ml": None,
            "v_groove_l2_ml": None,
            "v_groove_total_ml": None,
            "semantic_mapping_version": ACM_ACI_SEMANTIC_MAPPING_VERSION,
            "measurement_source": "imported_dxf",
        }

    warnings = list(measured.get("warnings") or [])
    trace = measured.get("entity_trace") or []
    if len(trace) > MAX_ENTITY_COUNT:
        return {
            "measurement_status": "invalid",
            "warnings": warnings + [f"entity_count_exceeded:{len(trace)}"],
            "cut_length_ml": None,
            "v_groove_l1_ml": None,
            "v_groove_l2_ml": None,
            "v_groove_total_ml": None,
            "semantic_mapping_version": ACM_ACI_SEMANTIC_MAPPING_VERSION,
            "measurement_source": "imported_dxf",
        }

    # Extreme coordinates / zero-length from re-open via ezdxf
    try:
        import ezdxf

        doc = ezdxf.readfile(str(path))
        extreme = False
        zero_len = 0
        for entity in doc.modelspace():
            from services.acm_dxf_path_measurement import measure_entity_length_mm

            length = measure_entity_length_mm(entity)
            if length is not None and length < MIN_ENTITY_LENGTH_MM:
                zero_len += 1
            for attr in ("start", "end", "center"):
                pt = getattr(entity.dxf, attr, None)
                if pt is not None and (abs(float(pt.x)) > MAX_ABS_COORD_MM or abs(float(pt.y)) > MAX_ABS_COORD_MM):
                    extreme = True
            if entity.dxftype() == "SPLINE":
                try:
                    for c in entity.control_points:
                        if abs(float(c[0])) > MAX_ABS_COORD_MM or abs(float(c[1])) > MAX_ABS_COORD_MM:
                            extreme = True
                except Exception:
                    pass
        if extreme:
            warnings.append("extreme_coordinates")
            measured["measurement_status"] = "invalid"
            measured["warnings"] = warnings
            measured["cut_length_ml"] = None
            measured["v_groove_l1_ml"] = None
            measured["v_groove_l2_ml"] = None
            measured["v_groove_total_ml"] = None
            return measured
        if zero_len:
            warnings.append(f"zero_length_entities:{zero_len}")
    except Exception as exc:
        warnings.append(f"coordinate_guard_failed:{type(exc).__name__}")

    unknown_colors = measured.get("unknown_aci_colors") or []
    unknown_ml = _num(measured.get("unknown_length_ml")) or 0.0
    cut = _num(measured.get("cut_length_ml")) or 0.0
    vtot = _num(measured.get("v_groove_total_ml")) or 0.0

    status = str(measured.get("measurement_status") or "measured")
    if cut <= 0 and vtot <= 0 and unknown_ml > 0:
        status = "semantic_mapping_required"
        warnings.append("semantic_mapping_required")
    elif unknown_colors or unknown_ml > 0:
        status = "measured_with_warnings"
        warnings.append("unknown_aci_excluded_from_totals")
    elif status == "unavailable":
        status = "semantic_mapping_required"

    measured["measurement_status"] = status
    measured["warnings"] = list(dict.fromkeys(warnings))
    measured["measurement_version"] = MEASUREMENT_SERVICE_VERSION
    return measured


def get_production_geometry_bundle(acm_instance: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(acm_instance, Mapping):
        return {"schema": PRODUCTION_GEOMETRY_BUNDLE_SCHEMA, "attachments": []}
    raw = acm_instance.get("production_geometry")
    if isinstance(raw, Mapping) and raw.get("schema") == PRODUCTION_GEOMETRY_BUNDLE_SCHEMA:
        atts = raw.get("attachments") if isinstance(raw.get("attachments"), list) else []
        return {
            "schema": PRODUCTION_GEOMETRY_BUNDLE_SCHEMA,
            "attachments": [dict(a) for a in atts if isinstance(a, Mapping)],
        }
    return {"schema": PRODUCTION_GEOMETRY_BUNDLE_SCHEMA, "attachments": []}


def list_active_attachments(bundle: Mapping[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for a in bundle.get("attachments") or []:
        if not isinstance(a, Mapping):
            continue
        st = str(a.get("measurement_status") or "")
        if st in {"replaced", "archived"}:
            continue
        out.append(dict(a))
    return out


def mark_stale_attachments_in_instance(
    acm_instance: MutableMapping[str, Any],
    *,
    current_fingerprint: str,
) -> bool:
    """Mark measured attachments stale when fingerprint mismatches. Returns True if mutated."""
    bundle = get_production_geometry_bundle(acm_instance)
    changed = False
    new_atts: list[dict[str, Any]] = []
    for a in bundle.get("attachments") or []:
        row = dict(a)
        st = str(row.get("measurement_status") or "")
        fp = str(row.get("config_fingerprint") or "")
        if st in CONSUMABLE_MEASUREMENT_STATUSES and fp and fp != current_fingerprint:
            row["measurement_status"] = "stale"
            warnings = list(row.get("warnings") or [])
            if "config_fingerprint_mismatch" not in warnings:
                warnings.append("config_fingerprint_mismatch")
            row["warnings"] = warnings
            changed = True
        new_atts.append(row)
    if changed:
        acm_instance["production_geometry"] = {
            "schema": PRODUCTION_GEOMETRY_BUNDLE_SCHEMA,
            "attachments": new_atts,
        }
    return changed


def resolve_metrics_from_attachments(
    payload: Mapping[str, Any],
    *,
    acm_instance: Mapping[str, Any] | None,
    assembly_width_mm: float | None,
    assembly_height_mm: float | None,
    panels: list[tuple[str, float, float]],
    construction: Mapping[str, Any],
    joint_count: int,
) -> dict[str, Any] | None:
    """Return assembly metrics from active production_geometry attachments, or None."""
    bundle = get_production_geometry_bundle(acm_instance)
    active = [
        a
        for a in list_active_attachments(bundle)
        if str(a.get("geometry_role") or "") in ELIGIBLE_GEOMETRY_ROLES
    ]
    if not active:
        return None

    current_fp = compute_config_fingerprint(payload=payload, acm_instance=acm_instance)
    panel_metrics: list[dict[str, Any]] = []
    used_panels: set[str] = set()

    for att in active:
        st = str(att.get("measurement_status") or "")
        fp = str(att.get("config_fingerprint") or "")
        if fp and fp != current_fp:
            st = "stale"
        if st not in CONSUMABLE_MEASUREMENT_STATUSES:
            continue
        role = str(att.get("geometry_role") or "")
        if role not in ELIGIBLE_GEOMETRY_ROLES:
            continue

        panel_id = str(att.get("panel_id") or "").strip() or None
        snap = att.get("metrics_snapshot")
        if isinstance(snap, Mapping) and snap.get("schema") == ACM_PRODUCTION_GEOMETRY_METRICS_SCHEMA:
            row = dict(snap)
            if panel_id:
                row["panel_id"] = panel_id
            panel_metrics.append(row)
            if panel_id:
                used_panels.add(panel_id)
            continue

        # Live remeasure from disk if snapshot missing
        storage_ref = str(att.get("storage_reference") or "")
        workspace_id = str(att.get("workspace_id") or "")
        if not storage_ref or not workspace_id:
            continue
        try:
            path = resolve_attachment_disk_path(workspace_id, storage_ref)
            if not path.is_file():
                continue
            measured = measure_and_guard_dxf(path)
        except HTTPException:
            continue
        if str(measured.get("measurement_status") or "") not in CONSUMABLE_MEASUREMENT_STATUSES:
            continue
        # Bind dims from panel list
        pw = ph = None
        pid = panel_id or "dxf_import"
        for p_id, w, h in panels:
            if panel_id and p_id == panel_id:
                pw, ph, pid = w, h, p_id
                break
        if pw is None and len(panels) == 1 and panel_id is None:
            pid, pw, ph = panels[0]
        if pw is None:
            pw = assembly_width_mm
            ph = assembly_height_mm
        panel_metrics.append(
            build_panel_metrics_from_measured(
                measured,
                panel_id=pid,
                active_width_mm=pw,
                active_height_mm=ph,
                l1_mm=construction.get("l1_mm"),
                l2_mm=construction.get("l2_mm"),
                construction_type=str(construction.get("construction_type") or "unknown"),
            )
        )
        used_panels.add(pid)

    if not panel_metrics:
        # Attachments exist but none consumable (stale/invalid) — signal via empty with status
        stale_or_bad = any(
            str(a.get("measurement_status") or "") in {"stale", "invalid", "semantic_mapping_required"}
            or (
                str(a.get("config_fingerprint") or "")
                and str(a.get("config_fingerprint")) != current_fp
            )
            for a in active
        )
        if stale_or_bad:
            return aggregate_assembly_metrics(
                [
                    {
                        "schema": ACM_PRODUCTION_GEOMETRY_METRICS_SCHEMA,
                        "panel_id": pid,
                        "construction_type": construction.get("construction_type"),
                        "active_width_mm": pw,
                        "active_height_mm": ph,
                        "l1_mm": construction.get("l1_mm"),
                        "l2_mm": construction.get("l2_mm"),
                        "active_face_area_m2": round((pw * ph) / 1e6, 6) if pw and ph else None,
                        "blank_area_m2": None,
                        "cut_length_ml": None,
                        "v_groove_l1_ml": None,
                        "v_groove_l2_ml": None,
                        "v_groove_total_ml": None,
                        "measurement_source": "stale" if any(
                            str(a.get("measurement_status")) == "stale"
                            or (
                                str(a.get("config_fingerprint") or "")
                                and str(a.get("config_fingerprint")) != current_fp
                            )
                            for a in active
                        )
                        else "unavailable",
                        "measurement_status": "stale"
                        if any(
                            str(a.get("measurement_status")) == "stale"
                            or (
                                str(a.get("config_fingerprint") or "")
                                and str(a.get("config_fingerprint")) != current_fp
                            )
                            for a in active
                        )
                        else "unavailable",
                        "semantic_mapping_version": ACM_ACI_SEMANTIC_MAPPING_VERSION,
                        "warnings": ["attachment_not_consumable"],
                    }
                    for pid, pw, ph in (panels or [("unknown", 0.0, 0.0)])
                ],
                assembly_width_mm=assembly_width_mm,
                assembly_height_mm=assembly_height_mm,
                joint_count=joint_count,
            )
        return None

    # Missing panel attachments → unavailable for those panels (no silent reuse)
    if panels and len(panels) > 1:
        for pid, pw, ph in panels:
            if pid in used_panels:
                continue
            # Only add missing if we have per-panel attachments (not single assembly attach)
            if any(a.get("panel_id") for a in active):
                panel_metrics.append(
                    {
                        "schema": ACM_PRODUCTION_GEOMETRY_METRICS_SCHEMA,
                        "panel_id": pid,
                        "construction_type": construction.get("construction_type"),
                        "active_width_mm": pw,
                        "active_height_mm": ph,
                        "l1_mm": construction.get("l1_mm"),
                        "l2_mm": construction.get("l2_mm"),
                        "active_face_area_m2": round((pw * ph) / 1e6, 6),
                        "blank_area_m2": None,
                        "cut_length_ml": None,
                        "v_groove_l1_ml": None,
                        "v_groove_l2_ml": None,
                        "v_groove_total_ml": None,
                        "measurement_source": "unavailable",
                        "measurement_status": "unavailable",
                        "semantic_mapping_version": ACM_ACI_SEMANTIC_MAPPING_VERSION,
                        "warnings": ["missing_panel_attachment"],
                    }
                )

    return aggregate_assembly_metrics(
        panel_metrics,
        assembly_width_mm=assembly_width_mm,
        assembly_height_mm=assembly_height_mm,
        joint_count=joint_count,
    )


def _find_instance_sites(payload_raw: dict[str, Any], component_instance_id: str) -> list[tuple[list[str], dict[str, Any]]]:
    """Return (path_keys, instance_dict) sites matching component_instance_id."""
    sites: list[tuple[list[str], dict[str, Any]]] = []
    finish = payload_raw.get("finish_setup")
    if not isinstance(finish, dict):
        return sites
    cid = component_instance_id.strip()

    def _match(inst: Any) -> bool:
        return (
            isinstance(inst, dict)
            and inst.get("schema") == "acm_panel_component_instance_v1"
            and str(inst.get("component_instance_id") or "").strip() == cid
        )

    if _match(finish.get("acm_panel_instance")):
        sites.append((["finish_setup", "acm_panel_instance"], finish["acm_panel_instance"]))
    sel = finish.get("svg_support_selection")
    if isinstance(sel, dict) and _match(sel.get("acm_panel_instance")):
        sites.append(
            (["finish_setup", "svg_support_selection", "acm_panel_instance"], sel["acm_panel_instance"])
        )
    ms = finish.get("mounting_solution")
    if isinstance(ms, dict):
        cfg = ms.get("configuration")
        if isinstance(cfg, dict) and _match(cfg.get("acm_panel_instance")):
            sites.append(
                (
                    ["finish_setup", "mounting_solution", "configuration", "acm_panel_instance"],
                    cfg["acm_panel_instance"],
                )
            )
    return sites


async def upload_and_optionally_bind_production_dxf(
    db: AsyncSession,
    workspace_id: str,
    *,
    raw_bytes: bytes,
    filename: str,
    content_type: str | None,
    component_instance_id: str,
    panel_id: str | None,
    geometry_role: str,
    bind: bool,
    uploaded_by: str | None,
    current_user: Any,
) -> dict[str, Any]:
    """Upload DXF under V6 workspace storage; optionally bind to AcmPanel instance.

    Writes: always writes disk file; binds instance JSON only when bind=True.
    """
    from services.intake_v6_workspace_service import (
        _get_record_or_404,
        _json_loads,
        _parse_payload,
        _persist_payload,
        _reset_internal_draft_quote_confirmation,
    )

    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is not None:
        raise HTTPException(status_code=400, detail={"error": "workspace_archived"})

    role = (geometry_role or "").strip() or GEOMETRY_ROLE_PRODUCTION
    if role not in ELIGIBLE_GEOMETRY_ROLES and role not in {
        "reference_only",
        "customer_artwork",
        "unknown",
        "production_blank",
    }:
        raise HTTPException(status_code=400, detail={"error": "invalid_geometry_role", "role": role})

    try:
        stored_name = sanitize_dxf_filename(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": "invalid_filename", "detail": str(exc)}) from exc

    validation = validate_dxf_bytes(raw_bytes, filename=stored_name)
    if validation["outcome"] != "accepted":
        raise HTTPException(
            status_code=400,
            detail={"error": "dxf_rejected", "code": validation.get("code"), "detail": validation.get("detail")},
        )

    checksum = _sha256(raw_bytes)
    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}

    sites = _find_instance_sites(payload_raw, component_instance_id)
    if not sites:
        raise HTTPException(
            status_code=404,
            detail={"error": "component_instance_not_found", "component_instance_id": component_instance_id},
        )

    primary_inst = sites[0][1]
    fingerprint = compute_config_fingerprint(payload=payload_raw, acm_instance=primary_inst)
    bundle = get_production_geometry_bundle(primary_inst)

    # Duplicate checksum for same instance/panel → reuse
    panel_key = (panel_id or "").strip() or None
    for existing in list_active_attachments(bundle):
        if (
            str(existing.get("checksum") or "") == checksum
            and (str(existing.get("panel_id") or "") or None) == panel_key
            and str(existing.get("geometry_role") or "") == role
            and str(existing.get("config_fingerprint") or "") == fingerprint
            and str(existing.get("semantic_mapping_version") or "") == ACM_ACI_SEMANTIC_MAPPING_VERSION
            and str(existing.get("measurement_version") or "") == MEASUREMENT_SERVICE_VERSION
            and str(existing.get("measurement_status") or "") in CONSUMABLE_MEASUREMENT_STATUSES
        ):
            return {
                "ok": True,
                "duplicate": True,
                "bound": False,
                "attachment": existing,
                "measurement_preview": existing.get("metrics_snapshot"),
                "workspace_id": record.id,
            }

    attachment_id = uuid.uuid4().hex
    disk_name = f"{attachment_id}_{stored_name}"
    storage_dir = _storage_dir(record.id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    disk_path = storage_dir / disk_name
    disk_path.write_bytes(raw_bytes)
    logger.info("Stored AcmPanel production DXF at %s", disk_path)

    measured = measure_and_guard_dxf(disk_path)
    m_status = str(measured.get("measurement_status") or "invalid")
    if role not in ELIGIBLE_GEOMETRY_ROLES:
        m_status = "uploaded"
        measured = {
            **measured,
            "measurement_status": m_status,
            "warnings": list(measured.get("warnings") or []) + ["geometry_role_not_eligible_for_cut_v"],
            "cut_length_ml": None,
            "v_groove_l1_ml": None,
            "v_groove_l2_ml": None,
            "v_groove_total_ml": None,
        }

    construction = _construction_from_instance(primary_inst)
    # Panel dims for snapshot
    from services.acm_assembly_extent import read_panels_for_assembly_extent

    finish = payload_raw.get("finish_setup") if isinstance(payload_raw.get("finish_setup"), dict) else {}
    panels_raw, _, _, _ = read_panels_for_assembly_extent(finish, primary_inst)
    pw = ph = None
    if panel_key:
        for p in panels_raw or []:
            if isinstance(p, Mapping) and str(p.get("panel_id") or "") == panel_key:
                pw, ph = _num(p.get("width_mm")), _num(p.get("height_mm"))
                break
    if pw is None:
        geom = primary_inst.get("geometry") if isinstance(primary_inst.get("geometry"), Mapping) else {}
        pw = _num(geom.get("width_mm")) if geom else None
        ph = _num(geom.get("height_mm")) if geom else None

    metrics_snapshot = None
    if m_status in CONSUMABLE_MEASUREMENT_STATUSES and role in ELIGIBLE_GEOMETRY_ROLES:
        metrics_snapshot = build_panel_metrics_from_measured(
            measured,
            panel_id=panel_key or "dxf_import",
            active_width_mm=pw,
            active_height_mm=ph,
            l1_mm=construction.get("l1_mm"),
            l2_mm=construction.get("l2_mm"),
            construction_type=str(construction.get("construction_type") or "unknown"),
        )
        metrics_snapshot["measurement_status"] = m_status

    attachment: dict[str, Any] = {
        "schema": PRODUCTION_GEOMETRY_ATTACHMENT_SCHEMA,
        "attachment_id": attachment_id,
        "workspace_id": record.id,
        "component_instance_id": component_instance_id.strip(),
        "panel_id": panel_key,
        "filename": stored_name,
        "original_filename": (filename or stored_name).strip() or stored_name,
        "mime_type": (content_type or "").strip() or "application/dxf",
        "size_bytes": len(raw_bytes),
        "checksum": checksum,
        "storage_reference": disk_name,
        "geometry_role": role,
        "upload_source": "operator_upload",
        "uploaded_at": _utcnow_iso(),
        "uploaded_by": uploaded_by or getattr(current_user, "email", None) or str(getattr(current_user, "id", "")),
        "semantic_mapping_version": ACM_ACI_SEMANTIC_MAPPING_VERSION,
        "measurement_version": MEASUREMENT_SERVICE_VERSION,
        "measurement_status": m_status if m_status != "rejected" else "invalid",
        "config_fingerprint": fingerprint,
        "warnings": list(measured.get("warnings") or []),
        "metrics_snapshot": metrics_snapshot,
        "download_path": (
            f"/api/v1/intake-v6/workspaces/{record.id}/acm-panel/production-geometry/"
            f"{attachment_id}/download"
        ),
    }

    if not bind:
        return {
            "ok": True,
            "duplicate": False,
            "bound": False,
            "attachment": attachment,
            "measurement_preview": {
                "measurement_status": attachment["measurement_status"],
                "cut_length_ml": measured.get("cut_length_ml"),
                "v_groove_l1_ml": measured.get("v_groove_l1_ml"),
                "v_groove_l2_ml": measured.get("v_groove_l2_ml"),
                "v_groove_total_ml": measured.get("v_groove_total_ml"),
                "warnings": measured.get("warnings"),
                "semantic_mapping_version": ACM_ACI_SEMANTIC_MAPPING_VERSION,
                "config_fingerprint": fingerprint,
            },
            "workspace_id": record.id,
            "note": "File stored; instance not bound (bind=false). Call again with bind=true or bind endpoint.",
        }

    # Bind: archive prior active for same panel/role
    new_attachments: list[dict[str, Any]] = []
    for a in bundle.get("attachments") or []:
        row = dict(a)
        same_panel = (str(row.get("panel_id") or "") or None) == panel_key
        same_role = str(row.get("geometry_role") or "") == role
        st = str(row.get("measurement_status") or "")
        if same_panel and same_role and st not in {"replaced", "archived"}:
            row["measurement_status"] = "replaced"
            warnings = list(row.get("warnings") or [])
            warnings.append(f"replaced_by:{attachment_id}")
            row["warnings"] = warnings
        new_attachments.append(row)
    new_attachments.append(attachment)

    for _path_keys, inst in sites:
        inst["production_geometry"] = {
            "schema": PRODUCTION_GEOMETRY_BUNDLE_SCHEMA,
            "attachments": new_attachments,
        }
        inst["updated_at"] = _utcnow_iso()

    _reset_internal_draft_quote_confirmation(payload_raw)
    payload = _parse_payload(payload_raw)
    workspace = await _persist_payload(db, record, payload, current_user=current_user)

    return {
        "ok": True,
        "duplicate": False,
        "bound": True,
        "attachment": attachment,
        "measurement_preview": attachment.get("metrics_snapshot")
        or {
            "measurement_status": attachment["measurement_status"],
            "cut_length_ml": measured.get("cut_length_ml"),
            "v_groove_l1_ml": measured.get("v_groove_l1_ml"),
            "v_groove_l2_ml": measured.get("v_groove_l2_ml"),
            "v_groove_total_ml": measured.get("v_groove_total_ml"),
            "warnings": measured.get("warnings"),
        },
        "workspace": workspace.model_dump(mode="json") if hasattr(workspace, "model_dump") else None,
        "workspace_id": record.id,
    }


async def bind_existing_production_dxf(
    db: AsyncSession,
    workspace_id: str,
    *,
    attachment: Mapping[str, Any],
    current_user: Any,
) -> dict[str, Any]:
    """Bind a previously uploaded (unbound) attachment dict onto the instance."""
    return await upload_and_optionally_bind_production_dxf(
        db,
        workspace_id,
        raw_bytes=resolve_attachment_disk_path(
            str(attachment.get("workspace_id") or workspace_id),
            str(attachment.get("storage_reference") or ""),
        ).read_bytes(),
        filename=str(attachment.get("original_filename") or attachment.get("filename") or "upload.dxf"),
        content_type=str(attachment.get("mime_type") or "application/dxf"),
        component_instance_id=str(attachment.get("component_instance_id") or ""),
        panel_id=str(attachment.get("panel_id") or "") or None,
        geometry_role=str(attachment.get("geometry_role") or GEOMETRY_ROLE_PRODUCTION),
        bind=True,
        uploaded_by=str(attachment.get("uploaded_by") or None),
        current_user=current_user,
    )


async def download_production_dxf(
    db: AsyncSession,
    workspace_id: str,
    attachment_id: str,
) -> FileResponse:
    from services.intake_v6_workspace_service import _get_record_or_404, _json_loads

    record = await _get_record_or_404(db, workspace_id)
    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        raise HTTPException(status_code=404, detail={"error": "attachment_not_found"})

    finish = payload_raw.get("finish_setup") if isinstance(payload_raw.get("finish_setup"), dict) else {}
    inst = finish.get("acm_panel_instance") if isinstance(finish, dict) else None
    bundle = get_production_geometry_bundle(inst if isinstance(inst, Mapping) else None)
    match = next(
        (
            a
            for a in (bundle.get("attachments") or [])
            if isinstance(a, Mapping) and str(a.get("attachment_id") or "") == attachment_id.strip()
        ),
        None,
    )
    if match is None:
        # Also search unbound is not persisted — only bound attachments are downloadable via instance
        raise HTTPException(status_code=404, detail={"error": "attachment_not_found"})
    if str(match.get("workspace_id") or "") not in {record.id, workspace_id}:
        raise HTTPException(status_code=403, detail={"error": "workspace_isolation_violation"})

    path = resolve_attachment_disk_path(record.id, str(match.get("storage_reference") or ""))
    if not path.is_file():
        raise HTTPException(status_code=404, detail={"error": "file_missing_on_storage"})
    return FileResponse(
        path=str(path),
        filename=str(match.get("original_filename") or match.get("filename") or "geometry.dxf"),
        media_type=str(match.get("mime_type") or "application/dxf"),
    )
