"""Resolve ProductSystem template metadata for Intake V4 workspaces."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_template_module_links import ProductTemplateModuleLink
from models.product_templates import Product_templates
from schemas.intake_v4 import (
    IntakeV4ProductSystemModuleLink,
    IntakeV4ProductSystemBindingResponse,
    IntakeV4ProductSystemOperation,
    IntakeV4TaskPreviewItem,
)


@dataclass(frozen=True)
class ResolvedProductTemplate:
    template_code: str
    template_id: int
    template_label: str
    product_family: str | None
    product_family_name: str
    template_active: bool
    components: list[dict[str, Any]]
    operations: list[dict[str, Any]]


def _json_loads(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _normalize_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


async def list_template_module_links(
    db: AsyncSession,
    template: ResolvedProductTemplate,
) -> list[IntakeV4ProductSystemModuleLink]:
    result = await db.execute(
        select(ProductTemplateModuleLink).where(
            ProductTemplateModuleLink.parent_template_code == template.template_code,
            ProductTemplateModuleLink.active.is_(True),
        )
    )
    rows = list(result.scalars().all())
    if not rows:
        return []

    module_codes = sorted({str(row.module_template_code) for row in rows if row.module_template_code})
    module_labels: dict[str, str] = {}
    if module_codes:
        template_result = await db.execute(
            select(Product_templates).where(Product_templates.template_code.in_(module_codes))
        )
        for module in template_result.scalars().all():
            module_labels[str(module.template_code)] = str(module.family_name or module.template_code)

    items: list[IntakeV4ProductSystemModuleLink] = []
    for row in rows:
        items.append(
            IntakeV4ProductSystemModuleLink(
                module_template_id=int(row.module_template_id) if row.module_template_id is not None else None,
                module_template_code=str(row.module_template_code),
                module_template_label=module_labels.get(str(row.module_template_code)),
                relation_type=str(row.relation_type or "optional_addon"),
                trigger_field=str(row.trigger_field),
                trigger_value=_json_loads(row.trigger_value_json, None),
                input_mapping=_normalize_object(_json_loads(row.input_mapping_json, {})),
                default_values=_normalize_object(_json_loads(row.default_values_json, {})),
                pricing_mode=str(row.pricing_mode or "separate_quote_line"),
                execution_mode=str(row.execution_mode or "linked_child_work"),
                active=bool(row.active),
                notes=row.notes,
            )
        )
    return items


async def resolve_product_template_or_raise(
    db: AsyncSession,
    template_code: str,
) -> ResolvedProductTemplate:
    code = template_code.strip()
    if not code:
        raise HTTPException(status_code=422, detail={"error": "missing_template_code"})

    result = await db.execute(
        select(Product_templates).where(Product_templates.template_code == code)
    )
    row = result.scalar_one_or_none()
    if row is None:
        result = await db.execute(
            select(Product_templates).where(Product_templates.template_code == code.upper())
        )
        row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "product_system_template_not_found",
                "template_code": code,
            },
        )

    components = _json_loads(row.components_json, [])
    if not isinstance(components, list):
        components = []

    operations = _json_loads(row.operations_json, [])
    if not isinstance(operations, list):
        operations = []

    return ResolvedProductTemplate(
        template_code=row.template_code,
        template_id=int(row.id),
        template_label=row.family_name or row.template_code,
        product_family=row.family_id,
        product_family_name=row.family_name,
        template_active=bool(row.active),
        components=components,
        operations=operations,
    )


def list_template_operations(template: ResolvedProductTemplate) -> list[IntakeV4ProductSystemOperation]:
    ops: list[IntakeV4ProductSystemOperation] = []
    for raw in template.operations:
        if not isinstance(raw, dict):
            continue
        code = str(raw.get("code") or "").strip()
        if not code:
            continue
        seq_raw = raw.get("sequence")
        try:
            sequence = int(seq_raw) if seq_raw is not None else 999
        except (TypeError, ValueError):
            sequence = 999
        ops.append(
            IntakeV4ProductSystemOperation(
                code=code,
                label=str(raw.get("label") or code),
                workcenter=str(raw.get("workcenter") or "") or None,
                sequence=sequence,
                component_ref=str(raw.get("component_ref") or "") or None,
                active=True,
            )
        )
    ops.sort(key=lambda item: (item.sequence, item.code))
    return ops


def _finish_context(finish_setup: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(finish_setup, dict):
        return {
            "face_finish_type": "none",
            "return_finish_type": "none",
            "illuminated": True,
            "lighting_system_type": None,
            "return_depth_mm": None,
        }
    face = finish_setup.get("face_finish_type")
    ret = finish_setup.get("return_finish_type")
    return {
        "face_finish_type": str(face).strip() if face else "none",
        "return_finish_type": str(ret).strip() if ret else "none",
        "illuminated": finish_setup.get("illuminated") is not False,
        "lighting_system_type": finish_setup.get("lighting_system_type"),
        "return_depth_mm": finish_setup.get("return_depth_mm"),
    }


def _gate_active(gate: Any, ctx: dict[str, Any]) -> tuple[bool, str | None]:
    if not isinstance(gate, dict) or not gate:
        return True, None

    expected = gate.get("face_finish_type")
    if expected is not None and ctx["face_finish_type"] != str(expected):
        return False, f"face_finish_type={ctx['face_finish_type']}"

    not_expected = gate.get("face_finish_type_not")
    if not_expected is not None and ctx["face_finish_type"] == str(not_expected):
        return False, f"face_finish_type={ctx['face_finish_type']}"

    expected_return = gate.get("return_finish_type")
    if expected_return is not None and ctx["return_finish_type"] != str(expected_return):
        return False, f"return_finish_type={ctx['return_finish_type']}"

    return True, None


def _operation_active(raw: dict[str, Any], ctx: dict[str, Any]) -> tuple[bool, str | None]:
    code = str(raw.get("code") or "")
    params = raw.get("formula_params")
    if isinstance(params, dict):
        gate = params.get("gate")
        active, reason = _gate_active(gate, ctx)
        if not active:
            return False, reason

    if code in {"led_mounting", "electrical_wiring", "led_testing", "led_install_letters"}:
        if not ctx["illuminated"]:
            return False, "non_illuminated"
        if not ctx.get("lighting_system_type"):
            return False, "lighting_system_missing"

    if code in {"vinyl_application", "face_vinyl_apply"}:
        if ctx["face_finish_type"] in {"none", "policromie"}:
            return False, f"face_finish_type={ctx['face_finish_type']}"

    return True, None


def build_task_preview_items(
    template: ResolvedProductTemplate,
    finish_setup: dict[str, Any] | None,
) -> list[IntakeV4TaskPreviewItem]:
    ctx = _finish_context(finish_setup)
    items: list[IntakeV4TaskPreviewItem] = []
    for raw in template.operations:
        if not isinstance(raw, dict):
            continue
        code = str(raw.get("code") or "").strip()
        if not code:
            continue
        seq_raw = raw.get("sequence")
        try:
            sequence = int(seq_raw) if seq_raw is not None else 999
        except (TypeError, ValueError):
            sequence = 999
        active, reason = _operation_active(raw, ctx)
        items.append(
            IntakeV4TaskPreviewItem(
                operation_code=code,
                label=str(raw.get("label") or code),
                workcenter=str(raw.get("workcenter") or "") or None,
                sequence=sequence,
                component_ref=str(raw.get("component_ref") or "") or None,
                active=active,
                inactive_reason=reason,
            )
        )
    items.sort(key=lambda item: (item.sequence, item.operation_code))
    return items


async def build_binding_response(
    db: AsyncSession,
    workspace_id: str,
    template: ResolvedProductTemplate,
) -> IntakeV4ProductSystemBindingResponse:
    blockers: list[str] = []
    if not template.template_active:
        blockers.append("product_system_template_inactive")

    module_links = await list_template_module_links(db, template)

    return IntakeV4ProductSystemBindingResponse(
        workspace_id=workspace_id,
        template_code=template.template_code,
        template_id=template.template_id,
        template_label=template.template_label,
        product_family=template.product_family,
        product_family_name=template.product_family_name,
        operation_count=len(template.operations),
        component_count=len(template.components),
        template_active=template.template_active,
        module_links=module_links,
        blockers=blockers,
    )
