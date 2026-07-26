"""Read-only Form System/Product Truth readiness for letter group finishes."""

from __future__ import annotations

from typing import Any

from services.template_architecture_scope import VOLUMETRIC_V2_TEMPLATE_CODE


DOWNSTREAM_WRITE_INTENT = {
    "pricing": False,
    "quote": False,
    "order": False,
    "execution": False,
    "product_aggregate": False,
    "task_graph": False,
    "execution_plan": False,
    "db_write": False,
}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def _bool(value: Any) -> bool:
    return value is True


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def _read_positive_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _blocker(*, code: str, severity: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _finish_label(finish_type: str) -> str:
    labels = {
        "oracal_651": "Oracal 651",
        "oracal_641": "Oracal 641",
        "oracal_8500": "Oracal 8500",
        "white_aluminum": "Alb",
        "black_aluminum": "Negru",
        "mirror_gold": "Auriu",
        "mirror_silver": "Argintiu",
        "ral_paint": "Vopsit RAL",
        "oracal_wrapped": "Oracal 651",
        "none": "Fara finisaj",
    }
    return labels.get(finish_type, finish_type or "-")


def _face_label(row: dict[str, Any]) -> str:
    finish = _finish_label(_text(row.get("face_finish_type"), "none"))
    code = _text(row.get("face_oracal_code"))
    name = _text(row.get("face_oracal_name"))
    if code and name:
        return f"{finish} · {code} {name}"
    if code:
        return f"{finish} · {code}"
    return finish


def _return_label(row: dict[str, Any]) -> str:
    finish = _finish_label(_text(row.get("return_finish_type"), "none"))
    depth = _read_positive_number(row.get("return_depth_mm"))
    depth_label = f"{int(depth) if depth and depth.is_integer() else depth} mm" if depth is not None else "- mm"
    return f"{finish} · {depth_label}"


def _layers_by_key(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    setup = _as_dict(payload.get("layer_role_setup"))
    indexed: dict[str, dict[str, Any]] = {}
    for layer in _as_list(setup.get("layers")):
        row = _as_dict(layer)
        key = _text(row.get("layer_key"))
        if key:
            indexed[key] = row
    return indexed


def _analysis_layers_by_key(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    analysis = _as_dict(payload.get("svg_analysis_json"))
    indexed: dict[str, dict[str, Any]] = {}
    for layer in _as_list(analysis.get("layers")):
        row = _as_dict(layer)
        for key in (_text(row.get("id")), _text(row.get("name"))):
            if key:
                indexed[key] = row
    return indexed


def _svg_evidence(row: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    key = _text(row.get("group_key"))
    layer_name = _text(row.get("layer_name"))
    layers = _layers_by_key(payload)
    analysis_layers = _analysis_layers_by_key(payload)
    role_layer = layers.get(key) or layers.get(layer_name) or {}
    analysis_layer = analysis_layers.get(key) or analysis_layers.get(layer_name) or {}
    row_source_fill = _text(row.get("source_fill_color"))
    analysis_source_fill = _text(
        analysis_layer.get("colors", [None])[0]
        if isinstance(analysis_layer.get("colors"), list) and analysis_layer.get("colors")
        else None
    )
    source_fill = row_source_fill or analysis_source_fill
    analyzer_detected_group = bool(role_layer or analysis_layer)
    analyzer_detected_color = bool(analysis_source_fill)
    source_mismatch = not analyzer_detected_group or (
        bool(row_source_fill)
        and bool(analysis_source_fill)
        and row_source_fill.lower() != analysis_source_fill.lower()
    )
    return {
        "derived_from_svg": analyzer_detected_group or analyzer_detected_color,
        "source_fill_color": source_fill or None,
        "payload_source_fill_color": row_source_fill or None,
        "analyzer_source_fill_color": analysis_source_fill or None,
        "source_mismatch": source_mismatch,
        "analyzer_detected_group": analyzer_detected_group,
        "analyzer_detected_color": analyzer_detected_color,
        "analyzer_detected_oracal": False,
        "analyzer_detected_cant": False,
        "analyzer_detected_return_depth": False,
        "analyzer_detected_ral_or_white": False,
        "layer_role": role_layer.get("confirmed_role") or role_layer.get("auto_role"),
        "layer_role_confirmed": role_layer.get("confirmation_state") == "confirmed",
    }


def _face_finish(row: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    confirmed = _bool(row.get("confirmed"))
    source_type = "svg_nearest_color_mapping" if evidence.get("analyzer_detected_color") else "payload_persisted"
    state = "confirmed" if confirmed else "suggested" if source_type == "svg_nearest_color_mapping" else "hydrated"
    warnings: list[dict[str, str]] = []
    if evidence.get("source_mismatch"):
        warnings.append(
            _blocker(
                code="STALE_LETTER_GROUP_FINISH_ROWS",
                severity="blocker",
                message="Letter group finish row does not match the current SVG analyzer group/color evidence.",
            )
        )
    if source_type == "svg_nearest_color_mapping" and not confirmed:
        warnings.append(
            _blocker(
                code="FACE_ORACAL_NEAREST_MAPPING_NOT_CONFIRMED",
                severity="warning",
                message="Oracal color is derived from SVG fill nearest mapping and requires operator confirmation.",
            )
        )
    if _normalize(row.get("face_finish_type")) in {"oracal_651", "oracal_641", "oracal_8500"} and not _text(row.get("face_oracal_code")):
        warnings.append(
            _blocker(
                code="FACE_ORACAL_COLOR_MISSING",
                severity="blocker",
                message="Face Oracal finish requires a color code.",
            )
        )
    key = _text(row.get("group_key"), "unknown")
    return {
        "label": _face_label(row),
        "finish_type": row.get("face_finish_type"),
        "oracal_code": row.get("face_oracal_code"),
        "oracal_name": row.get("face_oracal_name"),
        "source_type": source_type,
        "state": state,
        "confirmed": confirmed,
        "product_truth_path": f"components.face_finish.letter_groups.{key}.face_finish",
        "warnings": warnings,
    }


def _return_cant(row: dict[str, Any]) -> dict[str, Any]:
    confirmed = _bool(row.get("confirmed"))
    depth = _read_positive_number(row.get("return_depth_mm"))
    warnings = [
        _blocker(
            code="RETURN_CANT_NOT_FROM_SVG",
            severity="warning",
            message="Return/cant value is not detected from SVG and must be operator-confirmed.",
        )
    ]
    if depth is None:
        warnings.append(
            _blocker(
                code="RETURN_CANT_DEPTH_MISSING",
                severity="blocker",
                message="Return/cant depth is missing for this letter group.",
            )
        )
    if not _text(row.get("return_finish_type")):
        warnings.append(
            _blocker(
                code="RETURN_CANT_FINISH_MISSING",
                severity="blocker",
                message="Return/cant finish is missing for this letter group.",
            )
        )
    key = _text(row.get("group_key"), "unknown")
    return {
        "label": _return_label(row),
        "finish_type": row.get("return_finish_type"),
        "return_oracal_code": row.get("return_oracal_code"),
        "return_oracal_name": row.get("return_oracal_name"),
        "return_depth_mm": row.get("return_depth_mm"),
        "source_type": "payload_hydrated_or_prior_state",
        "state": "confirmed" if confirmed else "hydrated",
        "confirmed": confirmed,
        "product_truth_path": f"components.return_cant.letter_groups.{key}.return_cant",
        "warnings": warnings,
    }


def _row_readiness(row: dict[str, Any], face: dict[str, Any], ret: dict[str, Any]) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    blockers.extend([warning for warning in face["warnings"] if warning["severity"] == "blocker"])
    blockers.extend([warning for warning in ret["warnings"] if warning["severity"] == "blocker"])
    if blockers:
        status = "blocked"
        reason = blockers[0]["code"].lower()
    elif not _bool(row.get("confirmed")):
        status = "partial"
        reason = "letter_group_not_confirmed"
        blockers.append(
            _blocker(
                code="LETTER_GROUP_FINISH_NOT_CONFIRMED",
                severity="warning",
                message="Letter group finish row is not operator-confirmed.",
            )
        )
    else:
        status = "ready"
        reason = "ready"
    is_ready = status == "ready"
    return {
        "status": status,
        "is_ready": is_ready,
        "reason": reason,
        "confirmed": _bool(row.get("confirmed")),
        "ready_for_product_definition": False,
        "ready_for_pricing": False,
        "ready_for_quote": False,
        "ready_for_order": False,
        "ready_for_execution": False,
        "blockers": blockers,
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ready = sum(1 for row in rows if row["product_truth_readiness"]["status"] == "ready")
    partial = sum(1 for row in rows if row["product_truth_readiness"]["status"] == "partial")
    blocked = sum(1 for row in rows if row["product_truth_readiness"]["status"] == "blocked")
    if blocked:
        status = "blocked"
        reason = "letter_group_finish_required_data_missing"
    elif partial:
        status = "partial"
        reason = "letter_group_finish_not_confirmed"
    elif ready and ready == len(rows):
        status = "ready"
        reason = "all_letter_group_finishes_ready"
    else:
        status = "empty"
        reason = "letter_group_finishes_missing"
    return {
        "status": status,
        "groups_count": len(rows),
        "ready_groups_count": ready,
        "partial_groups_count": partial,
        "blocked_groups_count": blocked,
        "face_suggestions_count": sum(1 for row in rows if row["face_finish"]["source_type"] == "svg_nearest_color_mapping"),
        "return_cant_from_svg_count": 0,
        "return_cant_hydrated_count": sum(1 for row in rows if row["return_cant"]["source_type"] == "payload_hydrated_or_prior_state"),
        "pricing_ready": False,
        "quote_ready": False,
        "order_ready": False,
        "execution_ready": False,
        "reason": reason,
    }


def build_letter_group_finish_readiness_from_workspace_payload(
    payload: dict[str, Any],
    root_template_code: str,
) -> dict[str, Any]:
    """Build a read-only readiness model for Vector Litere / letter group finishes."""
    finish = _as_dict(payload.get("finish_setup"))
    groups = [_as_dict(row) for row in _as_list(finish.get("letter_group_finishes"))]
    rows: list[dict[str, Any]] = []
    for row in groups:
        key = _text(row.get("group_key"))
        if not key:
            continue
        evidence = _svg_evidence(row, payload)
        face = _face_finish(row, evidence)
        ret = _return_cant(row)
        rows.append(
            {
                "group_key": key,
                "layer_name": _text(row.get("layer_name"), key),
                "role": "letter_group_finish",
                "parent_root_template_code": root_template_code,
                "owning_template_code": root_template_code,
                "owning_components": {
                    "face_finish": "finish_artwork",
                    "return_cant": "return_cant",
                    "component_mapping_status": "partial",
                },
                "no_separate_product": True,
                "no_component_root": True,
                "no_component_quote": True,
                "linked_logo_involvement": False,
                "svg_evidence": evidence,
                "face_finish": face,
                "return_cant": ret,
                "product_truth_readiness": _row_readiness(row, face, ret),
            }
        )
    return {
        "root_template_code": root_template_code,
        "section": "Vector Litere",
        "source": "finish_setup.letter_group_finishes",
        "letter_group_finish_readiness_summary": _summary(rows),
        "letter_group_finish_rows": rows,
        "downstream_write_intent": DOWNSTREAM_WRITE_INTENT.copy(),
        "warnings": [
            "SVG Analyzer detects groups/colors, not Oracal, cant, return depth, RAL, or white aluminum truth.",
            "finish_setup.confirmed is global and does not imply per-row confirmed Product Truth.",
        ],
        "read_only": True,
    }