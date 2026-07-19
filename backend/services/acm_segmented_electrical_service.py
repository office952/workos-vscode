"""Normalize / validate / project segmented assembly electrical connection management.

Nested under segmented_background.electrical_connection_management.
CONFIRMED electrical → PD/Aggregate; DRAFT/UNCONFIRMED → non-authoritative only.
"""

from __future__ import annotations

from typing import Any, Mapping

from data.product_system.acm_segmented_electrical_connection_v1 import (
    CONN_INTERCONNECT,
    CONN_LV_FEED,
    CONN_OTHER,
    ELEC_STATUS_CONFIRMED,
    ELEC_STATUS_DRAFT,
    ELEC_STATUS_INACTIVE,
    ELECTRICAL_CONTRACT_VERSION,
    ELECTRICAL_SCHEMA,
    MSG_ELEC_AFTER_ALIGNMENT,
    MSG_ELEC_CONFIRMED,
    MSG_ELEC_CONTRADICTION,
    MSG_ELEC_CUSTOM_NOTE,
    MSG_ELEC_INDICATE_220V,
    MSG_ELEC_INVALID_CONNECTION,
    MSG_ELEC_INVALID_PANEL,
    MSG_ELEC_INVALID_SHARED,
    MSG_ELEC_RESERVE,
    MSG_ELEC_ROUTE_CABLES,
    MSG_ELEC_SELF_SHARED,
    MSG_ELEC_SHARED_FROM_PANEL,
    MSG_ELEC_UNCONFIRMED,
    POSITION_CUSTOM,
    POSITION_NONE,
    SERVICE_POSITIONS,
    SUPPLY_DIRECT,
    SUPPLY_MODES,
    SUPPLY_NONE,
    SUPPLY_SHARED,
    SUPPLY_UNCONFIRMED,
    electrical_meta,
    operator_message,
)


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _msg(code: str, *, level: str) -> dict[str, str]:
    return {"code": code, "level": level, "message": operator_message(code)}


def _norm_position(raw: Any) -> str | None:
    value = str(raw or "").strip().upper()
    if not value:
        return None
    if value not in SERVICE_POSITIONS:
        return None
    return value


def _normalize_workshop(raw: Any) -> dict[str, Any]:
    row = _as_dict(raw)
    return {
        "cables_routed_toward_service": bool(row.get("cables_routed_toward_service")),
        "passages_prepared": bool(row.get("passages_prepared")),
        "labeled": bool(row.get("labeled")),
        "reserve_required": bool(row.get("reserve_required")),
        "reserve_note_ro": str(row.get("reserve_note_ro") or "").strip() or None,
    }


def _normalize_installation(raw: Any) -> dict[str, Any]:
    row = _as_dict(raw)
    return {
        "connect_to_client_220v": bool(row.get("connect_to_client_220v")),
        "finalize_after_alignment": bool(row.get("finalize_after_alignment")),
        "notes_ro": str(row.get("notes_ro") or "").strip() or None,
    }


def _normalize_panel_electrical(raw: Any, *, known_panel_ids: set[str]) -> dict[str, Any] | None:
    row = _as_dict(raw)
    panel_id = str(row.get("panel_id") or "").strip()
    if not panel_id:
        return None
    supply = str(row.get("supply_mode") or SUPPLY_UNCONFIRMED).strip().upper()
    if supply not in SUPPLY_MODES:
        supply = SUPPLY_UNCONFIRMED

    shared_from = str(row.get("shared_from_panel_id") or "").strip() or None
    if supply != SUPPLY_SHARED:
        shared_from = None

    position = _norm_position(row.get("service_point_position"))
    if supply == SUPPLY_DIRECT and position is None:
        position = None  # unresolved position while mode is direct → warning
    if supply in {SUPPLY_NONE, SUPPLY_SHARED}:
        if position is None:
            position = POSITION_NONE
    if supply == SUPPLY_UNCONFIRMED:
        position = position  # keep if operator set, else None

    cable_exit = _norm_position(row.get("cable_exit_position"))
    custom_note = str(row.get("custom_position_note") or "").strip() or None
    sketch_ref = str(row.get("sketch_ref") or "").strip() or None

    return {
        "panel_id": panel_id,
        "supply_mode": supply,
        "shared_from_panel_id": shared_from,
        "service_point_position": position,
        "custom_position_note": custom_note,
        "sketch_ref": sketch_ref,
        "cable_exit_position": cable_exit,
        "routing_direction_note_ro": str(row.get("routing_direction_note_ro") or "").strip() or None,
        "power_supply_group_id": str(row.get("power_supply_group_id") or "").strip() or None,
        "letter_group_ref": str(row.get("letter_group_ref") or "").strip() or None,
        "workshop_prep": _normalize_workshop(row.get("workshop_prep")),
        "installation": _normalize_installation(row.get("installation")),
        "notes_ro": str(row.get("notes_ro") or "").strip() or None,
        "_known": panel_id in known_panel_ids,
    }


def _normalize_connection(raw: Any, *, index: int) -> dict[str, Any] | None:
    row = _as_dict(raw)
    source = str(row.get("source_panel_id") or "").strip()
    dest = str(row.get("destination_panel_id") or "").strip()
    if not source or not dest:
        return None
    conn_type = str(row.get("connection_type") or CONN_LV_FEED).strip().upper()
    if conn_type not in {CONN_LV_FEED, CONN_INTERCONNECT, CONN_OTHER}:
        conn_type = CONN_LV_FEED
    length = row.get("estimated_length_m")
    try:
        length_f = float(length) if length is not None and length != "" else None
    except (TypeError, ValueError):
        length_f = None
    return {
        "connection_id": str(row.get("connection_id") or "").strip() or f"ec_{index + 1}",
        "source_panel_id": source,
        "destination_panel_id": dest,
        "connection_type": conn_type,
        "routing_direction_note_ro": str(row.get("routing_direction_note_ro") or "").strip() or None,
        "alignment_dependent": bool(row.get("alignment_dependent", True)),
        "prepared_in_workshop": bool(row.get("prepared_in_workshop")),
        "completed_on_site": bool(row.get("completed_on_site")),
        "reserve_required": bool(row.get("reserve_required", True)),
        "estimated_length_m": length_f,
        "length_is_estimate": True if length_f is not None else bool(row.get("length_is_estimate")),
        "sketch_ref": str(row.get("sketch_ref") or "").strip() or None,
        "notes_ro": str(row.get("notes_ro") or "").strip() or None,
    }


def validate_electrical_connection_management(
    electrical: Mapping[str, Any] | None,
    *,
    assembly_panel_ids: set[str],
) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    infos: list[dict[str, str]] = []

    if not isinstance(electrical, Mapping):
        return {"blockers": blockers, "warnings": warnings, "infos": infos}

    status = str(electrical.get("status") or ELEC_STATUS_DRAFT).strip().upper()
    panels = [p for p in _as_list(electrical.get("panels")) if isinstance(p, Mapping)]

    for panel in panels:
        pid = str(panel.get("panel_id") or "")
        if pid not in assembly_panel_ids:
            blockers.append(_msg(MSG_ELEC_INVALID_PANEL, level="blocker"))
            continue
        supply = str(panel.get("supply_mode") or SUPPLY_UNCONFIRMED).upper()
        if supply == SUPPLY_UNCONFIRMED:
            warnings.append(_msg(MSG_ELEC_UNCONFIRMED, level="warning"))
            infos.append(_msg(MSG_ELEC_INDICATE_220V, level="info"))
        elif supply == SUPPLY_DIRECT:
            pos = panel.get("service_point_position")
            if not pos or pos == POSITION_NONE:
                warnings.append(_msg(MSG_ELEC_UNCONFIRMED, level="warning"))
            elif pos == POSITION_CUSTOM:
                note = panel.get("custom_position_note") or panel.get("sketch_ref")
                if not note:
                    if status == ELEC_STATUS_CONFIRMED:
                        blockers.append(_msg(MSG_ELEC_CUSTOM_NOTE, level="blocker"))
                    else:
                        warnings.append(_msg(MSG_ELEC_CUSTOM_NOTE, level="warning"))
            infos.append(_msg(MSG_ELEC_ROUTE_CABLES, level="info"))
        elif supply == SUPPLY_SHARED:
            shared = str(panel.get("shared_from_panel_id") or "")
            if not shared or shared not in assembly_panel_ids:
                blockers.append(_msg(MSG_ELEC_INVALID_SHARED, level="blocker"))
            elif shared == pid:
                blockers.append(_msg(MSG_ELEC_SELF_SHARED, level="blocker"))
            else:
                infos.append(_msg(MSG_ELEC_SHARED_FROM_PANEL, level="info"))
            pos = panel.get("service_point_position")
            if pos and pos not in {POSITION_NONE, None}:
                # soft contradiction: shared feed but local 220V position set
                warnings.append(_msg(MSG_ELEC_CONTRADICTION, level="warning"))
        elif supply == SUPPLY_NONE:
            pos = panel.get("service_point_position")
            if pos and pos not in {POSITION_NONE, None}:
                warnings.append(_msg(MSG_ELEC_CONTRADICTION, level="warning"))

        workshop = _as_dict(panel.get("workshop_prep"))
        if workshop.get("reserve_required"):
            infos.append(_msg(MSG_ELEC_RESERVE, level="info"))
        install = _as_dict(panel.get("installation"))
        if install.get("finalize_after_alignment"):
            infos.append(_msg(MSG_ELEC_AFTER_ALIGNMENT, level="info"))

    for conn in _as_list(electrical.get("inter_panel_connections")):
        if not isinstance(conn, Mapping):
            continue
        src = str(conn.get("source_panel_id") or "")
        dst = str(conn.get("destination_panel_id") or "")
        if src not in assembly_panel_ids or dst not in assembly_panel_ids or src == dst:
            blockers.append(_msg(MSG_ELEC_INVALID_CONNECTION, level="blocker"))
        elif conn.get("alignment_dependent") and not conn.get("completed_on_site"):
            infos.append(_msg(MSG_ELEC_AFTER_ALIGNMENT, level="info"))
        if conn.get("reserve_required"):
            infos.append(_msg(MSG_ELEC_RESERVE, level="info"))

    if status == ELEC_STATUS_CONFIRMED:
        infos.append(_msg(MSG_ELEC_CONFIRMED, level="info"))
        # Confirming with any UNCONFIRMED panel is a blocker
        for panel in panels:
            if str(panel.get("supply_mode") or "").upper() == SUPPLY_UNCONFIRMED:
                blockers.append(_msg(MSG_ELEC_UNCONFIRMED, level="blocker"))

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


def normalize_electrical_connection_management(
    raw: Any,
    *,
    assembly_panel_ids: set[str],
) -> dict[str, Any] | None:
    if raw is None:
        return None
    incoming = _as_dict(raw)
    if not incoming:
        return None

    status = str(incoming.get("status") or ELEC_STATUS_DRAFT).strip().upper()
    if status not in {ELEC_STATUS_INACTIVE, ELEC_STATUS_DRAFT, ELEC_STATUS_CONFIRMED}:
        status = ELEC_STATUS_DRAFT

    panels_in = _as_list(incoming.get("panels"))
    panels: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_panel in panels_in:
        normalized = _normalize_panel_electrical(raw_panel, known_panel_ids=assembly_panel_ids)
        if not normalized:
            continue
        pid = normalized["panel_id"]
        if pid in seen:
            continue
        seen.add(pid)
        known = normalized.pop("_known", True)
        if not known and pid not in assembly_panel_ids:
            # keep invalid for validation to surface
            pass
        panels.append(normalized)

    # Ensure every assembly panel has a row (default UNCONFIRMED)
    for pid in sorted(assembly_panel_ids):
        if pid in seen:
            continue
        panels.append(
            {
                "panel_id": pid,
                "supply_mode": SUPPLY_UNCONFIRMED,
                "shared_from_panel_id": None,
                "service_point_position": None,
                "custom_position_note": None,
                "sketch_ref": None,
                "cable_exit_position": None,
                "routing_direction_note_ro": None,
                "power_supply_group_id": None,
                "letter_group_ref": None,
                "workshop_prep": _normalize_workshop(None),
                "installation": _normalize_installation(None),
                "notes_ro": None,
            }
        )

    connections = []
    for i, raw_c in enumerate(_as_list(incoming.get("inter_panel_connections"))):
        conn = _normalize_connection(raw_c, index=i)
        if conn:
            connections.append(conn)

    operator_confirmed = bool(incoming.get("operator_confirmed")) and status == ELEC_STATUS_CONFIRMED
    if status != ELEC_STATUS_CONFIRMED:
        operator_confirmed = False

    out: dict[str, Any] = {
        "schema": ELECTRICAL_SCHEMA,
        "contract_version": ELECTRICAL_CONTRACT_VERSION,
        "status": status,
        "operator_confirmed": operator_confirmed,
        "panels": panels,
        "inter_panel_connections": connections,
        "meta": electrical_meta(),
    }
    validation = validate_electrical_connection_management(out, assembly_panel_ids=assembly_panel_ids)
    out["validation"] = validation

    confirmation = incoming.get("confirmation")
    if status == ELEC_STATUS_CONFIRMED:
        out["confirmation"] = {
            "message_code": MSG_ELEC_CONFIRMED,
            "message": operator_message(MSG_ELEC_CONFIRMED),
            "authority": "OPERATOR",
        }
    elif isinstance(confirmation, Mapping):
        out["confirmation"] = dict(confirmation)

    return out


def electrical_confirmation_blockers(
    electrical: Mapping[str, Any] | None,
    *,
    assembly_panel_ids: set[str],
) -> list[dict[str, str]]:
    validation = validate_electrical_connection_management(
        electrical, assembly_panel_ids=assembly_panel_ids
    )
    return list(validation.get("blockers") or [])


def project_electrical_for_product_definition(
    electrical: Mapping[str, Any] | None,
    *,
    assembly_confirmed: bool,
) -> dict[str, Any] | None:
    """Authoritative PD electrical: only when assembly + electrical are CONFIRMED."""
    if not assembly_confirmed or not isinstance(electrical, Mapping):
        return None
    status = str(electrical.get("status") or "").upper()
    if status != ELEC_STATUS_CONFIRMED or not bool(electrical.get("operator_confirmed")):
        return None
    return {
        "schema": ELECTRICAL_SCHEMA,
        "contract_version": ELECTRICAL_CONTRACT_VERSION,
        "status": ELEC_STATUS_CONFIRMED,
        "operator_confirmed": True,
        "panels": [dict(p) for p in _as_list(electrical.get("panels")) if isinstance(p, Mapping)],
        "inter_panel_connections": [
            dict(c)
            for c in _as_list(electrical.get("inter_panel_connections"))
            if isinstance(c, Mapping)
        ],
        "validation": electrical.get("validation") or {"blockers": [], "warnings": [], "infos": []},
        "confirmation": electrical.get("confirmation"),
        "meta": electrical_meta(),
        "task_materialization": False,
        "pricing": False,
        "psu_sizing": False,
    }


def project_electrical_for_aggregate(
    electrical: Mapping[str, Any] | None,
    *,
    assembly_confirmed: bool,
) -> dict[str, Any] | None:
    pd = project_electrical_for_product_definition(
        electrical, assembly_confirmed=assembly_confirmed
    )
    if pd is None:
        return None
    future_intent: list[str] = []
    for panel in pd.get("panels") or []:
        if not isinstance(panel, Mapping):
            continue
        if panel.get("supply_mode") == SUPPLY_DIRECT:
            future_intent.append("route_cables_to_declared_service_point")
        if panel.get("supply_mode") == SUPPLY_SHARED:
            future_intent.append("inter_panel_lv_feed")
        install = _as_dict(panel.get("installation"))
        if install.get("finalize_after_alignment"):
            future_intent.append("finalize_connection_after_panel_alignment")
    for conn in pd.get("inter_panel_connections") or []:
        if isinstance(conn, Mapping) and conn.get("alignment_dependent"):
            future_intent.append("finalize_connection_after_panel_alignment")
    # dedupe intents
    future_intent = list(dict.fromkeys(future_intent))
    return {
        "kind": "acm_segmented_electrical_connection",
        "contract_version": ELECTRICAL_CONTRACT_VERSION,
        "status": ELEC_STATUS_CONFIRMED,
        "panels": pd.get("panels"),
        "inter_panel_connections": pd.get("inter_panel_connections"),
        "workshop_install_split": True,
        "future_task_intent": future_intent,
        "future_task_intent_authority": "INFORMATIONAL_ONLY",
        "task_contract_authority": "task_contract.task_rules — not this projection",
        "materials": [],
        "processes": [],
        "task_rules": [],
        "execution_effects": [],
        "psu_sizing": False,
        "pricing": False,
        "notes": [
            "Confirmed electrical context only — no PSU sizing, pricing, or Execution tasks.",
            "Letter-local LED/wiring remains on volumetric-letter ownership.",
        ],
    }


def project_electrical_draft_non_authoritative(
    electrical: Mapping[str, Any] | None,
    *,
    assembly_confirmed: bool,
) -> dict[str, Any] | None:
    """Expose DRAFT/unconfirmed electrical as non-authoritative metadata on PD."""
    if not assembly_confirmed or not isinstance(electrical, Mapping):
        return None
    status = str(electrical.get("status") or "").upper()
    if status == ELEC_STATUS_CONFIRMED and bool(electrical.get("operator_confirmed")):
        return None
    if status == ELEC_STATUS_INACTIVE:
        return None
    return {
        "schema": ELECTRICAL_SCHEMA,
        "status": status or ELEC_STATUS_DRAFT,
        "operator_confirmed": False,
        "authoritative": False,
        "downstream_effects": False,
        "panels": [dict(p) for p in _as_list(electrical.get("panels")) if isinstance(p, Mapping)],
        "inter_panel_connections": [
            dict(c)
            for c in _as_list(electrical.get("inter_panel_connections"))
            if isinstance(c, Mapping)
        ],
        "validation": electrical.get("validation"),
    }
