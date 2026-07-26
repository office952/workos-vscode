"""Read-only runtime extraction for linked template segments."""

from __future__ import annotations

from typing import Any

from services.intake_v6_layer_identity import (
    canonical_candidate_keys,
    canonical_segment_key,
    index_layers_by_identity,
    resolve_binding_row,
    resolve_finish_row,
)
from services.template_architecture_scope import VOLUMETRIC_LOGO_TEMPLATE_CODE, VOLUMETRIC_V2_TEMPLATE_CODE

LOGO_SEGMENT_ROLE = "linked_logo_segment"
LOGO_LAYER_ROLES = {"printed_artwork", "logo"}


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
    return str(value or "").strip().upper()


def _is_logoish(value: Any) -> bool:
    text = str(value or "").lower()
    return "logo" in text or "sigla" in text or "siglă" in text or "emblem" in text


def _by_layer_key(items: list[Any]) -> dict[str, tuple[int, dict[str, Any]]]:
    indexed: dict[str, tuple[int, dict[str, Any]]] = {}
    for index, item in enumerate(items):
        data = _as_dict(item)
        key = _text(data.get("layer_key"))
        if key:
            indexed[key] = (index, data)
    return indexed


def _linked_logo_template(linked_template_composition: dict[str, Any]) -> dict[str, Any] | None:
    for item in _as_list(linked_template_composition.get("linked_templates")):
        linked = _as_dict(item)
        if (
            _normalize(linked.get("template_code")) == _normalize(VOLUMETRIC_LOGO_TEMPLATE_CODE)
            and linked.get("composition_role") == LOGO_SEGMENT_ROLE
        ):
            return linked
    return None


def _empty_result(*, root_template_code: str, reason: str) -> dict[str, Any]:
    return {
        "root_template_code": root_template_code,
        "composition_mode": "not_applicable",
        "segments": [],
        "summary": {
            "status": reason,
            "segments_count": 0,
            "confirmed_segments_count": 0,
            "suggested_binding_count": 0,
            "missing_finish_count": 0,
            "missing_binding_count": 0,
            "root_offerable_activation": False,
            "separate_quote_activation": False,
            "task_graph_activation": False,
            "product_truth_readiness_status": "not_applicable",
        },
    }


def _candidate_keys(
    *,
    layers_by_key: dict[str, tuple[int, dict[str, Any]]],
    bindings_by_key: dict[str, tuple[int, dict[str, Any]]],
    finishes_by_key: dict[str, tuple[int, dict[str, Any]]],
    linked_template_code: str,
) -> list[str]:
    keys: set[str] = set()
    for key, (_, binding) in bindings_by_key.items():
        if _normalize(binding.get("target_template_code")) == _normalize(linked_template_code):
            keys.add(key)
    for key, (_, layer) in layers_by_key.items():
        role = layer.get("confirmed_role") or layer.get("auto_role")
        if role in LOGO_LAYER_ROLES and (_is_logoish(key) or _is_logoish(layer.get("layer_name"))):
            keys.add(key)
    for key, (_, finish) in finishes_by_key.items():
        if _is_logoish(key) or _is_logoish(finish.get("layer_name")):
            keys.add(key)
    return sorted(keys)


def _source_paths(
    *,
    key: str,
    layer_index: int | None,
    binding_index: int | None,
    finish_index: int | None,
) -> list[str]:
    paths = []
    if layer_index is not None:
        paths.append(f"payload.layer_role_setup.layers[{layer_index}:{key}]")
    if binding_index is not None:
        paths.append(f"payload.layer_role_setup.layer_bindings[{binding_index}:{key}]")
    if finish_index is not None:
        paths.append(f"payload.finish_setup.artwork_finishes[{finish_index}:{key}]")
    return paths


def _segment_state(layer: dict[str, Any], finish: dict[str, Any]) -> str:
    if layer.get("confirmation_state") == "confirmed" and _bool(finish.get("confirmed")):
        return "confirmed"
    if not finish:
        return "missing_finish"
    if layer.get("confirmation_state") == "confirmed":
        return "layer_confirmed_finish_pending"
    return "needs_operator_confirmation"


def _finish_payload(finish: dict[str, Any]) -> dict[str, Any]:
    return {
        "execution_type": finish.get("execution_type"),
        "color_mode": finish.get("color_mode"),
        "print_transparency": finish.get("print_transparency"),
        "return_finish_type": finish.get("return_finish_type"),
        "return_depth_mm": finish.get("return_depth_mm"),
        "confirmed": _bool(finish.get("confirmed")),
    }


def _readiness_blocker(*, code: str, severity: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _product_truth_readiness(segment: dict[str, Any]) -> dict[str, Any]:
    binding_status = _text(segment.get("binding_status"), "missing")
    finish = _as_dict(segment.get("finish"))
    finish_confirmed = _bool(finish.get("confirmed"))
    layer_role_confirmed = segment.get("confirmed_role") in LOGO_LAYER_ROLES
    template_binding_confirmed = binding_status == "confirmed"
    blockers: list[dict[str, str]] = []

    status = "ready"
    reason = "ready"
    if not layer_role_confirmed:
        status = "blocked"
        reason = "layer_role_not_confirmed"
        blockers.append(
            _readiness_blocker(
                code="LINKED_SEGMENT_LAYER_ROLE_NOT_CONFIRMED",
                severity="blocker",
                message="Linked segment layer role is not operator-confirmed.",
            )
        )
    if binding_status == "missing":
        status = "blocked"
        reason = "missing_linked_template_binding"
        blockers.append(
            _readiness_blocker(
                code="LINKED_TEMPLATE_BINDING_MISSING",
                severity="blocker",
                message="Linked segment has no linked template binding in runtime payload.",
            )
        )
    if not finish_confirmed:
        status = "blocked"
        reason = "missing_finish"
        blockers.append(
            _readiness_blocker(
                code="LINKED_SEGMENT_FINISH_MISSING",
                severity="blocker",
                message="Linked segment artwork finish is missing or not confirmed.",
            )
        )
    if status != "blocked" and binding_status == "suggested":
        status = "partial"
        reason = "template_binding_suggested"
        blockers.append(
            _readiness_blocker(
                code="LINKED_TEMPLATE_BINDING_SUGGESTED",
                severity="warning",
                message="Logo segment is confirmed as artwork, but linked template binding remains suggested.",
            )
        )

    is_ready = status == "ready"
    return {
        "status": status,
        "is_ready": is_ready,
        "reason": reason,
        "ready_for_pricing": False,
        "ready_for_quote": False,
        "ready_for_order": False,
        "ready_for_execution": False,
        "confirmed_as_artwork": layer_role_confirmed,
        "finish_confirmed": finish_confirmed,
        "layer_role_confirmed": layer_role_confirmed,
        "template_binding_confirmed": template_binding_confirmed,
        "binding_status": binding_status,
        "required_confirmation": None if is_ready else "confirm_linked_template_binding",
        "product_truth_path": segment.get("product_truth_path"),
        "blockers": blockers,
    }


def _product_truth_readiness_summary(segments: list[dict[str, Any]]) -> dict[str, Any]:
    readiness_items = [_as_dict(segment.get("product_truth_readiness")) for segment in segments]
    ready_count = sum(1 for item in readiness_items if item.get("status") == "ready")
    partial_count = sum(1 for item in readiness_items if item.get("status") == "partial")
    blocked_count = sum(1 for item in readiness_items if item.get("status") == "blocked")
    warnings_count = sum(
        1
        for item in readiness_items
        for blocker in _as_list(item.get("blockers"))
        if _as_dict(blocker).get("severity") == "warning"
    )
    if blocked_count:
        status = "blocked"
        reason = "linked_segment_required_data_missing"
    elif partial_count:
        status = "partial"
        reason = "linked_template_binding_suggested"
    elif ready_count and ready_count == len(segments):
        status = "ready"
        reason = "all_linked_segments_ready"
    else:
        status = "not_applicable"
        reason = "no_runtime_segments"

    return {
        "status": status,
        "ready_segments_count": ready_count,
        "partial_segments_count": partial_count,
        "blocked_segments_count": blocked_count,
        "pricing_ready": False,
        "quote_ready": False,
        "order_ready": False,
        "execution_ready": False,
        "reason": reason,
        "warnings_count": warnings_count,
    }


def extract_linked_template_segments_from_workspace_payload(
    *,
    root_template_code: str,
    workspace_payload: dict[str, Any],
    linked_template_composition: dict[str, Any],
) -> dict[str, Any]:
    """Extract runtime linked segment rows without writes or downstream activation."""
    composition = _as_dict(linked_template_composition)
    if _normalize(root_template_code) != _normalize(VOLUMETRIC_V2_TEMPLATE_CODE):
        return _empty_result(root_template_code=root_template_code, reason="non_linked_root")
    if _normalize(composition.get("root_template_code")) != _normalize(root_template_code):
        return _empty_result(root_template_code=root_template_code, reason="composition_root_mismatch")

    linked_logo = _linked_logo_template(composition)
    if linked_logo is None:
        return _empty_result(root_template_code=root_template_code, reason="linked_logo_template_missing")

    payload = _as_dict(workspace_payload)
    layer_role_setup = _as_dict(payload.get("layer_role_setup"))
    finish_setup = _as_dict(payload.get("finish_setup"))
    layers_by_key = _by_layer_key(_as_list(layer_role_setup.get("layers")))
    bindings_by_key = _by_layer_key(_as_list(layer_role_setup.get("layer_bindings")))
    finishes_by_key = _by_layer_key(_as_list(finish_setup.get("artwork_finishes")))

    linked_template_code = _text(linked_logo.get("template_code"), VOLUMETRIC_LOGO_TEMPLATE_CODE)
    quote_policy = _text(linked_logo.get("quote_policy"), "no_separate_quote")
    task_policy = _text(linked_logo.get("task_merge_policy"), "emit_intent_merge_later_no_task_graph_now")
    keys = canonical_candidate_keys(
        layers=_as_list(layer_role_setup.get("layers")),
        bindings=_as_list(layer_role_setup.get("layer_bindings")),
        finishes=_as_list(finish_setup.get("artwork_finishes")),
        linked_template_code=linked_template_code,
        logo_layer_roles=LOGO_LAYER_ROLES,
        is_logoish=_is_logoish,
    )

    layers_by_identity = index_layers_by_identity(_as_list(layer_role_setup.get("layers")))

    segments: list[dict[str, Any]] = []
    for key in keys:
        layer = layers_by_identity.get(key, {})
        layer_index = None
        for index, item in enumerate(_as_list(layer_role_setup.get("layers"))):
            item_key = _text(_as_dict(item).get("layer_key") or _as_dict(item).get("layer_id"))
            if item_key and canonical_segment_key(layer_key=item_key, layer=_as_dict(item)) == key:
                layer_index = index
                layer = _as_dict(item)
                break
        binding_index, binding = resolve_binding_row(
            key=key,
            bindings_by_key=bindings_by_key,
            layers_by_identity=layers_by_identity,
        )
        finish_index, finish = resolve_finish_row(
            key=key,
            finishes_by_key=finishes_by_key,
            layers_by_identity=layers_by_identity,
        )
        binding_status = _text(binding.get("binding_status"), "missing")
        warnings: list[str] = ["linked_logo_template_is_child_only_not_root_offerable"]
        if binding_status == "suggested":
            warnings.append("binding_status_suggested_requires_product_truth_confirmation_boundary")
        if not binding:
            warnings.append("linked_template_binding_missing")
        if not finish:
            warnings.append("artwork_finish_missing")

        segment = {
            "segment_key": key,
            "instance_id": key,
            "display_name": _text(layer.get("layer_name"), _text(finish.get("layer_name"), key)),
            "parent_root_template_code": root_template_code,
            "owning_template_code": linked_template_code,
            "composition_role": _text(linked_logo.get("composition_role"), LOGO_SEGMENT_ROLE),
            "layer_role": _text(layer.get("auto_role"), _text(binding.get("suggested_semantic_role"), "unknown")),
            "confirmed_role": layer.get("confirmed_role"),
            "binding_status": binding_status,
            "binding_reason": binding.get("binding_reason"),
            "source": "runtime_workspace_payload",
            "source_paths": _source_paths(
                key=key,
                layer_index=layer_index,
                binding_index=binding_index,
                finish_index=finish_index,
            ),
            "state": _segment_state(layer, finish),
            "product_truth_path": f"linked_templates.{linked_template_code}.segments.{key}",
            "finish": _finish_payload(finish),
            "quote_policy": quote_policy,
            "task_policy": task_policy,
            "warnings": warnings,
        }
        segment["product_truth_readiness"] = _product_truth_readiness(segment)
        segments.append(segment)

    suggested_binding_count = sum(1 for segment in segments if segment["binding_status"] == "suggested")
    missing_finish_count = sum(1 for segment in segments if not segment["finish"]["confirmed"])
    missing_binding_count = sum(1 for segment in segments if segment["binding_status"] == "missing")
    confirmed_segments_count = sum(1 for segment in segments if segment["state"] == "confirmed")
    readiness_status = "partial_binding_suggested" if suggested_binding_count else "segments_confirmed"
    if not segments:
        readiness_status = "no_runtime_segments"
    elif missing_finish_count or missing_binding_count:
        readiness_status = "partial_runtime_mapping"

    return {
        "root_template_code": root_template_code,
        "composition_mode": _text(composition.get("composition_mode"), "root_with_linked_segments"),
        "segments": segments,
        "product_truth_readiness_summary": _product_truth_readiness_summary(segments),
        "summary": {
            "status": "ok",
            "segments_count": len(segments),
            "confirmed_segments_count": confirmed_segments_count,
            "suggested_binding_count": suggested_binding_count,
            "missing_finish_count": missing_finish_count,
            "missing_binding_count": missing_binding_count,
            "root_offerable_activation": False,
            "separate_quote_activation": False,
            "task_graph_activation": False,
            "product_truth_readiness_status": readiness_status,
        },
    }