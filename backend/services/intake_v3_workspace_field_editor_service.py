"""Intake V3 controlled field patch service — allowlist-based, preview-regenerating."""

from __future__ import annotations

import copy
from typing import Any

from data_models.intake_v3_contracts import (
    SUPPORT_MODE_NO_SHARED,
    SUPPORT_MODE_SHARED_PENDING,
)
from fastapi import HTTPException
from schemas.intake_v3 import (
    IntakeV3EditableFieldDefinition,
    IntakeV3EditableFieldsResponse,
    IntakeV3FieldPatch,
    IntakeV3FieldPatchItemResult,
    IntakeV3Workspace,
    SupportContext,
)

FORBIDDEN_FIELD_PATHS = frozenset(
    {
        "created_quote_id",
        "order_id",
        "quote_id",
        "execution_plan_id",
        "execution_task_id",
        "stock_movement_id",
        "inventory_mutation_allowed",
        "quote_creation_allowed",
        "order_creation_allowed",
        "execution_plan_creation_allowed",
        "employee_mobile_action_allowed",
        "production_handoff.preview_only",
        "production_handoff.task_seed",
        "employee_preview_seed.non_executable",
    }
)

FIELD_ALIASES: dict[str, str] = {
    "dimensions.width_mm": "client_request.width_mm",
    "dimensions.height_mm": "client_request.height_mm",
    "dimensions.depth_mm": "client_request.depth_mm",
    "finish_assignment.face_finish.material": "finish_assignment.face_finish.material_code",
    "finish_assignment.face_finish.roll_width_mm": "finish_assignment.face_finish.face_vinyl_roll_width_mm",
    "finish_assignment.return_finish.material": "finish_assignment.return_finish.material_code",
    "finish_assignment.return_finish.depth_mm": "finish_assignment.return_finish.return_depth_mm",
}

ALLOWED_CANONICAL_PATHS = frozenset(
    {
        "title",
        "client_request.width_mm",
        "client_request.height_mm",
        "client_request.depth_mm",
        "support_context.support_mode",
        "support_context.illuminated",
        "finish_assignment.face_finish.enabled",
        "finish_assignment.face_finish.finish_type",
        "finish_assignment.face_finish.material_code",
        "finish_assignment.face_finish.material_family",
        "finish_assignment.face_finish.color_code",
        "finish_assignment.face_finish.color_name",
        "finish_assignment.face_finish.face_vinyl_roll_width_mm",
        "finish_assignment.face_finish.confirmed",
        "finish_assignment.return_finish.finish_type",
        "finish_assignment.return_finish.return_depth_mm",
        "finish_assignment.return_finish.material_code",
        "finish_assignment.return_finish.material_family",
        "finish_assignment.return_finish.color_code",
        "finish_assignment.return_finish.color_name",
        "finish_assignment.return_finish.confirmed",
        "finish_assignment.backing_finish.material",
        "finish_assignment.backing_finish.thickness_mm",
        "finish_assignment.backing_finish.color",
        "finish_assignment.backing_finish.confirmed",
    }
)

FACE_FINISH_TYPES = frozenset(
    {"none", "white_face", "vinyl", "printed_vinyl", "oracal_8500", "other"}
)
RETURN_FINISH_TYPES = frozenset(
    {"none", "raw", "prefinished", "oracal_wrapped", "oracal_651", "vinyl", "painted", "other"}
)
SUPPORT_MODES = frozenset({SUPPORT_MODE_NO_SHARED, SUPPORT_MODE_SHARED_PENDING})


def canonical_field_path(field_path: str) -> str:
    path = field_path.strip()
    if path in FIELD_ALIASES:
        return FIELD_ALIASES[path]
    return path


def get_allowed_intake_v3_field_paths() -> list[str]:
    return sorted(ALLOWED_CANONICAL_PATHS | set(FIELD_ALIASES.keys()))


def get_editable_fields_metadata() -> IntakeV3EditableFieldsResponse:
    definitions = [
        IntakeV3EditableFieldDefinition(
            field_path="title",
            label="Draft title",
            field_type="string",
            description="Workspace draft label (record title, not payload).",
        ),
        IntakeV3EditableFieldDefinition(
            field_path="dimensions.width_mm",
            label="Width (mm)",
            field_type="number",
            min_value=0.01,
        ),
        IntakeV3EditableFieldDefinition(
            field_path="dimensions.height_mm",
            label="Height (mm)",
            field_type="number",
            min_value=0.01,
        ),
        IntakeV3EditableFieldDefinition(
            field_path="dimensions.depth_mm",
            label="Depth (mm)",
            field_type="number",
            min_value=0.01,
            required=False,
        ),
        IntakeV3EditableFieldDefinition(
            field_path="support_context.support_mode",
            label="Support mode",
            field_type="enum",
            enum_options=[SUPPORT_MODE_NO_SHARED, SUPPORT_MODE_SHARED_PENDING],
        ),
        IntakeV3EditableFieldDefinition(
            field_path="support_context.illuminated",
            label="Illuminated",
            field_type="boolean",
        ),
        IntakeV3EditableFieldDefinition(
            field_path="finish_assignment.face_finish.enabled",
            label="Face vinyl enabled",
            field_type="boolean",
        ),
        IntakeV3EditableFieldDefinition(
            field_path="finish_assignment.face_finish.finish_type",
            label="Face finish type",
            field_type="enum",
            enum_options=sorted(FACE_FINISH_TYPES),
        ),
        IntakeV3EditableFieldDefinition(
            field_path="finish_assignment.face_finish.material",
            label="Face material",
            field_type="string",
        ),
        IntakeV3EditableFieldDefinition(
            field_path="finish_assignment.face_finish.color_code",
            label="Face color code",
            field_type="string",
        ),
        IntakeV3EditableFieldDefinition(
            field_path="finish_assignment.face_finish.color_name",
            label="Face color name",
            field_type="string",
        ),
        IntakeV3EditableFieldDefinition(
            field_path="finish_assignment.face_finish.roll_width_mm",
            label="Face roll width (mm)",
            field_type="number",
            min_value=0.01,
            required=False,
        ),
        IntakeV3EditableFieldDefinition(
            field_path="finish_assignment.return_finish.finish_type",
            label="Return finish type",
            field_type="enum",
            enum_options=sorted(RETURN_FINISH_TYPES),
        ),
        IntakeV3EditableFieldDefinition(
            field_path="finish_assignment.return_finish.depth_mm",
            label="Return depth (mm)",
            field_type="number",
            min_value=0.01,
            required=False,
        ),
        IntakeV3EditableFieldDefinition(
            field_path="finish_assignment.return_finish.material",
            label="Return material",
            field_type="string",
        ),
        IntakeV3EditableFieldDefinition(
            field_path="finish_assignment.return_finish.color_code",
            label="Return color code",
            field_type="string",
        ),
        IntakeV3EditableFieldDefinition(
            field_path="finish_assignment.return_finish.color_name",
            label="Return color name",
            field_type="string",
        ),
        IntakeV3EditableFieldDefinition(
            field_path="finish_assignment.backing_finish.material",
            label="Backing material",
            field_type="string",
        ),
        IntakeV3EditableFieldDefinition(
            field_path="finish_assignment.backing_finish.thickness_mm",
            label="Backing thickness (mm)",
            field_type="number",
            min_value=0.01,
            required=False,
        ),
        IntakeV3EditableFieldDefinition(
            field_path="finish_assignment.backing_finish.color",
            label="Backing color",
            field_type="string",
            required=False,
        ),
    ]
    return IntakeV3EditableFieldsResponse(fields=definitions)


def resolve_workspace_support_context(workspace: IntakeV3Workspace) -> SupportContext:
    if workspace.support_context is not None:
        return workspace.support_context
    intent = (workspace.client_request.mounting_intent or "").lower()
    shared = "shared" in intent or ("suport" in intent and "comun" in intent)
    return SupportContext(shared_support=shared, illuminated=True)


def normalize_intake_v3_editable_payload(payload: dict[str, Any]) -> dict[str, Any]:
    data = copy.deepcopy(payload)
    if "support_context" not in data or not isinstance(data.get("support_context"), dict):
        intent = (data.get("client_request") or {}).get("mounting_intent", "")
        shared = isinstance(intent, str) and (
            "shared" in intent.lower() or ("suport" in intent.lower() and "comun" in intent.lower())
        )
        data["support_context"] = {"shared_support": shared, "illuminated": True}
    else:
        ctx = data["support_context"]
        if "illuminated" not in ctx:
            ctx["illuminated"] = True
        if "shared_support" not in ctx:
            ctx["shared_support"] = False
    if "finish_assignment" not in data:
        data["finish_assignment"] = {}
    if "client_request" not in data:
        data["client_request"] = {}
    return data


def _is_forbidden_path(path: str) -> bool:
    if path in FORBIDDEN_FIELD_PATHS:
        return True
    return any(path.startswith(f"{prefix}.") for prefix in FORBIDDEN_FIELD_PATHS)


def _validate_patch_value(canonical: str, value: Any) -> str | None:
    if canonical == "title":
        if not isinstance(value, str) or not value.strip():
            return "title must be a non-empty string"
        return None

    if canonical in {
        "client_request.width_mm",
        "client_request.height_mm",
    }:
        if not isinstance(value, (int, float)) or value <= 0:
            return f"{canonical} must be a positive number"
        return None

    if canonical == "client_request.depth_mm":
        if value is None:
            return None
        if not isinstance(value, (int, float)) or value <= 0:
            return "client_request.depth_mm must be a positive number when provided"
        return None

    if canonical == "support_context.support_mode":
        if value not in SUPPORT_MODES:
            return f"support_mode must be one of: {', '.join(sorted(SUPPORT_MODES))}"
        return None

    if canonical == "support_context.illuminated":
        if not isinstance(value, bool):
            return "support_context.illuminated must be boolean"
        return None

    if canonical.endswith(".confirmed") or canonical.endswith(".enabled"):
        if not isinstance(value, bool):
            return f"{canonical} must be boolean"
        return None

    if canonical == "finish_assignment.face_finish.finish_type":
        if value not in FACE_FINISH_TYPES:
            return f"Unsupported face finish type: {value}"
        return None

    if canonical == "finish_assignment.return_finish.finish_type":
        if value not in RETURN_FINISH_TYPES:
            return f"Unsupported return finish type: {value}"
        return None

    if canonical in {
        "finish_assignment.face_finish.face_vinyl_roll_width_mm",
        "finish_assignment.return_finish.return_depth_mm",
        "finish_assignment.backing_finish.thickness_mm",
    }:
        if value is None:
            return None
        if not isinstance(value, (int, float)) or value <= 0:
            return f"{canonical} must be a positive number when provided"
        return None

    if canonical.endswith(".material_code") or canonical.endswith(".material") or canonical.endswith(".color") or canonical.endswith(".color_code") or canonical.endswith(".color_name") or canonical.endswith(".material_family"):
        if value is None:
            return None
        if not isinstance(value, str):
            return f"{canonical} must be a string"
        return None

    return None


def validate_intake_v3_field_patch(patches: list[IntakeV3FieldPatch]) -> tuple[list[IntakeV3FieldPatchItemResult], list[IntakeV3FieldPatchItemResult]]:
    """All-or-nothing validation — any rejection blocks the whole batch."""
    applied: list[IntakeV3FieldPatchItemResult] = []
    rejected: list[IntakeV3FieldPatchItemResult] = []

    if not patches:
        rejected.append(
            IntakeV3FieldPatchItemResult(
                field_path="*",
                status="rejected",
                message="At least one patch is required",
            )
        )
        return applied, rejected

    for patch in patches:
        raw_path = patch.field_path.strip()
        canonical = canonical_field_path(raw_path)

        if _is_forbidden_path(raw_path) or _is_forbidden_path(canonical):
            rejected.append(
                IntakeV3FieldPatchItemResult(
                    field_path=raw_path,
                    status="rejected",
                    message="Forbidden field path",
                )
            )
            continue

        if canonical not in ALLOWED_CANONICAL_PATHS and raw_path not in FIELD_ALIASES:
            rejected.append(
                IntakeV3FieldPatchItemResult(
                    field_path=raw_path,
                    status="rejected",
                    message="Field path not in allowlist",
                )
            )
            continue

        error = _validate_patch_value(canonical, patch.value)
        if error:
            rejected.append(
                IntakeV3FieldPatchItemResult(
                    field_path=raw_path,
                    status="rejected",
                    message=error,
                )
            )
        else:
            applied.append(
                IntakeV3FieldPatchItemResult(
                    field_path=raw_path,
                    status="validated",
                    message="ok",
                )
            )

    if rejected:
        return [], rejected
    return applied, []


def _set_nested(data: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    current: dict[str, Any] = data
    for part in parts[:-1]:
        next_val = current.get(part)
        if not isinstance(next_val, dict):
            next_val = {}
            current[part] = next_val
        current = next_val
    current[parts[-1]] = value


def apply_intake_v3_field_patch(payload: dict[str, Any], patch: IntakeV3FieldPatch) -> dict[str, Any]:
    return apply_intake_v3_field_patches(payload, [patch])


def apply_intake_v3_field_patches(payload: dict[str, Any], patches: list[IntakeV3FieldPatch]) -> dict[str, Any]:
    data = normalize_intake_v3_editable_payload(payload)

    for patch in patches:
        canonical = canonical_field_path(patch.field_path)
        if canonical == "title":
            continue
        if canonical == "support_context.support_mode":
            shared = patch.value == SUPPORT_MODE_SHARED_PENDING
            _set_nested(data, "support_context.shared_support", shared)
            mounting = (
                "shared_support_pending"
                if shared
                else "no_shared_support"
            )
            _set_nested(data, "client_request.mounting_intent", mounting)
            continue
        if canonical == "support_context.illuminated":
            _set_nested(data, "support_context.illuminated", patch.value)
            continue
        _set_nested(data, canonical, patch.value)

    return data


def apply_validated_field_patches_or_raise(
    payload: dict[str, Any],
    patches: list[IntakeV3FieldPatch],
) -> tuple[dict[str, Any], list[IntakeV3FieldPatchItemResult], str | None]:
    """Validate all patches, apply if valid, return sanitized payload dict."""
    applied_meta, rejected = validate_intake_v3_field_patch(patches)
    if rejected:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "field_patch_rejected",
                "rejected_patches": [item.model_dump() for item in rejected],
            },
        )

    data = apply_intake_v3_field_patches(payload, patches)
    from services.intake_v3_workspace_service import sanitize_intake_v3_workspace_payload

    workspace = sanitize_intake_v3_workspace_payload(data)
    title_patch = next((p for p in patches if canonical_field_path(p.field_path) == "title"), None)
    new_title = title_patch.value.strip() if title_patch and isinstance(title_patch.value, str) else None
    return workspace.model_dump(mode="json"), applied_meta, new_title
