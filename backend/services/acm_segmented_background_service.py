"""Normalize / validate / project ACM/ACP segmented background assemblies.

Envelope: one SUPPORT_CONTOUR (MAX_ONE) remains the logical assembly host.
Physical panels nest under shell-owned `segmented_background` config.

PROPOSED / INACTIVE / missing → zero PD/Aggregate segmented output.
CONFIRMED → assembly + panels + bindings + blockers for impossible crossings.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping

from data.product_system.acm_segmented_background_v1 import (
    APPLIED_LIKE_CONSTRUCTIONS,
    CONSTRUCTION_ACRYLIC_INSERT,
    CONSTRUCTION_APPLIED_VOLUMETRIC,
    CONSTRUCTION_CUTOUT,
    CONSTRUCTION_SIMPLE_APPLIED,
    CONTRACT_VERSION,
    CROSSING_ACRYLIC_INSERT_JOINT,
    CROSSING_APPLIED_VOLUMETRIC_JOINT,
    CROSSING_CUTOUT_JOINT,
    CROSSING_NONE,
    CUTOUT_LIKE_CONSTRUCTIONS,
    HOST_SHELL_TEMPLATE,
    MOUNT_STANDARD,
    MOUNT_TWO_STAGE_JOINT,
    MSG_APPLIED_CROSSING,
    MSG_ASSEMBLY_CONFIRMED,
    MSG_CROSSING_ON_SINGLE_PANEL,
    MSG_CUTOUT_CROSSING_BLOCKER,
    MSG_DUPLICATE_PANEL_ID,
    MSG_GRAPHIC_DISTRIBUTED,
    MSG_INSERT_CROSSING_BLOCKER,
    MSG_INVALID_PANEL_REF,
    MSG_PROPOSAL_REJECTED,
    MSG_SEGMENTATION_PROPOSAL,
    SCHEMA,
    STATUS_CONFIRMED,
    STATUS_INACTIVE,
    STATUS_PROPOSED,
    STATUS_REJECTED,
    STATUS_SINGLE_PANEL,
    contract_meta,
    operator_message,
)

_PANEL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]{0,63}$")


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def stable_assembly_id(*parts: str) -> str:
    seed = "|".join(str(p or "").strip() for p in parts if str(p or "").strip())
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
    return f"asm_{digest}"


def stable_panel_id(hint: str | None, *, index: int) -> str:
    raw = str(hint or "").strip()
    if raw and _PANEL_ID_RE.match(raw):
        return raw
    return f"panel_{index + 1}"


def _msg(code: str, *, level: str) -> dict[str, str]:
    return {
        "code": code,
        "level": level,
        "message": operator_message(code),
    }


def empty_single_panel_assembly(
    *,
    assembly_id: str | None = None,
    width_mm: float | int | None = None,
    height_mm: float | int | None = None,
    contour_element_id: str | None = None,
) -> dict[str, Any]:
    panel_id = "panel_1"
    panel: dict[str, Any] = {
        "panel_id": panel_id,
        "order": 1,
        "width_mm": width_mm,
        "height_mm": height_mm,
        "position": {"x_mm": 0, "y_mm": 0},
        "contour_element_id": contour_element_id,
    }
    return {
        "schema": SCHEMA,
        "contract_version": CONTRACT_VERSION,
        "status": STATUS_SINGLE_PANEL,
        "assembly_id": assembly_id or stable_assembly_id(panel_id, str(width_mm), str(height_mm)),
        "host_component_template_code": HOST_SHELL_TEMPLATE,
        "operator_confirmed": True,
        "graphic_continuity": True,
        "panels": [panel],
        "joints": [],
        "assembly_dimensions": {
            "width_mm": width_mm,
            "height_mm": height_mm,
        },
        "element_bindings": [],
        "detection": None,
        "validation": {"blockers": [], "warnings": [], "infos": []},
        "meta": contract_meta(),
    }


def propose_segmented_assembly(
    *,
    nearby_supports: list[Mapping[str, Any]],
    assembly_id: str | None = None,
) -> dict[str, Any]:
    """Build a PROPOSED assembly from nearby support contours. Not authority."""
    panels: list[dict[str, Any]] = []
    x_cursor = 0.0
    for i, raw in enumerate(nearby_supports):
        row = _as_dict(raw)
        width = row.get("width_mm")
        height = row.get("height_mm")
        try:
            w = float(width) if width is not None else None
        except (TypeError, ValueError):
            w = None
        try:
            h = float(height) if height is not None else None
        except (TypeError, ValueError):
            h = None
        panel_id = stable_panel_id(row.get("panel_id") or row.get("contour_element_id"), index=i)
        panels.append(
            {
                "panel_id": panel_id,
                "order": i + 1,
                "width_mm": w,
                "height_mm": h,
                "position": {
                    "x_mm": row.get("x_mm", x_cursor),
                    "y_mm": row.get("y_mm", 0),
                },
                "contour_element_id": row.get("contour_element_id"),
            }
        )
        if w is not None:
            x_cursor += w

    joints: list[dict[str, Any]] = []
    for i in range(len(panels) - 1):
        left = panels[i]["panel_id"]
        right = panels[i + 1]["panel_id"]
        joints.append(
            {
                "joint_id": f"joint_{left}_{right}",
                "left_panel_id": left,
                "right_panel_id": right,
                "orientation": "VERTICAL",
            }
        )

    total_w = None
    widths = [p["width_mm"] for p in panels if p.get("width_mm") is not None]
    if widths and len(widths) == len(panels):
        total_w = sum(float(w) for w in widths)
    heights = [p["height_mm"] for p in panels if p.get("height_mm") is not None]
    total_h = float(heights[0]) if heights and len(set(heights)) == 1 else None

    asm_id = assembly_id or stable_assembly_id(
        *[str(p.get("contour_element_id") or p["panel_id"]) for p in panels]
    )
    return {
        "schema": SCHEMA,
        "contract_version": CONTRACT_VERSION,
        "status": STATUS_PROPOSED,
        "assembly_id": asm_id,
        "host_component_template_code": HOST_SHELL_TEMPLATE,
        "operator_confirmed": False,
        "graphic_continuity": True,
        "panels": panels,
        "joints": joints,
        "assembly_dimensions": {"width_mm": total_w, "height_mm": total_h},
        "element_bindings": [],
        "detection": {
            "source": "svg_analyzer_proposal",
            "nearby_support_count": len(panels),
            "message_code": MSG_SEGMENTATION_PROPOSAL,
            "message": operator_message(MSG_SEGMENTATION_PROPOSAL),
            "authority": "PROPOSAL_ONLY",
        },
        "validation": {
            "blockers": [],
            "warnings": [],
            "infos": [_msg(MSG_SEGMENTATION_PROPOSAL, level="info")],
        },
        "meta": contract_meta(),
    }


def _normalize_panel(raw: Any, *, index: int) -> dict[str, Any]:
    row = _as_dict(raw)
    panel_id = stable_panel_id(row.get("panel_id"), index=index)
    order = row.get("order")
    try:
        order_i = int(order) if order is not None else index + 1
    except (TypeError, ValueError):
        order_i = index + 1
    pos = _as_dict(row.get("position"))
    return {
        "panel_id": panel_id,
        "order": order_i,
        "width_mm": row.get("width_mm"),
        "height_mm": row.get("height_mm"),
        "position": {
            "x_mm": pos.get("x_mm", row.get("x_mm", 0)),
            "y_mm": pos.get("y_mm", row.get("y_mm", 0)),
        },
        "contour_element_id": row.get("contour_element_id"),
    }


def _normalize_joint(raw: Any, *, index: int) -> dict[str, Any]:
    row = _as_dict(raw)
    left = str(row.get("left_panel_id") or "").strip()
    right = str(row.get("right_panel_id") or "").strip()
    joint_id = str(row.get("joint_id") or "").strip() or f"joint_{index + 1}"
    return {
        "joint_id": joint_id,
        "left_panel_id": left,
        "right_panel_id": right,
        "orientation": str(row.get("orientation") or "VERTICAL").upper(),
    }


def _classify_crossing(
    *,
    construction_type: str,
    crosses_joint: bool,
) -> tuple[str, str]:
    """Return (crossing_classification, mount_strategy)."""
    if not crosses_joint:
        return CROSSING_NONE, MOUNT_STANDARD
    if construction_type == CONSTRUCTION_APPLIED_VOLUMETRIC:
        return CROSSING_APPLIED_VOLUMETRIC_JOINT, MOUNT_TWO_STAGE_JOINT
    if construction_type == CONSTRUCTION_SIMPLE_APPLIED:
        return CROSSING_APPLIED_VOLUMETRIC_JOINT, MOUNT_TWO_STAGE_JOINT
    if construction_type == CONSTRUCTION_CUTOUT:
        return CROSSING_CUTOUT_JOINT, MOUNT_STANDARD
    if construction_type == CONSTRUCTION_ACRYLIC_INSERT:
        return CROSSING_ACRYLIC_INSERT_JOINT, MOUNT_STANDARD
    return CROSSING_NONE, MOUNT_STANDARD


def _normalize_element_binding(raw: Any, *, index: int) -> dict[str, Any]:
    row = _as_dict(raw)
    construction = str(row.get("construction_type") or "").strip().upper()
    if construction not in {
        CONSTRUCTION_APPLIED_VOLUMETRIC,
        CONSTRUCTION_SIMPLE_APPLIED,
        CONSTRUCTION_CUTOUT,
        CONSTRUCTION_ACRYLIC_INSERT,
    }:
        construction = CONSTRUCTION_APPLIED_VOLUMETRIC

    crosses = bool(row.get("crosses_joint"))
    classification, default_mount = _classify_crossing(
        construction_type=construction,
        crosses_joint=crosses,
    )
    mount = str(row.get("mount_strategy") or default_mount).strip().upper()
    if crosses and construction in APPLIED_LIKE_CONSTRUCTIONS:
        mount = MOUNT_TWO_STAGE_JOINT
    elif not crosses:
        mount = MOUNT_STANDARD

    primary = str(row.get("primary_panel_id") or "").strip() or None
    secondary = str(row.get("secondary_panel_id") or "").strip() or None
    if not crosses:
        secondary = None

    binding_id = str(row.get("binding_id") or "").strip() or f"eb_{index + 1}"
    return {
        "binding_id": binding_id,
        "element_ref": row.get("element_ref"),
        "construction_type": construction,
        "primary_panel_id": primary,
        "secondary_panel_id": secondary,
        "crosses_joint": crosses,
        "joint_id": row.get("joint_id") if crosses else None,
        "crossing_classification": classification,
        "mount_strategy": mount,
        "panel_alignment_dependency": bool(crosses and construction in APPLIED_LIKE_CONSTRUCTIONS),
        "cable_passage_context": bool(row.get("cable_passage_context", crosses)),
        # Letters remain external — interface context only
        "applied_component_template_code": row.get("applied_component_template_code"),
        "does_not_absorb_letter_ownership": True,
    }


def validate_segmented_background(config: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return validation payload; does not mutate status."""
    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    infos: list[dict[str, str]] = []

    if not isinstance(config, Mapping):
        return {"blockers": blockers, "warnings": warnings, "infos": infos}

    status = str(config.get("status") or "").strip().upper()
    panels = [p for p in _as_list(config.get("panels")) if isinstance(p, Mapping)]
    panel_ids = [str(p.get("panel_id") or "") for p in panels]
    panel_id_set = {pid for pid in panel_ids if pid}

    if len(panel_ids) != len(panel_id_set):
        blockers.append(_msg(MSG_DUPLICATE_PANEL_ID, level="blocker"))

    for p in panels:
        pid = str(p.get("panel_id") or "")
        if not pid or not _PANEL_ID_RE.match(pid):
            blockers.append(_msg(MSG_INVALID_PANEL_REF, level="blocker"))
            break

    bindings = [b for b in _as_list(config.get("element_bindings")) if isinstance(b, Mapping)]
    panels_used: set[str] = set()
    for b in bindings:
        primary = str(b.get("primary_panel_id") or "").strip()
        secondary = str(b.get("secondary_panel_id") or "").strip() or None
        crosses = bool(b.get("crosses_joint"))
        construction = str(b.get("construction_type") or "")

        if primary:
            panels_used.add(primary)
        if secondary:
            panels_used.add(secondary)

        if primary and primary not in panel_id_set:
            blockers.append(_msg(MSG_INVALID_PANEL_REF, level="blocker"))
        if secondary and secondary not in panel_id_set:
            blockers.append(_msg(MSG_INVALID_PANEL_REF, level="blocker"))

        if crosses and len(panel_id_set) < 2:
            blockers.append(_msg(MSG_CROSSING_ON_SINGLE_PANEL, level="blocker"))
            continue

        if crosses and construction in CUTOUT_LIKE_CONSTRUCTIONS:
            code = (
                MSG_INSERT_CROSSING_BLOCKER
                if construction == CONSTRUCTION_ACRYLIC_INSERT
                else MSG_CUTOUT_CROSSING_BLOCKER
            )
            blockers.append(_msg(code, level="blocker"))
        elif crosses and construction in APPLIED_LIKE_CONSTRUCTIONS:
            if not primary or not secondary or primary == secondary:
                blockers.append(_msg(MSG_INVALID_PANEL_REF, level="blocker"))
            else:
                infos.append(_msg(MSG_APPLIED_CROSSING, level="info"))

    if status == STATUS_CONFIRMED and len(panel_id_set) >= 2 and len(panels_used) >= 2:
        # Graphic distributed across panels without requiring every element to cross.
        infos.append(_msg(MSG_GRAPHIC_DISTRIBUTED, level="info"))
    elif status == STATUS_PROPOSED:
        infos.append(_msg(MSG_SEGMENTATION_PROPOSAL, level="info"))

    # Deduplicate by code+level
    def _dedupe(rows: list[dict[str, str]]) -> list[dict[str, str]]:
        seen: set[tuple[str, str]] = set()
        out: list[dict[str, str]] = []
        for r in rows:
            key = (r.get("code") or "", r.get("level") or "")
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
        return out

    return {
        "blockers": _dedupe(blockers),
        "warnings": _dedupe(warnings),
        "infos": _dedupe(infos),
    }


def normalize_segmented_background(
    raw: Any,
    *,
    default_status: str | None = None,
) -> dict[str, Any] | None:
    """Normalize operator/finish payload. Returns None when absent."""
    if raw is None:
        return None
    incoming = _as_dict(raw)
    if not incoming:
        return None

    status = str(incoming.get("status") or default_status or STATUS_SINGLE_PANEL).strip().upper()
    if status not in {
        STATUS_SINGLE_PANEL,
        STATUS_PROPOSED,
        STATUS_CONFIRMED,
        STATUS_REJECTED,
        STATUS_INACTIVE,
    }:
        status = STATUS_PROPOSED

    panels_raw = _as_list(incoming.get("panels"))
    panels = [_normalize_panel(p, index=i) for i, p in enumerate(panels_raw)]
    joints = [_normalize_joint(j, index=i) for i, j in enumerate(_as_list(incoming.get("joints")))]
    bindings = [
        _normalize_element_binding(b, index=i)
        for i, b in enumerate(_as_list(incoming.get("element_bindings")))
    ]

    # Single panel incorrectly marked as crossing → clear crossing (normalize, not silent accept)
    if len(panels) < 2:
        for b in bindings:
            if b.get("crosses_joint"):
                b["crosses_joint"] = False
                b["secondary_panel_id"] = None
                b["joint_id"] = None
                b["crossing_classification"] = CROSSING_NONE
                b["mount_strategy"] = MOUNT_STANDARD
                b["panel_alignment_dependency"] = False

    dims = _as_dict(incoming.get("assembly_dimensions"))
    detection = incoming.get("detection")
    if detection is not None and not isinstance(detection, Mapping):
        detection = None
    elif isinstance(detection, Mapping):
        detection = dict(detection)
        detection["authority"] = "PROPOSAL_ONLY"

    assembly_id = str(incoming.get("assembly_id") or "").strip()
    if not assembly_id:
        assembly_id = stable_assembly_id(
            *[str(p.get("panel_id")) for p in panels],
            status,
        )

    base: dict[str, Any] = {
        "schema": SCHEMA,
        "contract_version": CONTRACT_VERSION,
        "status": status,
        "assembly_id": assembly_id,
        "host_component_template_code": HOST_SHELL_TEMPLATE,
        "operator_confirmed": bool(
            incoming.get("operator_confirmed", status == STATUS_CONFIRMED)
        ),
        "graphic_continuity": bool(incoming.get("graphic_continuity", True)),
        "panels": panels,
        "joints": joints,
        "assembly_dimensions": {
            "width_mm": dims.get("width_mm", incoming.get("width_mm")),
            "height_mm": dims.get("height_mm", incoming.get("height_mm")),
        },
        "element_bindings": bindings,
        "detection": detection,
        "meta": contract_meta(),
    }

    if status == STATUS_CONFIRMED:
        base["operator_confirmed"] = True
    if status in {STATUS_PROPOSED, STATUS_INACTIVE, STATUS_REJECTED}:
        base["operator_confirmed"] = False

    # Shell-owned electrical context — only meaningful on confirmed multi-panel assemblies.
    from services.acm_segmented_electrical_service import (
        normalize_electrical_connection_management,
    )

    panel_ids = {str(p.get("panel_id") or "") for p in panels if p.get("panel_id")}
    if status == STATUS_CONFIRMED and len(panel_ids) >= 2:
        electrical = normalize_electrical_connection_management(
            incoming.get("electrical_connection_management"),
            assembly_panel_ids=panel_ids,
        )
        if electrical is not None:
            base["electrical_connection_management"] = electrical
    elif "electrical_connection_management" in incoming and status == STATUS_CONFIRMED:
        # Single-panel confirmed should not carry segmented electrical truth.
        pass

    base["validation"] = validate_segmented_background(base)
    return base


def confirmation_blockers(config: Mapping[str, Any] | None) -> list[dict[str, str]]:
    """Blockers that prevent operator confirmation (cutout/insert, invalid refs, etc.)."""
    normalized = normalize_segmented_background(config)
    if normalized is None:
        return [_msg(MSG_INVALID_PANEL_REF, level="blocker")]
    panels = [p for p in _as_list(normalized.get("panels")) if isinstance(p, Mapping)]
    blockers = list((normalized.get("validation") or {}).get("blockers") or [])
    if len(panels) < 2:
        blockers.append(
            {
                "code": "SEGMENTATION_REQUIRES_TWO_PANELS",
                "level": "blocker",
                "message": "Un ansamblu segmentat necesita cel putin doua panouri.",
            }
        )
    for p in panels:
        w = p.get("width_mm")
        h = p.get("height_mm")
        try:
            wf = float(w) if w is not None else 0.0
            hf = float(h) if h is not None else 0.0
        except (TypeError, ValueError):
            wf, hf = 0.0, 0.0
        if wf <= 0 or hf <= 0:
            blockers.append(
                {
                    "code": "INVALID_PANEL_DIMENSIONS",
                    "level": "blocker",
                    "message": "Dimensiunile panoului sunt invalide.",
                }
            )
            break
    # Deduplicate
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for b in blockers:
        code = str(b.get("code") or "")
        if code in seen:
            continue
        seen.add(code)
        out.append(b)
    return out


def confirm_segmented_background(raw: Any) -> dict[str, Any]:
    """Explicit operator confirmation. Raises ValueError if confirmation blockers exist."""
    normalized = normalize_segmented_background(raw)
    if normalized is None:
        raise ValueError("segmented_background_missing")
    blockers = confirmation_blockers(normalized)
    if blockers:
        raise ValueError(
            {
                "error": "segmented_background_confirmation_blocked",
                "blockers": blockers,
            }
        )
    normalized["status"] = STATUS_CONFIRMED
    normalized["operator_confirmed"] = True
    normalized["confirmation"] = {
        "message_code": MSG_ASSEMBLY_CONFIRMED,
        "message": operator_message(MSG_ASSEMBLY_CONFIRMED),
        "authority": "OPERATOR",
    }
    normalized["validation"] = validate_segmented_background(normalized)
    return normalized


def reject_segmented_background(raw: Any = None) -> dict[str, Any]:
    """Operator reject — clear confirmed authority; zero downstream effects."""
    normalized = normalize_segmented_background(raw) or {
        "schema": SCHEMA,
        "contract_version": CONTRACT_VERSION,
        "panels": [],
        "joints": [],
        "element_bindings": [],
        "assembly_dimensions": {},
        "meta": contract_meta(),
    }
    normalized["status"] = STATUS_REJECTED
    normalized["operator_confirmed"] = False
    normalized["confirmation"] = {
        "message_code": MSG_PROPOSAL_REJECTED,
        "message": operator_message(MSG_PROPOSAL_REJECTED),
        "authority": "OPERATOR",
    }
    normalized["validation"] = {
        "blockers": [],
        "warnings": [],
        "infos": [_msg(MSG_PROPOSAL_REJECTED, level="info")],
    }
    return normalized


def coalesce_segmented_background_for_finish(
    incoming_finish: Mapping[str, Any] | None,
    existing_finish: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Keep PROPOSED/CONFIRMED/REJECTED when a sparse finish patch omits the field.

    Letter/logo binding sync may PUT finish_setup without segmented_background; that
    must not wipe a live operator proposal.
    """
    finish_d = dict(incoming_finish or {})
    if finish_d.get("segmented_background") is not None:
        return finish_d
    existing = _as_dict(existing_finish)
    existing_seg = existing.get("segmented_background")
    if not isinstance(existing_seg, Mapping):
        return finish_d
    existing_status = str(existing_seg.get("status") or "").strip().upper()
    if existing_status in {STATUS_PROPOSED, STATUS_CONFIRMED, STATUS_REJECTED}:
        finish_d["segmented_background"] = dict(existing_seg)
    return finish_d


def persist_segmented_background_on_finish(finish: Mapping[str, Any] | None) -> dict[str, Any]:
    """Normalize finish_setup.segmented_background; block illegal CONFIRMED writes.

    Returns updated finish dict. Raises ValueError with structured detail when
    status=CONFIRMED but confirmation blockers remain.
    """
    finish_d = dict(finish or {})
    raw = finish_d.get("segmented_background")
    if raw is None:
        return finish_d
    normalized = normalize_segmented_background(raw)
    if normalized is None:
        finish_d["segmented_background"] = None
        return finish_d
    status = str(normalized.get("status") or "").upper()
    if status == STATUS_CONFIRMED:
        # Re-run confirm gates — never silently accept impossible crossings.
        blockers = confirmation_blockers(normalized)
        if blockers:
            raise ValueError(
                {
                    "error": "segmented_background_confirmation_blocked",
                    "blockers": blockers,
                }
            )
        normalized["operator_confirmed"] = True
        normalized["confirmation"] = {
            "message_code": MSG_ASSEMBLY_CONFIRMED,
            "message": operator_message(MSG_ASSEMBLY_CONFIRMED),
            "authority": "OPERATOR",
        }
        # Electrical confirm is independent — block only when electrical itself is CONFIRMED
        # with contradictions (does not require electrical for assembly confirm).
        from services.acm_segmented_electrical_service import electrical_confirmation_blockers

        electrical = normalized.get("electrical_connection_management")
        if isinstance(electrical, Mapping) and str(electrical.get("status") or "").upper() == "CONFIRMED":
            panel_ids = {
                str(p.get("panel_id") or "")
                for p in _as_list(normalized.get("panels"))
                if p.get("panel_id")
            }
            elec_blockers = electrical_confirmation_blockers(
                electrical, assembly_panel_ids=panel_ids
            )
            if elec_blockers:
                raise ValueError(
                    {
                        "error": "segmented_electrical_confirmation_blocked",
                        "blockers": elec_blockers,
                    }
                )
    elif status in {STATUS_PROPOSED, STATUS_REJECTED, STATUS_INACTIVE, STATUS_SINGLE_PANEL}:
        normalized["operator_confirmed"] = False
        normalized.pop("electrical_connection_management", None)
    finish_d["segmented_background"] = normalized
    return finish_d


def read_segmented_background_from_finish(finish: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Prefer finish_setup.segmented_background; fallback mounting_solution.configuration."""
    finish_d = _as_dict(finish)
    direct = finish_d.get("segmented_background")
    normalized = normalize_segmented_background(direct)
    if normalized is not None:
        return normalized
    mounting = _as_dict(finish_d.get("mounting_solution"))
    cfg = _as_dict(mounting.get("configuration"))
    return normalize_segmented_background(cfg.get("segmented_background"))


def project_segmented_background_for_product_definition(
    config: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """PD truth: CONFIRMED assembly only. PROPOSED/INACTIVE → None (zero leakage)."""
    if not isinstance(config, Mapping):
        return None
    status = str(config.get("status") or "").strip().upper()
    if status != STATUS_CONFIRMED:
        return None
    if not bool(config.get("operator_confirmed")):
        return None

    validation = validate_segmented_background(config)
    panels = sorted(
        [dict(p) for p in _as_list(config.get("panels")) if isinstance(p, Mapping)],
        key=lambda p: int(p.get("order") or 0),
    )
    from services.acm_segmented_electrical_service import (
        project_electrical_draft_non_authoritative,
        project_electrical_for_product_definition,
    )

    electrical_raw = config.get("electrical_connection_management")
    electrical_confirmed = project_electrical_for_product_definition(
        electrical_raw, assembly_confirmed=True
    )
    electrical_draft = project_electrical_draft_non_authoritative(
        electrical_raw, assembly_confirmed=True
    )
    out: dict[str, Any] = {
        "schema": SCHEMA,
        "contract_version": CONTRACT_VERSION,
        "status": STATUS_CONFIRMED,
        "assembly_id": config.get("assembly_id"),
        "host_component_template_code": HOST_SHELL_TEMPLATE,
        "operator_confirmed": True,
        "graphic_continuity": bool(config.get("graphic_continuity", True)),
        "panels": panels,
        "joints": [dict(j) for j in _as_list(config.get("joints")) if isinstance(j, Mapping)],
        "assembly_dimensions": dict(_as_dict(config.get("assembly_dimensions"))),
        "element_bindings": [
            dict(b) for b in _as_list(config.get("element_bindings")) if isinstance(b, Mapping)
        ],
        "validation": validation,
        "meta": contract_meta(),
        # Explicit non-effects for this build
        "task_materialization": False,
        "pricing": False,
    }
    if electrical_confirmed is not None:
        out["electrical_connection_management"] = electrical_confirmed
    elif electrical_draft is not None:
        out["electrical_connection_management_draft"] = electrical_draft
    return out


def project_segmented_background_for_aggregate(
    config: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Guarded Aggregate projection — confirmed technical truth only, no materials/tasks."""
    pd = project_segmented_background_for_product_definition(config)
    if pd is None:
        return None

    validation = pd.get("validation") or {}
    blockers = list(validation.get("blockers") or [])
    infos = list(validation.get("infos") or [])

    allowed_crossings: list[dict[str, Any]] = []
    for b in pd.get("element_bindings") or []:
        if not isinstance(b, Mapping):
            continue
        if b.get("crossing_classification") == CROSSING_APPLIED_VOLUMETRIC_JOINT:
            allowed_crossings.append(
                {
                    "binding_id": b.get("binding_id"),
                    "element_ref": b.get("element_ref"),
                    "primary_panel_id": b.get("primary_panel_id"),
                    "secondary_panel_id": b.get("secondary_panel_id"),
                    "mount_strategy": b.get("mount_strategy"),
                    "panel_alignment_dependency": b.get("panel_alignment_dependency"),
                }
            )

    future_intent: list[str] = []
    if len(pd.get("panels") or []) >= 2:
        future_intent.append("panel_alignment_required")
    if allowed_crossings:
        future_intent.append("two_stage_applied_letter_mounting")
    if blockers:
        future_intent.append("cutout_or_insert_crossing_blocked")

    from services.acm_segmented_electrical_service import project_electrical_for_aggregate

    electrical_agg = project_electrical_for_aggregate(
        config.get("electrical_connection_management") if isinstance(config, Mapping) else None,
        assembly_confirmed=True,
    )
    if electrical_agg:
        for intent in electrical_agg.get("future_task_intent") or []:
            if intent not in future_intent:
                future_intent.append(intent)

    out_agg: dict[str, Any] = {
        "kind": "acm_segmented_background",
        "contract_version": CONTRACT_VERSION,
        "assembly_id": pd.get("assembly_id"),
        "status": STATUS_CONFIRMED,
        "panels": pd.get("panels"),
        "joints": pd.get("joints"),
        "assembly_dimensions": pd.get("assembly_dimensions"),
        "element_bindings": pd.get("element_bindings"),
        "allowed_applied_crossings": allowed_crossings,
        "blockers": blockers,
        "infos": infos,
        "future_task_intent": future_intent,
        "future_task_intent_authority": "INFORMATIONAL_ONLY",
        "task_contract_authority": "task_contract.task_rules — not this projection",
        "quantity_status": "GUARDED",
        "materials": [],
        "processes": [],
        "task_rules": [],
        "execution_effects": [],
        "notes": [
            "Confirmed assembly only — no pricing, no Execution materialization.",
            "Volumetric letters remain external components; interface binding only.",
            "future_task_intent is contractual/informational — not a parallel task source.",
        ],
    }
    if electrical_agg is not None:
        out_agg["electrical_connection_management"] = electrical_agg
    return out_agg


def apply_segmented_panel_context_to_applied_interface(
    interface: Mapping[str, Any] | None,
    *,
    element_binding: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Merge panel/joint context into applied interface without absorbing letter ownership."""
    if not isinstance(interface, Mapping):
        return None
    out = dict(interface)
    if not isinstance(element_binding, Mapping):
        return out
    out["primary_panel_id"] = element_binding.get("primary_panel_id")
    out["secondary_panel_id"] = element_binding.get("secondary_panel_id")
    out["crosses_joint"] = bool(element_binding.get("crosses_joint"))
    out["joint_id"] = element_binding.get("joint_id")
    out["mount_strategy"] = element_binding.get("mount_strategy")
    out["panel_alignment_dependency"] = bool(element_binding.get("panel_alignment_dependency"))
    out["cable_passage_context"] = bool(element_binding.get("cable_passage_context"))
    out["does_not_absorb_letter_ownership"] = True
    return out
