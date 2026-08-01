"""
Ops-graph frozen technical materials — read-only projection.

Projects allowlisted fields from Order Snapshot V2
`product_aggregate_snapshot.materials` for operator display.

Does NOT:
- mutate snapshot / plan / tasks
- invent quantities (null stays null)
- dedupe / sum / collapse variants
- read Intake, live Product System, Pricing, or Inventory
- claim stock, reservation, or consumption
"""

from __future__ import annotations

import copy
import json
from typing import Any


PROJECTION_VERSION = "ops_graph_frozen_technical_materials/v1"
SOURCE_PATH = "order_snapshot_v2.product_aggregate_snapshot.materials"

SEMANTIC_TITLE_RO = "Materiale tehnice conform comenzii"
SEMANTIC_NOTE_RO = (
    "Lista provine din definiția tehnică înghețată a comenzii. "
    "Nu reprezintă stoc, rezervare sau consum."
)

# Allowlisted material row fields only — never price/cost/rates.
_ALLOWED_ENTRY_KEYS = (
    "material_code",
    "label",
    "unit",
    "quantity",
    "provenance",
    "component_ref",
    "source_template_code",
)


def _as_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text if text else None
    text = str(value).strip()
    return text if text else None


def _as_quantity(value: Any) -> float | int | None:
    """Preserve null. Never coerce missing to 0."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    return None


def _project_entry(row: dict[str, Any], entry_index: int) -> dict[str, Any]:
    return {
        "entry_index": entry_index,
        "material_code": _as_optional_str(row.get("material_code")),
        "label": _as_optional_str(row.get("label")),
        "unit": _as_optional_str(row.get("unit")),
        "quantity": _as_quantity(row.get("quantity")),
        "provenance": _as_optional_str(row.get("provenance")),
        "component_ref": _as_optional_str(row.get("component_ref")),
        "source_template_code": _as_optional_str(row.get("source_template_code")),
    }


def _parse_snapshot(snapshot_v2_json: str | None) -> tuple[dict[str, Any] | None, str | None]:
    if snapshot_v2_json is None or (
        isinstance(snapshot_v2_json, str) and not snapshot_v2_json.strip()
    ):
        return None, "snapshot_missing"
    if not isinstance(snapshot_v2_json, str):
        return None, "snapshot_invalid"
    try:
        payload = json.loads(snapshot_v2_json)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None, "snapshot_invalid"
    if not isinstance(payload, dict):
        return None, "snapshot_invalid"
    return payload, None


def project_frozen_technical_materials(
    snapshot_v2_json: str | None,
) -> dict[str, Any]:
    """
    Build display-only projection. Does not mutate input JSON.
    Preserves source list order and duplicate codes.
    """
    base: dict[str, Any] = {
        "version": PROJECTION_VERSION,
        "source": SOURCE_PATH,
        "title": SEMANTIC_TITLE_RO,
        "semantic_note": SEMANTIC_NOTE_RO,
        "status": "present",
        "entries": [],
        "entry_count": 0,
        "warnings": [],
    }

    snapshot, err = _parse_snapshot(snapshot_v2_json)
    if err:
        base["status"] = err
        base["warnings"].append(err)
        return base

    # Deep-copy only the materials list branch for safety; never write back.
    pa = snapshot.get("product_aggregate_snapshot")
    if not isinstance(pa, dict):
        base["status"] = "materials_absent"
        base["warnings"].append("product_aggregate_snapshot_absent")
        return base

    materials = pa.get("materials")
    if materials is None:
        base["status"] = "materials_absent"
        base["warnings"].append("materials_key_absent")
        return base
    if not isinstance(materials, list):
        base["status"] = "materials_absent"
        base["warnings"].append("materials_not_list")
        return base
    if len(materials) == 0:
        base["status"] = "materials_empty"
        return base

    # Detect duplicate codes without merging (honesty warning only).
    codes_seen: dict[str, int] = {}
    entries: list[dict[str, Any]] = []
    for idx, raw in enumerate(materials):
        if not isinstance(raw, dict):
            base["warnings"].append(f"entry_{idx}_not_object")
            continue
        # Work on a shallow copy of allowlisted keys only — ignore price fields.
        allowlisted = {k: copy.copy(raw.get(k)) for k in _ALLOWED_ENTRY_KEYS if k in raw}
        entry = _project_entry(allowlisted, entry_index=idx)
        code = entry.get("material_code")
        if code:
            codes_seen[code] = codes_seen.get(code, 0) + 1
        entries.append(entry)

    dup_codes = sorted(code for code, n in codes_seen.items() if n > 1)
    if dup_codes:
        base["warnings"].append(
            "duplicate_material_codes_preserved:" + ",".join(dup_codes)
        )

    base["entries"] = entries
    base["entry_count"] = len(entries)
    base["status"] = "present"
    return base


def attach_frozen_technical_materials_to_plan_payload(
    payload: dict[str, Any],
    snapshot_v2_json: str | None,
) -> dict[str, Any]:
    """Attach projection to GET plan payload without mutating tasks."""
    payload["frozen_technical_materials"] = project_frozen_technical_materials(
        snapshot_v2_json
    )
    return payload
