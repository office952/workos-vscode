"""LetterGroupInstance authority — write SoT for volumetric letter groups.

READ: instances if present else one-time hydrate from letter_group_finishes.
WRITE: letter_group_instances[] (coalesce preserves when omitted).
PROJECTION: one-way instances → letter_group_finishes for legacy consumers.
"""

from __future__ import annotations

import uuid
from typing import Any, Mapping, MutableMapping

LETTER_GROUP_INSTANCE_SCHEMA = "volumetric_letter_group_instance_v1"
COMPONENT_PLACEMENT_SCHEMA = "component_placement_v1"

_LEGACY_FINISH_KEYS = (
    "group_key",
    "layer_name",
    "source_fill_color",
    "face_area_m2",
    "perimeter_m",
    "element_count",
    "face_finish_type",
    "face_oracal_code",
    "face_oracal_name",
    "return_finish_type",
    "return_oracal_code",
    "return_oracal_name",
    "return_depth_mm",
    "face_vinyl_roll_width_mm",
    "backing_mode",
    "confirmed",
)


def _as_dict(value: Any) -> dict[str, Any] | None:
    return dict(value) if isinstance(value, Mapping) else None


def _new_instance_id() -> str:
    return str(uuid.uuid4())


def _workspace_lighting(finish: Mapping[str, Any]) -> dict[str, Any]:
    # Copy flags/system once; leave led_module_count unset so quantity builder
    # falls back to workspace total (avoids N× double-count on hydrate).
    return {
        "illuminated": bool(finish.get("illuminated", True)),
        "lighting_system_type": finish.get("lighting_system_type"),
        "light_color": finish.get("light_color"),
        "led_module_count": None,
        "selected_psu_watts": finish.get("selected_psu_watts"),
    }


def legacy_finish_to_instance(
    row: Mapping[str, Any],
    *,
    finish: Mapping[str, Any],
    svg_hash: str | None = None,
    existing_id: str | None = None,
) -> dict[str, Any]:
    group_key = str(row.get("group_key") or "").strip()
    lighting = row.get("lighting") if isinstance(row.get("lighting"), Mapping) else None
    return {
        "schema": LETTER_GROUP_INSTANCE_SCHEMA,
        "instance_id": existing_id or str(row.get("instance_id") or "").strip() or _new_instance_id(),
        "group_key": group_key,
        "source_layer_ids": [group_key] if group_key else [],
        "artwork_reference": {
            "layer_key": group_key,
            "source_svg_hash": svg_hash,
            "binding_id": None,
        },
        "geometry": {
            "face_area_m2": row.get("face_area_m2"),
            "perimeter_m": row.get("perimeter_m"),
            "element_count": row.get("element_count"),
            "source_fill_color": row.get("source_fill_color"),
        },
        "construction": {"return_depth_mm": row.get("return_depth_mm")},
        "materials": {
            "face_finish_type": row.get("face_finish_type"),
            "face_oracal_code": row.get("face_oracal_code"),
            "face_oracal_name": row.get("face_oracal_name"),
            "face_vinyl_roll_width_mm": row.get("face_vinyl_roll_width_mm"),
            "return_finish_type": row.get("return_finish_type"),
            "return_oracal_code": row.get("return_oracal_code"),
            "return_oracal_name": row.get("return_oracal_name"),
            "backing_mode": row.get("backing_mode"),
        },
        "finish": {
            "face_finish_type": row.get("face_finish_type"),
            "return_finish_type": row.get("return_finish_type"),
            "backing_mode": row.get("backing_mode"),
        },
        "lighting": dict(lighting) if lighting else _workspace_lighting(finish),
        "confirmed": bool(row.get("confirmed")),
        "provenance": {
            "source": "hydrated_legacy" if not row.get("instance_id") else "instance",
            "geometry_drift": row.get("geometry_drift"),
        },
        "layer_name": row.get("layer_name") or group_key,
    }


def project_instance_to_legacy_finish(instance: Mapping[str, Any]) -> dict[str, Any]:
    geom = instance.get("geometry") if isinstance(instance.get("geometry"), Mapping) else {}
    mats = instance.get("materials") if isinstance(instance.get("materials"), Mapping) else {}
    construction = (
        instance.get("construction") if isinstance(instance.get("construction"), Mapping) else {}
    )
    return {
        "group_key": instance.get("group_key"),
        "layer_name": instance.get("layer_name") or instance.get("group_key"),
        "source_fill_color": geom.get("source_fill_color"),
        "face_area_m2": geom.get("face_area_m2"),
        "perimeter_m": geom.get("perimeter_m"),
        "element_count": geom.get("element_count"),
        "face_finish_type": mats.get("face_finish_type"),
        "face_oracal_code": mats.get("face_oracal_code"),
        "face_oracal_name": mats.get("face_oracal_name"),
        "return_finish_type": mats.get("return_finish_type"),
        "return_oracal_code": mats.get("return_oracal_code"),
        "return_oracal_name": mats.get("return_oracal_name"),
        "return_depth_mm": construction.get("return_depth_mm"),
        "face_vinyl_roll_width_mm": mats.get("face_vinyl_roll_width_mm"),
        "backing_mode": mats.get("backing_mode"),
        "confirmed": bool(instance.get("confirmed")),
    }


def read_letter_group_instances(finish: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(finish, Mapping):
        return []
    raw = finish.get("letter_group_instances")
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for row in raw:
        if not isinstance(row, Mapping):
            continue
        iid = str(row.get("instance_id") or "").strip()
        gk = str(row.get("group_key") or "").strip()
        if iid and gk:
            out.append(dict(row))
    return out


def hydrate_instances_from_legacy(
    finish: Mapping[str, Any],
    *,
    svg_hash: str | None = None,
) -> list[dict[str, Any]]:
    existing = read_letter_group_instances(finish)
    if existing:
        return existing
    legacy = finish.get("letter_group_finishes")
    if not isinstance(legacy, list):
        return []
    return [
        legacy_finish_to_instance(row, finish=finish, svg_hash=svg_hash)
        for row in legacy
        if isinstance(row, Mapping) and str(row.get("group_key") or "").strip()
    ]


def project_instances_to_legacy_finishes(instances: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [project_instance_to_legacy_finish(i) for i in instances]


def ensure_placements(
    finish: Mapping[str, Any],
    instances: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    existing = finish.get("component_placements")
    if isinstance(existing, list) and existing:
        return [dict(p) for p in existing if isinstance(p, Mapping)]

    acm = finish.get("acm_panel_instance")
    acm_id = None
    if isinstance(acm, Mapping):
        acm_id = str(acm.get("component_instance_id") or "").strip() or None

    placements: list[dict[str, Any]] = []
    for inst in instances:
        source_id = str(inst.get("instance_id") or "").strip()
        if not source_id:
            continue
        if acm_id:
            placements.append(
                {
                    "schema": COMPONENT_PLACEMENT_SCHEMA,
                    "placement_id": str(uuid.uuid4()),
                    "source_instance_id": source_id,
                    "target_kind": "acm_panel",
                    "target_instance_id": acm_id,
                    "target_face": None,
                    "mounting_method": None,
                }
            )
        else:
            placements.append(
                {
                    "schema": COMPONENT_PLACEMENT_SCHEMA,
                    "placement_id": str(uuid.uuid4()),
                    "source_instance_id": source_id,
                    "target_kind": "none",
                    "target_instance_id": None,
                    "target_face": None,
                    "mounting_method": None,
                }
            )
    return placements


def _incoming_instance_rows(finish: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Accept rows with group_key even when instance_id is still to be minted."""
    raw = finish.get("letter_group_instances")
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for row in raw:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("group_key") or "").strip():
            out.append(dict(row))
    return out


def coalesce_letter_group_authority_for_finish(
    finish_doc: MutableMapping[str, Any],
    existing_finish: Mapping[str, Any] | None,
    *,
    svg_hash: str | None = None,
) -> dict[str, Any]:
    """Preserve instances when omitted; hydrate once from legacy; project one-way."""
    out = dict(finish_doc)
    existing = _as_dict(existing_finish) or {}

    incoming = _incoming_instance_rows(out)
    prior = read_letter_group_instances(existing)

    if not incoming and prior:
        # Omit must not wipe — AcmPanel-style preserve.
        instances = prior
    elif not incoming:
        instances = hydrate_instances_from_legacy(out if out.get("letter_group_finishes") else existing, svg_hash=svg_hash)
        if not instances and existing.get("letter_group_finishes"):
            instances = hydrate_instances_from_legacy(existing, svg_hash=svg_hash)
    else:
        # Reuse prior UUIDs by group_key when present.
        prior_by_key = {str(p.get("group_key")): p for p in prior}
        merged: list[dict[str, Any]] = []
        for row in incoming:
            key = str(row.get("group_key") or "")
            prev = prior_by_key.get(key)
            iid = str(row.get("instance_id") or "").strip()
            if not iid and prev:
                row = {**row, "instance_id": prev.get("instance_id")}
            elif not iid:
                row = {**row, "instance_id": _new_instance_id()}
            # Never let empty lighting wipe prior instance lighting.
            if not isinstance(row.get("lighting"), Mapping) and prev and isinstance(prev.get("lighting"), Mapping):
                row = {**row, "lighting": dict(prev["lighting"])}
            merged.append(dict(row))
        # Confirmed orphans (group_key left analysis) stay — join is by key, not index.
        incoming_keys = {str(r.get("group_key") or "") for r in merged}
        for prev in prior:
            key = str(prev.get("group_key") or "")
            if key and key not in incoming_keys and bool(prev.get("confirmed")):
                merged.append(dict(prev))
        instances = merged

    if instances:
        out["letter_group_instances"] = instances
        out["letter_group_finishes"] = project_instances_to_legacy_finishes(instances)
        out["component_placements"] = ensure_placements(out, instances)
    elif prior:
        out["letter_group_instances"] = prior
        out["letter_group_finishes"] = project_instances_to_legacy_finishes(prior)
        placements = existing.get("component_placements")
        if isinstance(placements, list):
            out["component_placements"] = placements

    return out


def build_volumetric_letters_commercial_quantities(
    *,
    quote_geometry: Mapping[str, Any] | None,
    finish_setup: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Sole V6 commercial quantity resolver for letters (no rates, no money)."""
    geom = dict(quote_geometry) if isinstance(quote_geometry, Mapping) else {}
    finish = dict(finish_setup) if isinstance(finish_setup, Mapping) else {}
    instances = read_letter_group_instances(finish) or hydrate_instances_from_legacy(finish)

    face_sum = 0.0
    peri_sum = 0.0
    face_any = False
    peri_any = False
    for inst in instances:
        g = inst.get("geometry") if isinstance(inst.get("geometry"), Mapping) else {}
        fa = g.get("face_area_m2")
        pm = g.get("perimeter_m")
        try:
            if fa is not None and float(fa) > 0:
                face_sum += float(fa)
                face_any = True
        except (TypeError, ValueError):
            pass
        try:
            if pm is not None and float(pm) > 0:
                peri_sum += float(pm)
                peri_any = True
        except (TypeError, ValueError):
            pass

    letter_face = None
    if face_any:
        letter_face = round(face_sum, 6)
    else:
        for key in ("letter_face_area_m2", "face_area_m2"):
            try:
                v = float(geom.get(key))  # type: ignore[arg-type]
                if v > 0:
                    letter_face = v
                    break
            except (TypeError, ValueError):
                continue

    letter_peri = None
    # Official CPP outer perimeter remains quote_geometry when present.
    try:
        v = float(geom.get("letter_perimeter_m"))  # type: ignore[arg-type]
        if v > 0:
            letter_peri = v
    except (TypeError, ValueError):
        if peri_any:
            letter_peri = round(peri_sum, 6)

    led_count = None
    for inst in instances:
        lighting = inst.get("lighting") if isinstance(inst.get("lighting"), Mapping) else {}
        if lighting.get("illuminated") is False:
            continue
        try:
            n = int(lighting.get("led_module_count"))  # type: ignore[arg-type]
            if n > 0:
                led_count = (led_count or 0) + n
        except (TypeError, ValueError):
            continue
    if led_count is None:
        for key in ("letter_led_module_count", "led_module_count"):
            try:
                n = int(finish.get(key))  # type: ignore[arg-type]
                if n > 0:
                    led_count = n
                    break
            except (TypeError, ValueError):
                continue

    return {
        "schema": "volumetric_letters_commercial_quantities_v1",
        "source": "letter_group_instance_authority",
        "letter_face_area_m2": letter_face,
        "letter_perimeter_m": letter_peri,
        "letter_return_perimeter_ml": geom.get("letter_return_perimeter_ml"),
        "cnc_cutting_perimeter_ml": geom.get("cnc_cutting_perimeter_ml"),
        "led_perimeter_ml": geom.get("led_perimeter_ml"),
        "led_module_count": led_count,
        "instance_count": len(instances),
        "cost_engine_legacy": True,
        "notes": [
            "CPP consumes outer letter_perimeter_m / letter_face_area_m2 via this resolver",
            "CostEngine may still read quote_geometry CNC/return keys — not a V6 override",
        ],
    }
