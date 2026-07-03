"""
Sprint #27 — ProductSystem Strict Contract Validator.

Purpose
-------
Enforce the canonical hierarchical shape of a `product_templates` row at the
ROUTER boundary. When a client POSTs / PUTs a row with malformed JSON, the
router rejects the request with HTTP 422 and a precise `detail` list so the
frontend can surface field-level errors without guessing.

Canonical rules (MUST match the frontend `validateTemplateComponentsStrict`
byte-for-byte):

    COMPONENT_ID_EMPTY              — component.component_id must be non-empty
    COMPONENT_ID_DUPLICATE          — component_id must be unique across components[]
    COMPONENT_TYPE_INVALID          — component.type must be one of the
                                       ALLOWED_COMPONENT_TYPES tuple (original ACP
                                       types + BUILD 4 advertising production types)
    COMPONENT_NAME_EMPTY            — component.name must be non-empty
    OPERATION_CODE_EMPTY            — operation.code must be non-empty
    OPERATION_WORKCENTER_EMPTY      — operation.workcenter must be non-empty
    OPERATION_MINUTES_NON_POSITIVE  — static op must have estimatedMinutes > 0
    OPERATION_SEQUENCE_NON_POSITIVE — operation.sequence must be > 0
    OPERATION_FORMULA_ID_EMPTY      — formula_based op must declare formula_id
    MATERIAL_CODE_EMPTY             — material.materialCode must be non-empty
    MATERIAL_QUANTITY_NON_POSITIVE  — static material must have quantity > 0
    MATERIAL_UNIT_EMPTY             — material.unit must be non-empty
    MATERIAL_FORMULA_ID_EMPTY       — formula_based material must declare formula_id
    COMPONENT_REF_ORPHAN            — operation/material.component_ref must
                                       resolve to an existing component_id

Dual-name fields:
  - `materialCode` (camelCase) and `material_code` (snake_case) are both
    accepted. At least one must be a non-empty string; after validation the
    canonical payload is normalized to include both forms.
  - `estimatedMinutes` and `estimated_minutes` — same rule.

Flat-only payloads (operations_json / required_materials_json carrying rows
whose `component_ref` does NOT resolve to any component_id in components_json)
are rejected: the write path is strictly hierarchical in Sprint #27.

Legacy READS remain lenient elsewhere (the router does not re-validate on
GET; this module only runs on CREATE/UPDATE).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

# Canonical component types — MUST stay in sync with
# PRODUCT_COMPONENT_TYPES in app/frontend/src/lib/api.ts.
# These 6 types come from the approved ProductSystem spec
# (Panouri ACP Iluminate canonical template). Validation remains strict:
# unknown types are rejected, never coerced.
ALLOWED_COMPONENT_TYPES: Tuple[str, ...] = (
    # --- Original ACP types ---
    "STRUCTURA",
    "FATA_ACP_ROUTATA",
    "DIFUZIE_PLEXI",
    "ILUMINARE",
    "RELIEF_PLEXI_10MM",
    "FINISAJ",
    # --- BUILD 4: Advertising production types ---
    "PRINT_SUBSTRATE",       # Banner / mesh print surface
    "VINYL_APPLICATION",     # Autocolant / sticker / folie
    "PLEXI_PANEL",           # Plexiglass plate / sheet
    "FRAME_PROFILE",         # Lightbox / caseta frame
    "LITERE_3D",             # Volumetric letters face/side
    "ELECTRIC_LED",          # LED system for lightbox/letters
    "EXTERNALIZARE",         # Externalized production (mesh etc.)
    "TAIERE_CNC_LASER",      # CNC / laser cutting component
    "LAMINARE",              # Lamination layer
)


class TemplateContractError(Exception):
    """Raised when a product_template payload is structurally invalid.

    `errors` is a list of `{"path", "code", "detail"}` dicts so the router can
    forward them to the client as the HTTP 422 body.
    """

    def __init__(self, errors: List[Dict[str, str]]):
        self.errors = errors
        super().__init__(f"product_template contract violation: {errors}")


def _is_positive_number(value: Any) -> bool:
    if value is None:
        return False
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def _coerce_calculation_type(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized in ("static", "formula_based"):
        return normalized
    return None


def _parse_json_string(raw: Any, field_name: str) -> Any:
    """Parse a JSON string field. None / empty string => empty list.

    Accepts already-decoded list/dict for convenience (some callers pre-parse).
    Raises TemplateContractError on malformed JSON.
    """
    if raw is None or raw == "":
        return []
    if isinstance(raw, (list, dict)):
        return raw
    if not isinstance(raw, str):
        raise TemplateContractError(
            [
                {
                    "path": field_name,
                    "code": "JSON_INVALID_TYPE",
                    "detail": f"{field_name} must be a JSON string, list, or dict",
                }
            ]
        )
    try:
        return json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise TemplateContractError(
            [
                {
                    "path": field_name,
                    "code": "JSON_MALFORMED",
                    "detail": f"{field_name} is not valid JSON: {exc}",
                }
            ]
        )


def _validate_component_header(
    raw_component: Any,
    index: int,
    seen_ids: set,
) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    """Validate the component header fields (not its nested rows).

    Returns (normalized_component, errors). Errors are accumulated even when
    the header is bad so the caller can report all problems at once.
    """
    errors: List[Dict[str, str]] = []
    path = f"components[{index}]"

    if not isinstance(raw_component, dict):
        errors.append(
            {
                "path": path,
                "code": "COMPONENT_SHAPE_INVALID",
                "detail": "component must be an object",
            }
        )
        return {}, errors

    cid_raw = raw_component.get("component_id")
    cid = str(cid_raw).strip() if cid_raw is not None else ""
    if not cid:
        errors.append(
            {
                "path": f"{path}.component_id",
                "code": "COMPONENT_ID_EMPTY",
                "detail": "component_id must be a non-empty string",
            }
        )
    elif cid in seen_ids:
        errors.append(
            {
                "path": f"{path}.component_id",
                "code": "COMPONENT_ID_DUPLICATE",
                "detail": f"component_id '{cid}' is not unique",
            }
        )
    else:
        seen_ids.add(cid)

    ctype_raw = raw_component.get("type")
    ctype = str(ctype_raw).strip().upper() if ctype_raw is not None else ""
    if ctype not in ALLOWED_COMPONENT_TYPES:
        errors.append(
            {
                "path": f"{path}.type",
                "code": "COMPONENT_TYPE_INVALID",
                "detail": f"type must be one of {', '.join(ALLOWED_COMPONENT_TYPES)}",
            }
        )

    name_raw = raw_component.get("name")
    name = str(name_raw).strip() if name_raw is not None else ""
    if not name:
        errors.append(
            {
                "path": f"{path}.name",
                "code": "COMPONENT_NAME_EMPTY",
                "detail": "component name must be a non-empty string",
            }
        )

    if raw_component.get("_legacy") is True:
        errors.append(
            {
                "path": path,
                "code": "COMPONENT_LEGACY_UNCONFIRMED",
                "detail": "legacy component must be confirmed (type + name) before save",
            }
        )

    return (
        {
            "component_id": cid,
            "type": ctype if ctype in ALLOWED_COMPONENT_TYPES else "",
            "name": name,
            "operations": list(raw_component.get("operations") or []),
            "materials": list(raw_component.get("materials") or []),
        },
        errors,
    )


def _validate_operation(
    raw_op: Any,
    component_id: str,
    op_index: int,
    known_component_ids: set,
    component_path: str,
) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    errors: List[Dict[str, str]] = []
    op_path = f"{component_path}.operations[{op_index}]"

    if not isinstance(raw_op, dict):
        errors.append(
            {
                "path": op_path,
                "code": "OPERATION_SHAPE_INVALID",
                "detail": "operation must be an object",
            }
        )
        return {}, errors

    code = str(raw_op.get("code") or "").strip()
    if not code:
        errors.append(
            {
                "path": f"{op_path}.code",
                "code": "OPERATION_CODE_EMPTY",
                "detail": "operation.code must be a non-empty string",
            }
        )

    workcenter = str(raw_op.get("workcenter") or "").strip()
    if not workcenter:
        errors.append(
            {
                "path": f"{op_path}.workcenter",
                "code": "OPERATION_WORKCENTER_EMPTY",
                "detail": "operation.workcenter must be a non-empty string",
            }
        )

    calc_type = _coerce_calculation_type(raw_op.get("calculation_type"))
    is_formula = calc_type == "formula_based"

    # Dual-name: estimatedMinutes (camel) / estimated_minutes (snake).
    mins_raw = raw_op.get("estimatedMinutes")
    if mins_raw is None:
        mins_raw = raw_op.get("estimated_minutes")

    if is_formula:
        formula_id = str(raw_op.get("formula_id") or "").strip()
        if not formula_id:
            errors.append(
                {
                    "path": f"{op_path}.formula_id",
                    "code": "OPERATION_FORMULA_ID_EMPTY",
                    "detail": "formula_based operation must declare a non-empty formula_id",
                }
            )
    else:
        if not _is_positive_number(mins_raw):
            errors.append(
                {
                    "path": f"{op_path}.estimatedMinutes",
                    "code": "OPERATION_MINUTES_NON_POSITIVE",
                    "detail": "static operation must have estimatedMinutes > 0",
                }
            )

    seq_raw = raw_op.get("sequence")
    if not _is_positive_number(seq_raw):
        errors.append(
            {
                "path": f"{op_path}.sequence",
                "code": "OPERATION_SEQUENCE_NON_POSITIVE",
                "detail": "operation.sequence must be > 0",
            }
        )

    ref = str(raw_op.get("component_ref") or "").strip()
    if not ref or ref not in known_component_ids:
        errors.append(
            {
                "path": f"{op_path}.component_ref",
                "code": "COMPONENT_REF_ORPHAN",
                "detail": f"operation.component_ref '{ref}' does not resolve to a component_id",
            }
        )
    elif ref != component_id:
        errors.append(
            {
                "path": f"{op_path}.component_ref",
                "code": "COMPONENT_REF_ORPHAN",
                "detail": (
                    f"operation.component_ref '{ref}' does not match its owning "
                    f"component '{component_id}'"
                ),
            }
        )

    # Normalize numeric fields so downstream (service, engine) can trust them.
    try:
        mins_norm = float(mins_raw) if mins_raw is not None else 0.0
    except (TypeError, ValueError):
        mins_norm = 0.0
    try:
        seq_norm = int(seq_raw) if seq_raw is not None else 0
    except (TypeError, ValueError):
        seq_norm = 0

    normalized = {
        "code": code,
        "name": str(raw_op.get("name") or ""),
        "workcenter": workcenter,
        "estimatedMinutes": mins_norm,
        "estimated_minutes": mins_norm,
        "sequence": seq_norm,
        "component_ref": ref,
    }
    if calc_type:
        normalized["calculation_type"] = calc_type
    for opt in ("formula_id", "formula_params", "requires_quote_input"):
        if raw_op.get(opt) is not None:
            normalized[opt] = raw_op[opt]

    return normalized, errors


def _validate_material(
    raw_mat: Any,
    component_id: str,
    mat_index: int,
    known_component_ids: set,
    component_path: str,
) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    errors: List[Dict[str, str]] = []
    mat_path = f"{component_path}.materials[{mat_index}]"

    if not isinstance(raw_mat, dict):
        errors.append(
            {
                "path": mat_path,
                "code": "MATERIAL_SHAPE_INVALID",
                "detail": "material must be an object",
            }
        )
        return {}, errors

    # Dual-name: materialCode (camel) / material_code (snake).
    code_camel = str(raw_mat.get("materialCode") or "").strip()
    code_snake = str(raw_mat.get("material_code") or "").strip()
    code = code_camel or code_snake
    if not code:
        errors.append(
            {
                "path": f"{mat_path}.materialCode",
                "code": "MATERIAL_CODE_EMPTY",
                "detail": "material.materialCode must be a non-empty string",
            }
        )

    unit = str(raw_mat.get("unit") or "").strip()
    if not unit:
        errors.append(
            {
                "path": f"{mat_path}.unit",
                "code": "MATERIAL_UNIT_EMPTY",
                "detail": "material.unit must be a non-empty string",
            }
        )

    calc_type = _coerce_calculation_type(raw_mat.get("calculation_type"))
    is_formula = calc_type == "formula_based"

    if is_formula:
        formula_id = str(raw_mat.get("formula_id") or "").strip()
        if not formula_id:
            errors.append(
                {
                    "path": f"{mat_path}.formula_id",
                    "code": "MATERIAL_FORMULA_ID_EMPTY",
                    "detail": "formula_based material must declare a non-empty formula_id",
                }
            )
    else:
        if not _is_positive_number(raw_mat.get("quantity")):
            errors.append(
                {
                    "path": f"{mat_path}.quantity",
                    "code": "MATERIAL_QUANTITY_NON_POSITIVE",
                    "detail": "static material must have quantity > 0",
                }
            )

    ref = str(raw_mat.get("component_ref") or "").strip()
    if not ref or ref not in known_component_ids:
        errors.append(
            {
                "path": f"{mat_path}.component_ref",
                "code": "COMPONENT_REF_ORPHAN",
                "detail": f"material.component_ref '{ref}' does not resolve to a component_id",
            }
        )
    elif ref != component_id:
        errors.append(
            {
                "path": f"{mat_path}.component_ref",
                "code": "COMPONENT_REF_ORPHAN",
                "detail": (
                    f"material.component_ref '{ref}' does not match its owning "
                    f"component '{component_id}'"
                ),
            }
        )

    try:
        qty_norm = float(raw_mat.get("quantity") or 0)
    except (TypeError, ValueError):
        qty_norm = 0.0

    normalized: Dict[str, Any] = {
        "materialCode": code,
        "material_code": code,
        "name": str(raw_mat.get("name") or ""),
        "quantity": qty_norm,
        "unit": unit,
        "component_ref": ref,
    }
    if calc_type:
        normalized["calculation_type"] = calc_type
    for opt in ("formula_id", "formula_params", "requires_quote_input"):
        if raw_mat.get(opt) is not None:
            normalized[opt] = raw_mat[opt]

    return normalized, errors


def validate_hierarchical_payload(
    components_json: Any,
    operations_json: Any,
    required_materials_json: Any,
) -> Dict[str, Any]:
    """Validate and normalize the three JSON fields.

    Returns a dict with keys `components_json`, `operations_json`,
    `required_materials_json` holding JSON-encoded normalized strings ready
    for persistence.

    Raises `TemplateContractError` with a precise list of field errors on
    any violation. All errors found in one payload are accumulated so the
    client receives a complete report.
    """
    errors: List[Dict[str, str]] = []

    components_raw = _parse_json_string(components_json, "components_json")
    flat_ops_raw = _parse_json_string(operations_json, "operations_json")
    flat_mats_raw = _parse_json_string(required_materials_json, "required_materials_json")

    if not isinstance(components_raw, list) or len(components_raw) == 0:
        errors.append(
            {
                "path": "components_json",
                "code": "COMPONENTS_EMPTY",
                "detail": "components_json must be a non-empty array of component objects",
            }
        )
        raise TemplateContractError(errors)

    if not isinstance(flat_ops_raw, list):
        errors.append(
            {
                "path": "operations_json",
                "code": "OPERATIONS_SHAPE_INVALID",
                "detail": "operations_json must be a JSON array",
            }
        )
    if not isinstance(flat_mats_raw, list):
        errors.append(
            {
                "path": "required_materials_json",
                "code": "MATERIALS_SHAPE_INVALID",
                "detail": "required_materials_json must be a JSON array",
            }
        )
    if errors:
        raise TemplateContractError(errors)

    # --- Pass 1: headers + collect known component_ids ---
    seen_ids: set = set()
    components_norm: List[Dict[str, Any]] = []
    for i, raw_c in enumerate(components_raw):
        hdr, hdr_errors = _validate_component_header(raw_c, i, seen_ids)
        errors.extend(hdr_errors)
        if hdr:
            components_norm.append(hdr)

    known_ids = {c["component_id"] for c in components_norm if c.get("component_id")}

    # --- Pass 2: nested ops + nested mats per component ---
    for i, comp in enumerate(components_norm):
        cid = comp.get("component_id") or ""
        cpath = f"components[{i}]"
        nested_ops_norm: List[Dict[str, Any]] = []
        nested_mats_norm: List[Dict[str, Any]] = []
        has_op = False
        has_mat = False

        for j, raw_op in enumerate(comp.get("operations") or []):
            # Default component_ref to the owning component_id so UI-side
            # drafts that forget to set it are still accepted — this matches
            # how the frontend serializes payloads.
            if isinstance(raw_op, dict) and not (raw_op.get("component_ref") or "").strip():
                raw_op = {**raw_op, "component_ref": cid}
            normalized, op_errors = _validate_operation(
                raw_op, cid, j, known_ids, cpath
            )
            errors.extend(op_errors)
            if normalized:
                nested_ops_norm.append(normalized)
                has_op = True

        for j, raw_mat in enumerate(comp.get("materials") or []):
            if isinstance(raw_mat, dict) and not (raw_mat.get("component_ref") or "").strip():
                raw_mat = {**raw_mat, "component_ref": cid}
            normalized, mat_errors = _validate_material(
                raw_mat, cid, j, known_ids, cpath
            )
            errors.extend(mat_errors)
            if normalized:
                nested_mats_norm.append(normalized)
                has_mat = True

        comp["operations"] = nested_ops_norm
        comp["materials"] = nested_mats_norm

        if not has_op:
            errors.append(
                {
                    "path": f"{cpath}.operations",
                    "code": "COMPONENT_HAS_NO_OPERATIONS",
                    "detail": "each component must declare at least one operation",
                }
            )
        if not has_mat:
            errors.append(
                {
                    "path": f"{cpath}.materials",
                    "code": "COMPONENT_HAS_NO_MATERIALS",
                    "detail": "each component must declare at least one material",
                }
            )

    # --- Pass 3: flat mirrors — every row must map to a known component_id ---
    for i, raw_op in enumerate(flat_ops_raw):
        if not isinstance(raw_op, dict):
            errors.append(
                {
                    "path": f"operations_json[{i}]",
                    "code": "OPERATION_SHAPE_INVALID",
                    "detail": "flat operations_json row must be an object",
                }
            )
            continue
        ref = str(raw_op.get("component_ref") or "").strip()
        if not ref or ref not in known_ids:
            errors.append(
                {
                    "path": f"operations_json[{i}].component_ref",
                    "code": "COMPONENT_REF_ORPHAN",
                    "detail": (
                        f"flat operation has component_ref '{ref}' which does not "
                        f"resolve to any component_id in components_json"
                    ),
                }
            )

    for i, raw_mat in enumerate(flat_mats_raw):
        if not isinstance(raw_mat, dict):
            errors.append(
                {
                    "path": f"required_materials_json[{i}]",
                    "code": "MATERIAL_SHAPE_INVALID",
                    "detail": "flat required_materials_json row must be an object",
                }
            )
            continue
        ref = str(raw_mat.get("component_ref") or "").strip()
        if not ref or ref not in known_ids:
            errors.append(
                {
                    "path": f"required_materials_json[{i}].component_ref",
                    "code": "COMPONENT_REF_ORPHAN",
                    "detail": (
                        f"flat material has component_ref '{ref}' which does not "
                        f"resolve to any component_id in components_json"
                    ),
                }
            )

    if errors:
        raise TemplateContractError(errors)

    # --- Emit canonical flat mirrors from the normalized hierarchical shape.
    # This guarantees the DB row is internally consistent: flat mirrors are
    # derived from components_norm, NOT trusted from the input (which could
    # disagree).
    flat_ops_out: List[Dict[str, Any]] = []
    flat_mats_out: List[Dict[str, Any]] = []
    for comp in components_norm:
        for op in comp["operations"]:
            flat_ops_out.append(dict(op))
        for m in comp["materials"]:
            flat_mats_out.append(dict(m))

    return {
        "components_json": json.dumps(components_norm, ensure_ascii=False),
        "operations_json": json.dumps(flat_ops_out, ensure_ascii=False),
        "required_materials_json": json.dumps(flat_mats_out, ensure_ascii=False),
    }