"""Actual Cost Policy Runtime V1 application service.

Owns standard internal labor costing and explicit execution-job closure only.
It does not read workcenter rates, employee salary fields, or commercial pricing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.actual_cost_policy import (
    ActualLaborCostLine,
    ExecutionJobClosure,
    ExecutionJobClosureEvent,
    RoleSkillLaborCostPolicy,
)
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.stock_movements import StockMovement
from services.controlled_task_session_service import _parse_reality_tasks
from services.execution_plan_task_parser import operational_tasks_only
from services.task_work_session_service import ensure_session_id, is_session_active

REASON_MISSING_POLICY = "standard_role_skill_policy_unavailable"
REASON_HISTORICAL_POLICY_UNAVAILABLE = "historical_policy_unavailable"
REASON_HISTORICAL_COST_NOT_FROZEN = "historical_cost_not_frozen"
REASON_POLICY_BOUNDARY_CROSSING = "policy_boundary_crossing_unsupported"
REASON_ACTIVE_SESSION = "active_session_open"
REASON_INCOMPLETE_TASKS = "required_tasks_incomplete"
REASON_MATERIAL_COST_MISSING = "actual_material_cost_missing"
REASON_JOB_NOT_CLOSED = "job_not_closed"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(raw: object) -> datetime | None:
    try:
        value = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _duration_seconds(session: dict[str, Any]) -> int | None:
    started = _parse_timestamp(session.get("started_at"))
    ended = _parse_timestamp(session.get("ended_at"))
    if started is None or ended is None or ended < started:
        return None
    return int((ended - started).total_seconds())


@dataclass(frozen=True)
class PolicyMatch:
    policy: RoleSkillLaborCostPolicy | None
    reason: str | None


class ActualCostPolicyRuntimeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_policy(self, payload: dict[str, Any], actor_id: str) -> RoleSkillLaborCostPolicy:
        role_code = str(payload.get("role_code") or "").strip()
        skill_code = str(payload.get("skill_code") or "").strip() or None
        rate = payload.get("standard_internal_rate")
        effective_from = payload.get("effective_from")
        if not role_code or not isinstance(rate, (int, float)) or rate < 0 or not isinstance(effective_from, datetime):
            raise HTTPException(status_code=422, detail={"error": "invalid_standard_internal_cost_policy"})
        if payload.get("rate_unit", "hour") != "hour":
            raise HTTPException(status_code=422, detail={"error": "rate_unit_must_be_hour"})
        effective_to = payload.get("effective_to")
        if effective_to is not None and effective_to <= effective_from:
            raise HTTPException(status_code=422, detail={"error": "invalid_effective_interval"})
        await self._assert_no_overlap(
            role_code=role_code,
            skill_code=skill_code,
            effective_from=effective_from,
            effective_to=effective_to,
        )
        policy = RoleSkillLaborCostPolicy(
            role_code=role_code,
            skill_code=skill_code,
            standard_internal_rate=float(rate),
            rate_unit="hour",
            currency=str(payload.get("currency") or "RON"),
            effective_from=effective_from,
            effective_to=effective_to,
            active=True,
            provenance=str(payload.get("provenance") or "manager_confirmed"),
            reason=str(payload.get("reason") or "Cost intern standard aprobat"),
            created_by=actor_id,
            version=1,
        )
        self.db.add(policy)
        await self.db.flush()
        return policy

    async def _assert_no_overlap(
        self, *, role_code: str, skill_code: str | None, effective_from: datetime, effective_to: datetime | None
    ) -> None:
        statement = select(RoleSkillLaborCostPolicy).where(
            RoleSkillLaborCostPolicy.role_code == role_code,
            RoleSkillLaborCostPolicy.active.is_(True),
            RoleSkillLaborCostPolicy.skill_code.is_(skill_code),
        )
        existing = (await self.db.execute(statement)).scalars().all()
        for policy in existing:
            existing_end = policy.effective_to
            starts_before_existing_end = existing_end is None or effective_from < existing_end
            ends_after_existing_start = effective_to is None or effective_to > policy.effective_from
            if starts_before_existing_end and ends_after_existing_start:
                raise HTTPException(status_code=409, detail={"error": "overlapping_active_policy_interval"})

    async def match_policy(self, *, role_code: str, skill_code: str | None, at: datetime) -> PolicyMatch:
        for candidate_skill in (skill_code, None):
            statement = (
                select(RoleSkillLaborCostPolicy)
                .where(
                    RoleSkillLaborCostPolicy.role_code == role_code,
                    RoleSkillLaborCostPolicy.skill_code.is_(candidate_skill),
                    RoleSkillLaborCostPolicy.active.is_(True),
                    RoleSkillLaborCostPolicy.effective_from <= at,
                )
                .order_by(RoleSkillLaborCostPolicy.effective_from.desc())
            )
            policies = (await self.db.execute(statement)).scalars().all()
            policy = next(
                (row for row in policies if row.effective_to is None or at < row.effective_to),
                None,
            )
            if policy is not None:
                return PolicyMatch(policy=policy, reason=None)
        return PolicyMatch(policy=None, reason=REASON_MISSING_POLICY)

    async def finalize_labor_lines(self, order_id: int) -> dict[str, Any]:
        reality = (
            await self.db.execute(select(ExecutionReality).where(ExecutionReality.order_id == order_id))
        ).scalar_one_or_none()
        if reality is None:
            return {"created": 0, "existing": 0, "unavailable_reasons": [REASON_HISTORICAL_POLICY_UNAVAILABLE]}
        plan = (
            await self.db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
        ).scalar_one_or_none()
        tasks = {str(task.get("task_id")): task for task in operational_tasks_only(plan.tasks_json)} if plan else {}
        created = 0
        existing = 0
        reasons: list[str] = []
        for session in _parse_reality_tasks(reality.tasks_json):
            if is_session_active(session) or not session.get("ended_at"):
                continue
            session_ref = ensure_session_id(session)
            duplicate = (
                await self.db.execute(
                    select(ActualLaborCostLine).where(
                        ActualLaborCostLine.order_id == order_id,
                        ActualLaborCostLine.session_ref == session_ref,
                    )
                )
            ).scalar_one_or_none()
            if duplicate is not None:
                existing += 1
                continue
            # Existing observations are not altered or retrospectively valued.
            if session.get("actual_cost_policy_runtime_v1") is not True:
                reasons.extend([REASON_HISTORICAL_POLICY_UNAVAILABLE, REASON_HISTORICAL_COST_NOT_FROZEN])
                continue
            seconds = _duration_seconds(session)
            employee_id = session.get("employee_id")
            if seconds is None or not isinstance(employee_id, int):
                reasons.append(REASON_HISTORICAL_POLICY_UNAVAILABLE)
                continue
            employee = (
                await self.db.execute(select(Employees).where(Employees.id == employee_id))
            ).scalar_one_or_none()
            if employee is None or not employee.role:
                reasons.append(REASON_MISSING_POLICY)
                continue
            task = tasks.get(str(session.get("task_id") or ""), {})
            skill_code = str(session.get("skill_code") or task.get("skill_code") or "").strip() or None
            start = _parse_timestamp(session.get("started_at"))
            end = _parse_timestamp(session.get("ended_at"))
            assert start is not None and end is not None
            start_match = await self.match_policy(role_code=str(employee.role), skill_code=skill_code, at=start)
            end_match = await self.match_policy(role_code=str(employee.role), skill_code=skill_code, at=end)
            if start_match.policy is None or end_match.policy is None:
                reasons.append(REASON_MISSING_POLICY)
                continue
            if start_match.policy.id != end_match.policy.id:
                reasons.append(REASON_POLICY_BOUNDARY_CROSSING)
                continue
            policy = end_match.policy
            self.db.add(
                ActualLaborCostLine(
                    order_id=order_id,
                    task_id=str(session.get("task_id") or ""),
                    session_ref=session_ref,
                    employee_id=employee_id,
                    role_code=str(employee.role),
                    skill_code=skill_code,
                    duration_seconds=seconds,
                    rate_used=float(policy.standard_internal_rate),
                    currency=policy.currency,
                    labor_cost_amount=round(seconds * float(policy.standard_internal_rate) / 3600, 4),
                    policy_id=policy.id,
                    policy_version=policy.version,
                    freeze_status="frozen",
                )
            )
            created += 1
        await self.db.flush()
        return {"created": created, "existing": existing, "unavailable_reasons": sorted(set(reasons))}

    async def actual_material_cost(self, order_id: int) -> dict[str, Any]:
        movements = (
            await self.db.execute(
                select(StockMovement).where(
                    StockMovement.order_id == order_id,
                    StockMovement.movement_type == "consumption",
                )
            )
        ).scalars().all()
        if not movements:
            return {"available": False, "value": None, "reason": REASON_MATERIAL_COST_MISSING}
        if any(m.extended_cost_snapshot is None for m in movements):
            return {"available": False, "value": None, "reason": REASON_MATERIAL_COST_MISSING}
        currencies = {m.currency_snapshot for m in movements}
        if len(currencies) != 1 or None in currencies:
            return {"available": False, "value": None, "reason": REASON_MATERIAL_COST_MISSING}
        return {
            "available": True,
            "value": round(sum(float(m.extended_cost_snapshot) for m in movements), 4),
            "currency": currencies.pop(),
            "reason": None,
        }

    async def closure_readiness(self, order_id: int) -> dict[str, Any]:
        reality = (
            await self.db.execute(select(ExecutionReality).where(ExecutionReality.order_id == order_id))
        ).scalar_one_or_none()
        sessions = _parse_reality_tasks(reality.tasks_json if reality else None)
        if any(is_session_active(session) for session in sessions):
            return {"ready": False, "reason": REASON_ACTIVE_SESSION}
        plan = (
            await self.db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
        ).scalar_one_or_none()
        if plan is None:
            return {"ready": False, "reason": REASON_INCOMPLETE_TASKS}
        task_ids = {str(entry.get("task_id") or "") for entry in sessions if entry.get("ended_at")}
        required = {str(task.get("task_id") or "") for task in operational_tasks_only(plan.tasks_json)}
        if not required or not required.issubset(task_ids):
            return {"ready": False, "reason": REASON_INCOMPLETE_TASKS}
        return {"ready": True, "reason": None}

    async def close_job(self, order_id: int, actor_id: str, checklist: dict[str, Any]) -> ExecutionJobClosure:
        readiness = await self.closure_readiness(order_id)
        if not readiness["ready"]:
            raise HTTPException(status_code=422, detail={"error": readiness["reason"]})
        if checklist.get("authorized") is not True:
            raise HTTPException(status_code=422, detail={"error": "closure_checklist_not_authorized"})
        closure = (
            await self.db.execute(select(ExecutionJobClosure).where(ExecutionJobClosure.order_id == order_id))
        ).scalar_one_or_none() or ExecutionJobClosure(order_id=order_id)
        closure.status = "closed"
        closure.closed_at = _utc_now()
        closure.closed_by = actor_id
        closure.checklist_json = json.dumps(checklist, ensure_ascii=False)
        self.db.add(closure)
        self.db.add(ExecutionJobClosureEvent(order_id=order_id, event_type="closed", actor_id=actor_id, checklist_json=closure.checklist_json))
        await self.db.flush()
        return closure

    async def reopen_job(self, order_id: int, actor_id: str, reason: str) -> ExecutionJobClosure:
        if not reason.strip():
            raise HTTPException(status_code=422, detail={"error": "reopen_reason_required"})
        closure = (
            await self.db.execute(select(ExecutionJobClosure).where(ExecutionJobClosure.order_id == order_id))
        ).scalar_one_or_none()
        if closure is None or closure.status != "closed":
            raise HTTPException(status_code=409, detail={"error": "job_not_closed"})
        closure.status = "reopened"
        closure.reopen_at = _utc_now()
        closure.reopen_by = actor_id
        closure.reopen_reason = reason
        self.db.add(ExecutionJobClosureEvent(order_id=order_id, event_type="reopened", actor_id=actor_id, reason=reason))
        await self.db.flush()
        return closure
