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


PROJECTION_VERSION = "ops_graph_frozen_technical_materials/v2"
SOURCE_PATH = "order_snapshot_v2.product_aggregate_snapshot.materials"

SEMANTIC_TITLE_RO = "Materiale tehnice conform comenzii"
SEMANTIC_NOTE_RO = (
    "Necesar tehnic înghețat la acceptarea comenzii. "
    "Nu reprezintă stoc, rezervare sau recomandare de achiziție."
)

# Allowlisted material row fields only — never price/cost/rates.
_ALLOWED_ENTRY_KEYS = (
    "material_code",
    "label",
    "unit",
    "quantity",
    "quantity_status",
    "quantity_model",
    "requirement_id",
    "variant_discriminator",
    "quantity_formula_id",
    "quantity_input_keys",
    "owner_scope",
    "provenance",
    "component_ref",
    "source_template_code",
)

_QUANTITY_STATUS_LABELS_RO = {
    "derived": "Calculată",
    "reference_only": "De referință",
    "source_missing": "Sursă lipsă",
    "legacy_unspecified": "Legacy / nespecificată",
}

_QUANTITY_MISSING_REASON_RO = {
    "source_missing": (
        "Cantitatea nu poate fi calculată încă deoarece lipsește "
        "sursa tehnică necesară."
    ),
    "reference_only": (
        "Material de referință — fără formulă de cantitate pe componentă."
    ),
    "legacy_unspecified": (
        "Snapshot vechi — cantitatea nu a fost înghețată pe contractul curent."
    ),
}


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


def _normalize_quantity_status(
    raw_status: Any,
    quantity: float | int | None,
) -> str:
    """Map legacy rows (no status) to honest legacy_unspecified."""
    text = _as_optional_str(raw_status)
    if text in _QUANTITY_STATUS_LABELS_RO:
        return text
    if quantity is not None:
        return "derived"
    return "legacy_unspecified"


def _project_entry(row: dict[str, Any], entry_index: int) -> dict[str, Any]:
    quantity = _as_quantity(row.get("quantity"))
    quantity_status = _normalize_quantity_status(row.get("quantity_status"), quantity)
    missing_reason = None
    if quantity is None:
        missing_reason = _QUANTITY_MISSING_REASON_RO.get(quantity_status)
    input_keys = row.get("quantity_input_keys")
    if not isinstance(input_keys, list):
        input_keys = None
    else:
        input_keys = [str(k) for k in input_keys if k is not None]
    return {
        "entry_index": entry_index,
        "material_code": _as_optional_str(row.get("material_code")),
        "label": _as_optional_str(row.get("label")),
        "unit": _as_optional_str(row.get("unit")),
        "quantity": quantity,
        "quantity_status": quantity_status,
        "quantity_status_label_ro": _QUANTITY_STATUS_LABELS_RO.get(
            quantity_status, "Legacy / nespecificată"
        ),
        "quantity_missing_reason_ro": missing_reason,
        "quantity_model": _as_optional_str(row.get("quantity_model")),
        "requirement_id": _as_optional_str(row.get("requirement_id")),
        "variant_discriminator": _as_optional_str(row.get("variant_discriminator")),
        "quantity_formula_id": _as_optional_str(row.get("quantity_formula_id")),
        "quantity_input_keys": input_keys,
        "owner_scope": _as_optional_str(row.get("owner_scope")),
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
