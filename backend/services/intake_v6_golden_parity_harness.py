"""Build 1 — Intake V6 golden reference parity harness (read-only compare helpers).

Does not change operator behavior, formulas, prices, or schema.
Additive provenance / contract metadata only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "intake_v6_golden_gradi"
CONTRACT_VERSION = "intake_v6_golden_gradi_v1"
TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2"

# Historical golden workspace — read-only reference; never mutate in harness.
HISTORICAL_GOLDEN_WORKSPACE_ID = "4888fddb-5d9f-46cb-9bcc-5dd3ed1263b1"
HISTORICAL_GOLDEN_DISPLAY_CODE = "IV6-C8066690"

INTERFACE_FACE_CANT = {
    "interface_id": "RETURN_FACE_BONDING",
    "components": ["FACE", "CANT"],
    "material_code": "MAT-ADEZIV-CANT-LITERE",
    "material_row_key": "adhesive_return_to_face",
    "operation_codes": ["RETURN_PROFILE_FACE_BONDING", "return_face_bonding"],
    "current_owner": "modelare_cant",
    "target_owner": "interface:FACE+CANT",
    "build1_behavior": "full_product_output_unchanged",
    "build3_isolation": "cant_only_must_silence_adhesive_and_bonding",
}


def fixture_path(name: str) -> Path:
    return FIXTURE_DIR / name


def load_json_fixture(name: str) -> Any:
    path = fixture_path(name)
    return json.loads(path.read_text(encoding="utf-8"))


def load_golden_workspace_payload(*, include_analysis: bool = True) -> dict[str, Any]:
    payload = load_json_fixture("workspace_payload.golden.json")
    if include_analysis:
        payload = dict(payload)
        payload["svg_analysis_json"] = load_json_fixture("svg_analysis_json.json")
    return payload


def extract_svg_facts(svg_analysis_json: dict[str, Any], layer_role_setup: dict[str, Any] | None = None) -> dict[str, Any]:
    layers = svg_analysis_json.get("layers") if isinstance(svg_analysis_json.get("layers"), list) else []
    colors = svg_analysis_json.get("colors") if isinstance(svg_analysis_json.get("colors"), dict) else {}
    unique = colors.get("unique") if isinstance(colors.get("unique"), list) else []
    geometry = svg_analysis_json.get("geometry") if isinstance(svg_analysis_json.get("geometry"), dict) else {}
    document = svg_analysis_json.get("document") if isinstance(svg_analysis_json.get("document"), dict) else {}

    auto_buckets: dict[str, int] = {}
    layer_ids: list[str] = []
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        lid = str(layer.get("id") or "")
        if lid:
            layer_ids.append(lid)
        role = str(layer.get("autoRole") or layer.get("auto_role") or "unknown")
        auto_buckets[role] = auto_buckets.get(role, 0) + 1

    confirmed_buckets: dict[str, int] = {}
    confirmation_status = None
    if isinstance(layer_role_setup, dict):
        confirmation_status = layer_role_setup.get("confirmation_status")
        for entry in layer_role_setup.get("layers") or []:
            if not isinstance(entry, dict):
                continue
            role = str(entry.get("confirmed_role") or entry.get("auto_role") or "unknown")
            confirmed_buckets[role] = confirmed_buckets.get(role, 0) + 1

    return {
        "schemaVersion": svg_analysis_json.get("schemaVersion"),
        "layers_count": len(layers),
        "layer_ids": layer_ids,
        "colors_unique_count": len(unique),
        "colors_unique": list(unique),
        "closed_subpath_count": geometry.get("closedSubPathCount"),
        "subpath_count": geometry.get("subPathCount"),
        "width_mm": document.get("widthMm"),
        "height_mm": document.get("heightMm"),
        "auto_role_buckets": auto_buckets,
        "confirmation_status": confirmation_status,
        "confirmed_role_buckets": confirmed_buckets,
        "acm_declared": "support_panel" in auto_buckets,
    }


def compare_svg_facts(actual: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    """Return mismatch messages; empty list means parity."""
    mismatches: list[str] = []
    report = expected.get("report") or expected
    tol = float(report.get("dim_tolerance_mm") or expected.get("dim_tolerance_mm") or 1.0)

    def _eq(key: str, left: Any, right: Any) -> None:
        if left != right:
            mismatches.append(f"{key}: actual={left!r} expected={right!r}")

    _eq("layers_count", actual.get("layers_count"), report.get("layers_count"))
    _eq("colors_unique_count", actual.get("colors_unique_count"), report.get("colors_unique_count"))
    _eq("closed_subpath_count", actual.get("closed_subpath_count"), report.get("closed_subpath_count"))
    _eq("subpath_count", actual.get("subpath_count"), report.get("subpath_count"))
    _eq("layer_ids", actual.get("layer_ids"), report.get("layer_ids"))
    _eq("colors_unique", actual.get("colors_unique"), report.get("colors_unique"))
    _eq("auto_role_buckets", actual.get("auto_role_buckets"), report.get("auto_role_buckets"))

    for dim in ("width_mm", "height_mm"):
        a = actual.get(dim)
        e = report.get(dim)
        if a is None or e is None:
            mismatches.append(f"{dim}: missing actual={a!r} expected={e!r}")
            continue
        if abs(float(a) - float(e)) > tol:
            mismatches.append(f"{dim}: actual={a} expected={e} tol={tol}")

    if report.get("acm_declared") is False and actual.get("acm_declared"):
        mismatches.append("acm_declared: analyzer emitted support_panel but golden forbids ACM")

    op = expected.get("operator_confirm") or {}
    if op:
        _eq("confirmation_status", actual.get("confirmation_status"), op.get("confirmation_status"))
        _eq(
            "confirmed_role_buckets",
            actual.get("confirmed_role_buckets"),
            op.get("confirmed_role_buckets"),
        )

    for forbidden in report.get("forbidden_auto_roles") or []:
        if forbidden in (actual.get("auto_role_buckets") or {}):
            mismatches.append(f"forbidden auto role present: {forbidden}")

    return mismatches


def compare_quote_geometry(
    actual: dict[str, Any],
    expected: dict[str, Any],
    *,
    keys: list[str] | None = None,
    float_tol: float = 1e-4,
) -> list[str]:
    keys = keys or [
        "width_mm",
        "height_mm",
        "letter_count",
        "real_letters_count",
        "face_area_m2",
        "artwork_area_m2",
        "letter_perimeter_m",
        "cutting_contours_count",
        "inner_holes_count",
        "face_cutting_perimeter_ml",
        "confirmed",
        "geometry_source",
    ]
    mismatches: list[str] = []
    for key in keys:
        a = actual.get(key)
        e = expected.get(key)
        if isinstance(a, float) or isinstance(e, float):
            if a is None or e is None or abs(float(a) - float(e)) > float_tol:
                mismatches.append(f"{key}: actual={a!r} expected={e!r}")
        elif a != e:
            mismatches.append(f"{key}: actual={a!r} expected={e!r}")
    return mismatches


def material_codes(aggregate: Any) -> set[str]:
    materials = getattr(aggregate, "materials", None)
    if materials is None and isinstance(aggregate, dict):
        materials = aggregate.get("materials")
    codes: set[str] = set()
    for row in materials or []:
        if hasattr(row, "material_code"):
            code = getattr(row, "material_code", None)
        elif isinstance(row, dict):
            code = row.get("material_code") or row.get("code") or row.get("id")
        else:
            code = None
        if code:
            codes.add(str(code))
    return codes


def operation_codes(aggregate: Any) -> set[str]:
    operations = getattr(aggregate, "operations", None)
    if operations is None and isinstance(aggregate, dict):
        operations = aggregate.get("operations")
    codes: set[str] = set()
    for row in operations or []:
        if hasattr(row, "operation_code"):
            code = getattr(row, "operation_code", None) or getattr(row, "code", None)
        elif isinstance(row, dict):
            code = row.get("operation_code") or row.get("code") or row.get("key") or row.get("id")
        else:
            code = None
        if code:
            codes.add(str(code))
    return codes


def fingerprint_commercial_lines(lines: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in lines or []:
        if hasattr(line, "model_dump"):
            data = line.model_dump()
        elif isinstance(line, dict):
            data = line
        else:
            continue
        code = data.get("code") or data.get("line_code") or data.get("rule_code")
        out.append(
            {
                "code": code,
                "quantity": data.get("quantity"),
                "unit_price": data.get("unit_price"),
                "subtotal": data.get("subtotal") if "subtotal" in data else data.get("line_total"),
                "unit": data.get("unit"),
            }
        )
    out.sort(key=lambda row: str(row.get("code") or ""))
    return out


def compare_commercial_fingerprints(
    actual: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    *,
    qty_tol: float = 1e-4,
    money_tol: float = 0.01,
) -> list[str]:
    mismatches: list[str] = []
    a_map = {str(r.get("code")): r for r in actual if r.get("code")}
    e_map = {str(r.get("code")): r for r in expected if r.get("code")}
    if set(a_map) != set(e_map):
        missing = sorted(set(e_map) - set(a_map))
        extra = sorted(set(a_map) - set(e_map))
        if missing:
            mismatches.append(f"missing line codes: {missing}")
        if extra:
            mismatches.append(f"extra line codes: {extra}")
    for code in sorted(set(a_map) & set(e_map)):
        a = a_map[code]
        e = e_map[code]
        for field, tol in (("quantity", qty_tol), ("unit_price", money_tol), ("subtotal", money_tol)):
            av = a.get(field)
            ev = e.get(field)
            if av is None and ev is None:
                continue
            if av is None or ev is None:
                mismatches.append(f"{code}.{field}: actual={av!r} expected={ev!r}")
                continue
            try:
                if abs(float(av) - float(ev)) > tol:
                    mismatches.append(f"{code}.{field}: actual={av} expected={ev}")
            except (TypeError, ValueError):
                if av != ev:
                    mismatches.append(f"{code}.{field}: actual={av!r} expected={ev!r}")
    return mismatches


def selected_module_codes(product_definition: Any) -> list[str]:
    modules = getattr(product_definition, "selected_modules", None)
    if modules is None and isinstance(product_definition, dict):
        modules = product_definition.get("selected_modules")
    codes: list[str] = []
    for mod in modules or []:
        if hasattr(mod, "module_code"):
            codes.append(str(mod.module_code))
        elif isinstance(mod, dict) and mod.get("module_code"):
            codes.append(str(mod["module_code"]))
    return sorted(codes)


def geometry_inputs_from_pd(product_definition: Any) -> dict[str, Any]:
    geom = getattr(product_definition, "geometry_inputs", None)
    if geom is None and isinstance(product_definition, dict):
        geom = product_definition.get("geometry_inputs")
    if hasattr(geom, "model_dump"):
        return geom.model_dump()
    if isinstance(geom, dict):
        return geom
    return {}


def assert_face_cant_interface_present(aggregate: Any) -> list[str]:
    """Full-product must still emit adhesive + bonding; documents Build 3 target only."""
    mats = material_codes(aggregate)
    ops = operation_codes(aggregate)
    issues: list[str] = []
    if INTERFACE_FACE_CANT["material_code"] not in mats:
        issues.append(f"missing adhesive material {INTERFACE_FACE_CANT['material_code']}")
    if not any(code in ops for code in INTERFACE_FACE_CANT["operation_codes"]):
        issues.append(f"missing bonding ops {INTERFACE_FACE_CANT['operation_codes']}")
    return issues


def review_contract_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """Capture golden Review contract facts (no UI layout change)."""
    svg_source = payload.get("svg_source") if isinstance(payload.get("svg_source"), dict) else {}
    lrs = payload.get("layer_role_setup") if isinstance(payload.get("layer_role_setup"), dict) else {}
    qg = payload.get("quote_geometry") if isinstance(payload.get("quote_geometry"), dict) else {}
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
    composition = payload.get("product_composition_confirmed")
    return {
        "contract_version": "intake_v6_golden_review_v1",
        "file_identity": {
            "file_name": svg_source.get("file_name"),
            "file_size_bytes": svg_source.get("file_size_bytes"),
            "file_hash": svg_source.get("file_hash"),
        },
        "layers_confirmed": lrs.get("confirmation_status"),
        "layer_count": len(lrs.get("layers") or []),
        "composition_confirmed": bool(composition),
        "geometry": {
            "width_mm": qg.get("width_mm"),
            "height_mm": qg.get("height_mm"),
            "letter_count": qg.get("letter_count"),
            "letter_perimeter_m": qg.get("letter_perimeter_m"),
            "face_area_m2": qg.get("face_area_m2"),
        },
        "operator_intent": {
            "illuminated": finish.get("illuminated"),
            "return_depth_mm": finish.get("return_depth_mm"),
            "face_finish_type": finish.get("face_finish_type"),
            "backing_mode": finish.get("backing_mode"),
            "mounting_template_enabled": finish.get("mounting_template_enabled"),
        },
        "cpp_boundary": {
            "intake_is_money_authority": False,
            "dry_run_required": True,
        },
    }
