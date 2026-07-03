"""Intake V3 lighting / LED / PSU planning — workspace-level payload only."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from data_models.intake_v3_contracts import (
    BLOCKER_INSUFFICIENT_PSU_CAPACITY,
    BLOCKER_MISSING_LED_LIGHT_COLOR,
    BLOCKER_MISSING_LED_MODULE_COUNT,
    BLOCKER_MISSING_LED_MODULE_POWER,
    BLOCKER_MISSING_LED_SYSTEM,
    BLOCKER_MISSING_LIGHTING_ILLUMINATION_MODE,
    BLOCKER_MISSING_PSU_PLAN,
    BLOCKER_UNCONFIRMED_LIGHTING_PLAN,
    WARNING_LIGHTING_CUSTOM_COLOR,
    WARNING_LIGHTING_LOW_RESERVE_PERCENT,
    WARNING_LIGHTING_MANUAL_OVERRIDE,
    WARNING_LIGHTING_PSU_PACKED_AT_PACKAGING,
)
from schemas.intake_v3 import (
    IntakeV3ApplyLightingPlanRequest,
    IntakeV3LightingPlan,
    IntakeV3LightingPlanSummary,
    IntakeV3LightingPlanValidationResult,
    IntakeV3LightingSummary,
    IntakeV3PsuPlanUnit,
    OperationFlags,
    SupportContext,
    VectorModelIssue,
)

DEFAULT_RESERVE_PERCENT = 30.0
STANDARD_PSU_WATTAGES: tuple[int, ...] = (60, 100, 160, 200)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _positive(value: float | int | None) -> bool:
    try:
        return value is not None and float(value) > 0
    except (TypeError, ValueError):
        return False


def _round_watts(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 2)


def _issue(code: str, message: str, *, severity: str = "blocker", target_field: str | None = None) -> VectorModelIssue:
    return VectorModelIssue(code=code, severity=severity, message=message, target_field=target_field)


def _support_context(payload: dict[str, Any]) -> SupportContext:
    raw = payload.get("support_context")
    if isinstance(raw, dict):
        try:
            return SupportContext.model_validate(raw)
        except Exception:
            pass
    return SupportContext()


def _existing_plan(payload: dict[str, Any]) -> IntakeV3LightingPlan | None:
    raw = payload.get("lighting_plan")
    if isinstance(raw, dict):
        try:
            return IntakeV3LightingPlan.model_validate(raw)
        except Exception:
            return None
    return None


def is_non_illuminated(plan: IntakeV3LightingPlan) -> bool:
    if not plan.enabled:
        return True
    mode = (plan.illumination_mode or "unknown").lower()
    return mode == "non_illuminated"


def lighting_plan_required(payload: dict[str, Any]) -> bool:
    plan = _existing_plan(payload)
    if plan is not None:
        return not is_non_illuminated(plan)
    return _support_context(payload).illuminated


def draft_lighting_plan(payload: dict[str, Any]) -> IntakeV3LightingPlan:
    existing = _existing_plan(payload)
    if existing is not None:
        return sync_lighting_plan(existing)

    support = _support_context(payload)
    if not support.illuminated:
        return IntakeV3LightingPlan(
            enabled=False,
            illumination_mode="non_illuminated",
            psu_strategy="not_required",
            reserve_percent=DEFAULT_RESERVE_PERCENT,
        )

    return IntakeV3LightingPlan(
        enabled=True,
        illumination_mode="unknown",
        psu_strategy="auto",
        reserve_percent=DEFAULT_RESERVE_PERCENT,
    )


def propose_psu_units(required_watts: float) -> list[IntakeV3PsuPlanUnit]:
    """Minimal deterministic PSU combination from standard wattages."""
    if required_watts <= 0:
        return []

    best: list[int] | None = None

    def score(config: list[int]) -> tuple[int, float, int]:
        total = sum(config)
        return (len(config), total - required_watts, -max(config))

    def search(picked: list[int]) -> None:
        nonlocal best
        total = sum(picked)
        if total >= required_watts:
            if best is None or score(picked) < score(best):
                best = picked.copy()
            return
        if len(picked) >= 6:
            return
        for watt in STANDARD_PSU_WATTAGES:
            search([*picked, watt])

    search([])
    if not best:
        return []

    counts: dict[int, int] = {}
    for watt in best:
        counts[watt] = counts.get(watt, 0) + 1
    return [
        IntakeV3PsuPlanUnit(
            capacity_w=float(watt),
            quantity=qty,
            label=f"{watt} W PSU",
            source="auto",
        )
        for watt, qty in sorted(counts.items(), reverse=True)
    ]


def sync_lighting_plan(plan: IntakeV3LightingPlan) -> IntakeV3LightingPlan:
    synced = plan.model_copy(deep=True)

    if is_non_illuminated(synced):
        synced.psu_strategy = "not_required"
        synced.psu_units = []
        synced.psu_total_capacity_w = None
        synced.psu_reserve_w = None
        synced.estimated_total_watts = None
        synced.required_watts_with_reserve = None
        synced.psu_packed_at_packaging = False
        return synced

    if _positive(synced.module_power_w) and _positive(synced.module_count):
        synced.estimated_total_watts = _round_watts(
            float(synced.module_power_w) * int(synced.module_count)
        )
    else:
        synced.estimated_total_watts = None

    reserve = synced.reserve_percent if synced.reserve_percent is not None else DEFAULT_RESERVE_PERCENT
    if _positive(synced.estimated_total_watts):
        synced.required_watts_with_reserve = _round_watts(
            float(synced.estimated_total_watts) * (1 + float(reserve) / 100.0)
        )
    else:
        synced.required_watts_with_reserve = None

    strategy = (synced.psu_strategy or "auto").lower()
    if strategy == "packed_at_packaging":
        synced.psu_packed_at_packaging = True
        synced.psu_units = []
        synced.psu_total_capacity_w = None
        synced.psu_reserve_w = None
        return synced

    synced.psu_packed_at_packaging = False

    if strategy == "auto" and _positive(synced.required_watts_with_reserve):
        if not synced.psu_units:
            synced.psu_units = propose_psu_units(float(synced.required_watts_with_reserve))

    if synced.psu_units:
        total = sum(float(unit.capacity_w) * int(unit.quantity) for unit in synced.psu_units)
        synced.psu_total_capacity_w = _round_watts(total)
        if _positive(synced.required_watts_with_reserve):
            synced.psu_reserve_w = _round_watts(total - float(synced.required_watts_with_reserve))
        else:
            synced.psu_reserve_w = None
    else:
        synced.psu_total_capacity_w = None
        synced.psu_reserve_w = None

    return synced


def validate_lighting_plan_entry(plan: IntakeV3LightingPlan) -> list[VectorModelIssue]:
    synced = sync_lighting_plan(plan)
    issues: list[VectorModelIssue] = []

    if is_non_illuminated(synced):
        return issues

    mode = (synced.illumination_mode or "unknown").lower()
    if mode in {"", "unknown"}:
        issues.append(
            _issue(
                BLOCKER_MISSING_LIGHTING_ILLUMINATION_MODE,
                "Illumination mode is required for illuminated products.",
                target_field="lighting_plan.illumination_mode",
            )
        )

    if not synced.led_system:
        issues.append(
            _issue(
                BLOCKER_MISSING_LED_SYSTEM,
                "LED system type is required.",
                target_field="lighting_plan.led_system",
            )
        )

    if not synced.light_color:
        issues.append(
            _issue(
                BLOCKER_MISSING_LED_LIGHT_COLOR,
                "Light color selection is required.",
                target_field="lighting_plan.light_color",
            )
        )

    if not _positive(synced.module_power_w):
        issues.append(
            _issue(
                BLOCKER_MISSING_LED_MODULE_POWER,
                "Module power (W) is required.",
                target_field="lighting_plan.module_power_w",
            )
        )

    if not _positive(synced.module_count):
        issues.append(
            _issue(
                BLOCKER_MISSING_LED_MODULE_COUNT,
                "Module count is required.",
                target_field="lighting_plan.module_count",
            )
        )

    strategy = (synced.psu_strategy or "auto").lower()
    if strategy == "packed_at_packaging" or synced.psu_packed_at_packaging:
        return issues

    if strategy == "not_required":
        issues.append(
            _issue(
                BLOCKER_MISSING_PSU_PLAN,
                "PSU strategy must be configured for illuminated products.",
                target_field="lighting_plan.psu_strategy",
            )
        )

    if not synced.psu_units:
        issues.append(
            _issue(
                BLOCKER_MISSING_PSU_PLAN,
                "PSU units are required for illuminated products.",
                target_field="lighting_plan.psu_units",
            )
        )
    elif _positive(synced.required_watts_with_reserve) and _positive(synced.psu_total_capacity_w):
        if float(synced.psu_total_capacity_w) + 0.01 < float(synced.required_watts_with_reserve):
            if not (synced.manual_override_reason or "").strip():
                issues.append(
                    _issue(
                        BLOCKER_INSUFFICIENT_PSU_CAPACITY,
                        "PSU capacity is below required watts with reserve — adjust PSU or document override.",
                        target_field="lighting_plan.psu_units",
                    )
                )

    if not synced.is_confirmed:
        issues.append(
            _issue(
                BLOCKER_UNCONFIRMED_LIGHTING_PLAN,
                "Lighting plan needs LED module count and PSU capacity confirmation.",
                target_field="lighting_plan.is_confirmed",
            )
        )

    return issues


def collect_lighting_warnings(plan: IntakeV3LightingPlan) -> list[VectorModelIssue]:
    synced = sync_lighting_plan(plan)
    warnings: list[VectorModelIssue] = []

    if is_non_illuminated(synced):
        return warnings

    if (synced.manual_override_reason or "").strip():
        warnings.append(
            _issue(
                WARNING_LIGHTING_MANUAL_OVERRIDE,
                "Manual PSU override reason documented.",
                severity="warning",
                target_field="lighting_plan.manual_override_reason",
            )
        )

    reserve = synced.reserve_percent if synced.reserve_percent is not None else DEFAULT_RESERVE_PERCENT
    if float(reserve) < DEFAULT_RESERVE_PERCENT:
        warnings.append(
            _issue(
                WARNING_LIGHTING_LOW_RESERVE_PERCENT,
                f"Reserve percent {reserve}% is below recommended {DEFAULT_RESERVE_PERCENT}%.",
                severity="warning",
                target_field="lighting_plan.reserve_percent",
            )
        )

    if (synced.light_color or "").lower() == "custom":
        warnings.append(
            _issue(
                WARNING_LIGHTING_CUSTOM_COLOR,
                "Custom light color selected — verify with operator notes.",
                severity="warning",
                target_field="lighting_plan.light_color",
            )
        )

    if synced.psu_packed_at_packaging or (synced.psu_strategy or "").lower() == "packed_at_packaging":
        warnings.append(
            _issue(
                WARNING_LIGHTING_PSU_PACKED_AT_PACKAGING,
                "PSU will be packed and handled at packaging/delivery stage.",
                severity="warning",
                target_field="lighting_plan.psu_packed_at_packaging",
            )
        )

    insufficient = any(item.code == BLOCKER_INSUFFICIENT_PSU_CAPACITY for item in validate_lighting_plan_entry(synced))
    if insufficient and (synced.manual_override_reason or "").strip():
        warnings.append(
            _issue(
                WARNING_LIGHTING_MANUAL_OVERRIDE,
                "Insufficient PSU capacity accepted with manual override reason.",
                severity="warning",
                target_field="lighting_plan.manual_override_reason",
            )
        )

    return warnings


def collect_lighting_issues(payload: dict[str, Any]) -> tuple[list[VectorModelIssue], list[VectorModelIssue]]:
    if not lighting_plan_required(payload):
        return [], []

    plan = draft_lighting_plan(payload)
    blockers = validate_lighting_plan_entry(plan)
    warnings = collect_lighting_warnings(plan)

    blocker_codes = {item.code for item in blockers}
    if BLOCKER_INSUFFICIENT_PSU_CAPACITY in blocker_codes and (plan.manual_override_reason or "").strip():
        blockers = [item for item in blockers if item.code != BLOCKER_INSUFFICIENT_PSU_CAPACITY]

    return blockers, warnings


def summarize_lighting_plan(payload: dict[str, Any]) -> IntakeV3LightingPlanSummary:
    required = lighting_plan_required(payload)
    plan = draft_lighting_plan(payload)
    synced = sync_lighting_plan(plan)
    blockers, warnings = collect_lighting_issues(payload)

    if not required:
        status_value = "not_required"
        summary_message = "Non-illuminated product — LED/PSU planning not required."
    elif not blockers and synced.is_confirmed:
        status_value = "complete"
        summary_message = "Confirmed lighting plan is included in production setup summary."
    elif blockers:
        if _positive(synced.module_power_w) or _positive(synced.module_count) or synced.psu_units:
            status_value = "partial"
        else:
            status_value = "missing"
        summary_message = (
            "Pending lighting plan is not confirmed."
            if any(item.code == BLOCKER_UNCONFIRMED_LIGHTING_PLAN for item in blockers)
            else blockers[0].message
        )
    else:
        status_value = "partial"
        summary_message = "Lighting setup in progress — confirmation pending."

    preview = IntakeV3LightingSummary(
        enabled=synced.enabled,
        illumination_mode=str(synced.illumination_mode),
        led_system=synced.led_system,
        light_color=synced.light_color,
        light_color_label=synced.light_color_label,
        module_power_w=synced.module_power_w,
        module_count=synced.module_count,
        estimated_total_watts=synced.estimated_total_watts,
        required_watts_with_reserve=synced.required_watts_with_reserve,
        psu_strategy=str(synced.psu_strategy),
        psu_units=synced.psu_units,
        psu_total_capacity_w=synced.psu_total_capacity_w,
        psu_reserve_w=synced.psu_reserve_w,
        psu_packed_at_packaging=synced.psu_packed_at_packaging,
        status=status_value,
        is_confirmed=synced.is_confirmed,
        warnings=[item.message for item in warnings],
        summary_message=summary_message,
    )

    return IntakeV3LightingPlanSummary(
        lighting_plan_status=status_value,
        is_required=required,
        is_confirmed=synced.is_confirmed and not blockers,
        preview=preview,
    )


def validate_lighting_plan(payload: dict[str, Any], request: IntakeV3ApplyLightingPlanRequest) -> IntakeV3LightingPlanValidationResult:
    plan = sync_lighting_plan(request.lighting_plan)
    warnings = collect_lighting_warnings(plan)

    if is_non_illuminated(plan):
        return IntakeV3LightingPlanValidationResult(is_valid=True, blockers=[], warnings=warnings)

    if not request.lighting_plan.is_confirmed:
        return IntakeV3LightingPlanValidationResult(is_valid=True, blockers=[], warnings=warnings)

    blockers = validate_lighting_plan_entry(plan)
    if blockers:
        return IntakeV3LightingPlanValidationResult(is_valid=False, blockers=blockers, warnings=warnings)

    return IntakeV3LightingPlanValidationResult(is_valid=True, blockers=[], warnings=warnings)


def _sync_support_context(payload: dict[str, Any], plan: IntakeV3LightingPlan) -> dict[str, Any]:
    data = copy.deepcopy(payload)
    support_raw = data.get("support_context")
    if not isinstance(support_raw, dict):
        support_raw = {}
    support_raw["illuminated"] = not is_non_illuminated(plan)
    data["support_context"] = support_raw
    return data


def _sync_operation_flags(payload: dict[str, Any], plan: IntakeV3LightingPlan) -> dict[str, Any]:
    data = copy.deepcopy(payload)
    flags_raw = data.get("operation_flags")
    if not isinstance(flags_raw, dict):
        flags_raw = {}
    try:
        flags = OperationFlags.model_validate(flags_raw)
    except Exception:
        flags = OperationFlags()
    flags.psu_packed_at_packaging = bool(
        plan.psu_packed_at_packaging or (plan.psu_strategy or "").lower() == "packed_at_packaging"
    )
    data["operation_flags"] = flags.model_dump(mode="json")
    return data


def apply_lighting_plan_to_payload(
    payload: dict[str, Any],
    request: IntakeV3ApplyLightingPlanRequest,
    *,
    confirmed_by: str | None = None,
) -> tuple[dict[str, Any], IntakeV3LightingPlanSummary]:
    validation = validate_lighting_plan(payload, request)
    if not validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "lighting_plan_validation_failed",
                "blockers": [item.model_dump(mode="json") for item in validation.blockers],
                "warnings": [item.model_dump(mode="json") for item in validation.warnings],
            },
        )

    plan = sync_lighting_plan(request.lighting_plan)
    if plan.is_confirmed:
        plan.confirmed_at = _utcnow_iso()
        plan.confirmed_by = confirmed_by
    else:
        plan.confirmed_at = None
        plan.confirmed_by = None

    updated = copy.deepcopy(payload)
    updated["lighting_plan"] = plan.model_dump(mode="json")
    summary = summarize_lighting_plan(updated)
    updated["lighting_plan_status"] = summary.lighting_plan_status
    updated = _sync_support_context(updated, plan)
    updated = _sync_operation_flags(updated, plan)
    return updated, summary
