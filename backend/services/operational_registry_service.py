"""Operational Workforce & Resource Registry service.

Read/write helpers for employee authorizations, production resources,
operation resource requirements, and field-installation teams.

Does NOT touch CostEngine, Pricing, or Quote flows.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from models.employees import Employees
from models.operational_registry import (
    EmployeeResourceAuthorization,
    EmployeeSkillAuthorization,
    EmployeeWorkcenterAuthorization,
    FieldInstallationTeam,
    FieldInstallationTeamMember,
    MachineRegistry,
    OperationEmployeeAuthorization,
    OperationResourceRequirement,
)
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

FIELD_INSTALLATION_TEAM_STATUSES = frozenset(
    {"draft", "planned", "in_progress", "completed", "cancelled"}
)

AUTHORIZATION_MODES = frozenset({"skill", "explicit", "hybrid"})


def build_order_installation_ref(order_id: int) -> str:
    return f"ORDER-{order_id}"


def parse_order_id_from_installation_ref(installation_ref: str) -> Optional[int]:
    ref = (installation_ref or "").strip().upper()
    if ref.startswith("ORDER-"):
        try:
            return int(ref.split("-", 1)[1])
        except (TypeError, ValueError):
            return None
    return None


def _parse_json_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return [str(v) for v in parsed] if isinstance(parsed, list) else []
        except (TypeError, ValueError):
            return []
    return []


def _dump_json_list(values: Optional[List[str]]) -> Optional[str]:
    if values is None:
        return None
    return json.dumps(list(values), ensure_ascii=False)


class OperationalRegistryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_employee_authorizations(self, employee_id: int) -> Dict[str, List[str]]:
        skills = list(
            (
                await self.db.execute(
                    select(EmployeeSkillAuthorization.skill_code).where(
                        EmployeeSkillAuthorization.employee_id == employee_id
                    )
                )
            ).scalars().all()
        )
        workcenters = list(
            (
                await self.db.execute(
                    select(EmployeeWorkcenterAuthorization.workcenter_code).where(
                        EmployeeWorkcenterAuthorization.employee_id == employee_id
                    )
                )
            ).scalars().all()
        )
        resources = list(
            (
                await self.db.execute(
                    select(EmployeeResourceAuthorization.resource_code).where(
                        EmployeeResourceAuthorization.employee_id == employee_id
                    )
                )
            ).scalars().all()
        )
        return {
            "skill_codes": skills,
            "workcenter_codes": workcenters,
            "resource_codes": resources,
        }

    async def set_employee_authorizations(
        self,
        employee_id: int,
        *,
        skill_codes: Optional[List[str]] = None,
        workcenter_codes: Optional[List[str]] = None,
        resource_codes: Optional[List[str]] = None,
    ) -> Dict[str, List[str]]:
        if skill_codes is not None:
            await self.db.execute(
                delete(EmployeeSkillAuthorization).where(
                    EmployeeSkillAuthorization.employee_id == employee_id
                )
            )
            for code in sorted({c.strip() for c in skill_codes if c and c.strip()}):
                self.db.add(EmployeeSkillAuthorization(employee_id=employee_id, skill_code=code))

        if workcenter_codes is not None:
            await self.db.execute(
                delete(EmployeeWorkcenterAuthorization).where(
                    EmployeeWorkcenterAuthorization.employee_id == employee_id
                )
            )
            for code in sorted({c.strip() for c in workcenter_codes if c and c.strip()}):
                self.db.add(
                    EmployeeWorkcenterAuthorization(employee_id=employee_id, workcenter_code=code)
                )

        if resource_codes is not None:
            await self.db.execute(
                delete(EmployeeResourceAuthorization).where(
                    EmployeeResourceAuthorization.employee_id == employee_id
                )
            )
            for code in sorted({c.strip() for c in resource_codes if c and c.strip()}):
                self.db.add(
                    EmployeeResourceAuthorization(employee_id=employee_id, resource_code=code)
                )

        await self.db.commit()
        return await self.get_employee_authorizations(employee_id)

    async def list_employees_with_authorizations(
        self, skip: int = 0, limit: int = 500
    ) -> Dict[str, Any]:
        total = (await self.db.execute(select(func.count(Employees.id)))).scalar() or 0
        rows = (
            await self.db.execute(
                select(Employees).order_by(Employees.id.asc()).offset(skip).limit(limit)
            )
        ).scalars().all()

        items = []
        for emp in rows:
            auth = await self.get_employee_authorizations(emp.id)
            items.append(self._employee_registry_dict(emp, auth))
        return {"items": items, "total": total, "skip": skip, "limit": limit}

    async def get_employee_registry(self, employee_id: int) -> Optional[Dict[str, Any]]:
        emp = (
            await self.db.execute(select(Employees).where(Employees.id == employee_id))
        ).scalar_one_or_none()
        if emp is None:
            return None
        auth = await self.get_employee_authorizations(employee_id)
        return self._employee_registry_dict(emp, auth)

    def _employee_registry_dict(self, emp: Employees, auth: Dict[str, List[str]]) -> Dict[str, Any]:
        return {
            "id": emp.id,
            "name": emp.name,
            "role": emp.role,
            "department": emp.department,
            "status": emp.status,
            "employee_type": emp.employee_type,
            "user_id": emp.user_id,
            "salary_amount": emp.cost_lunar_firma,
            "salary_currency": emp.salary_currency or "RON",
            "salary_period": emp.salary_period or "monthly",
            "skill_codes": auth["skill_codes"],
            "workcenter_codes": auth["workcenter_codes"],
            "resource_codes": auth["resource_codes"],
        }

    async def list_resources(self) -> List[Dict[str, Any]]:
        rows = (
            await self.db.execute(
                select(MachineRegistry)
                .where(MachineRegistry.is_active == True)  # noqa: E712
                .order_by(MachineRegistry.workcenter_code, MachineRegistry.machine_code)
            )
        ).scalars().all()
        return [self._resource_dict(r) for r in rows]

    async def get_resource(self, resource_code: str) -> Optional[Dict[str, Any]]:
        row = (
            await self.db.execute(
                select(MachineRegistry).where(MachineRegistry.machine_code == resource_code)
            )
        ).scalar_one_or_none()
        return self._resource_dict(row) if row else None

    def _parse_json_dict(self, value: Any) -> Dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        if isinstance(value, str) and value.strip():
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else {}
            except (TypeError, ValueError):
                return {}
        return {}

    def _resource_dict(self, row: MachineRegistry) -> Dict[str, Any]:
        return {
            "resource_code": row.machine_code,
            "name": row.name,
            "description": row.description,
            "machine_type": row.machine_type,
            "resource_kind": row.resource_kind,
            "workcenter_code": row.workcenter_code,
            "operational_status": row.operational_status,
            "is_available": row.is_available,
            "is_active": row.is_active,
            "capabilities": _parse_json_list(row.capabilities),
            "capacity_metadata": self._parse_json_dict(row.capacity_metadata),
        }

    async def upsert_resource(self, data: Dict[str, Any]) -> MachineRegistry:
        code = str(data["machine_code"]).strip()
        existing = (
            await self.db.execute(
                select(MachineRegistry).where(MachineRegistry.machine_code == code)
            )
        ).scalar_one_or_none()

        payload = {
            "name": data["name"],
            "description": data.get("description"),
            "machine_type": data["machine_type"],
            "resource_kind": data.get("resource_kind", "machine"),
            "workcenter_code": data.get("workcenter_code"),
            "operational_status": data.get("operational_status", "active"),
            "is_available": bool(data.get("is_available", True)),
            "is_active": bool(data.get("is_active", True)),
            "manufacturer": data.get("manufacturer"),
            "model": data.get("model"),
            "year_acquired": data.get("year_acquired"),
            "capabilities": _dump_json_list(data.get("capabilities")),
            "capacity_metadata": json.dumps(data.get("capacity_metadata") or {}, ensure_ascii=False),
        }

        if existing is None:
            obj = MachineRegistry(machine_code=code, **payload)
            self.db.add(obj)
        else:
            if data.get("capacity_metadata") is not None:
                existing_meta = self._parse_json_dict(existing.capacity_metadata)
                incoming = data.get("capacity_metadata") or {}
                if isinstance(incoming, dict):
                    merged = {**existing_meta, **incoming}
                    payload["capacity_metadata"] = json.dumps(merged, ensure_ascii=False)
            for k, v in payload.items():
                setattr(existing, k, v)
            obj = existing

        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def list_operation_mappings(self) -> List[Dict[str, Any]]:
        rows = (
            await self.db.execute(
                select(OperationResourceRequirement).order_by(
                    OperationResourceRequirement.operation_code.asc()
                )
            )
        ).scalars().all()
        result = []
        for row in rows:
            mapped = await self._operation_mapping_dict(row)
            result.append(mapped)
        return result

    async def resolve_operation_mapping(
        self, operation_code: str
    ) -> Optional[Dict[str, Any]]:
        """Resolve registry mapping by direct code or product_system_aliases."""
        code = (operation_code or "").strip()
        if not code:
            return None

        direct = await self.get_operation_mapping(code)
        if direct is not None:
            return {**direct, "resolved_operation_code": code, "resolution": "direct"}

        rows = (
            await self.db.execute(select(OperationResourceRequirement))
        ).scalars().all()
        code_lower = code.lower()
        for row in rows:
            aliases = _parse_json_list(row.product_system_aliases)
            if any(a.lower() == code_lower for a in aliases):
                mapped = await self._operation_mapping_dict(row)
                return {
                    **mapped,
                    "resolved_operation_code": row.operation_code,
                    "resolution": "alias",
                    "matched_alias": code,
                }
        return None

    async def get_operation_employee_ids(self, operation_code: str) -> List[int]:
        return list(
            (
                await self.db.execute(
                    select(OperationEmployeeAuthorization.employee_id).where(
                        OperationEmployeeAuthorization.operation_code == operation_code
                    )
                )
            ).scalars().all()
        )

    async def set_operation_employee_authorizations(
        self, operation_code: str, employee_ids: Optional[List[int]]
    ) -> List[int]:
        code = (operation_code or "").strip()
        if not code:
            raise ValueError("operation_code_required")

        await self.db.execute(
            delete(OperationEmployeeAuthorization).where(
                OperationEmployeeAuthorization.operation_code == code
            )
        )
        normalized_ids = sorted({int(i) for i in (employee_ids or []) if i is not None})
        for emp_id in normalized_ids:
            await self._get_active_employee(emp_id)
            self.db.add(
                OperationEmployeeAuthorization(
                    operation_code=code,
                    employee_id=emp_id,
                    authorization_type="explicit",
                )
            )
        await self.db.commit()
        return normalized_ids

    def _employee_matches_mapping_rules(
        self,
        auth: Dict[str, List[str]],
        mapping: Dict[str, Any],
        *,
        machine_type: Optional[str] = None,
    ) -> bool:
        required_skills = set(mapping.get("required_skill_codes") or [])
        allowed_workcenters = set(mapping.get("allowed_workcenter_codes") or [])
        allowed_resources = set(mapping.get("allowed_resource_codes") or [])

        employee_skills = set(auth.get("skill_codes") or [])
        employee_workcenters = set(auth.get("workcenter_codes") or [])
        employee_resources = set(auth.get("resource_codes") or [])

        if not required_skills and not allowed_workcenters and not allowed_resources:
            return False

        skill_ok = not required_skills or bool(required_skills & employee_skills)
        wc_ok = not allowed_workcenters or bool(allowed_workcenters & employee_workcenters)
        resource_ok = True
        if allowed_resources:
            if machine_type:
                mt = machine_type.lower().replace(" ", "_")
                resource_ok = any(
                    r.lower() in mt or mt in r.lower() for r in allowed_resources
                ) or bool(allowed_resources & employee_resources)
            else:
                resource_ok = bool(allowed_resources & employee_resources) or not allowed_resources

        return skill_ok and wc_ok and resource_ok

    async def check_employee_operation_eligibility(
        self,
        employee_id: int,
        operation_code: str,
        *,
        machine_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        emp = (
            await self.db.execute(select(Employees).where(Employees.id == employee_id))
        ).scalar_one_or_none()
        if emp is None:
            return {
                "eligible": False,
                "authorization_status": "unverified",
                "reason": "employee_not_found",
            }
        if (emp.status or "").lower() != "active":
            return {
                "eligible": False,
                "authorization_status": "not_authorized",
                "reason": "employee_inactive",
            }

        resolved = await self.resolve_operation_mapping(operation_code)
        if resolved is None:
            return {
                "eligible": False,
                "authorization_status": "unverified",
                "reason": "no_operation_mapping",
            }

        registry_code = resolved["operation_code"]
        mode = (resolved.get("authorization_mode") or "hybrid").lower()
        if mode not in AUTHORIZATION_MODES:
            mode = "hybrid"

        auth = await self.get_employee_authorizations(employee_id)
        explicit_ids = set(await self.get_operation_employee_ids(registry_code))
        skill_match = self._employee_matches_mapping_rules(
            auth, resolved, machine_type=machine_type
        )

        if mode == "explicit":
            eligible = employee_id in explicit_ids
        elif mode == "skill":
            eligible = skill_match
        else:
            if explicit_ids:
                eligible = employee_id in explicit_ids or skill_match
            else:
                eligible = skill_match

        return {
            "eligible": eligible,
            "authorization_status": "authorized" if eligible else "not_authorized",
            "authorization_mode": mode,
            "operation_code": registry_code,
            "resolved_from": resolved.get("resolution"),
            "explicit_override": employee_id in explicit_ids,
            "skill_match": skill_match,
        }

    async def get_eligible_employees_for_operation(
        self,
        operation_code: str,
        *,
        machine_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        resolved = await self.resolve_operation_mapping(operation_code)
        if resolved is None:
            return {
                "operation_code": operation_code,
                "resolved_operation_code": None,
                "items": [],
                "total": 0,
                "resolution": "not_found",
            }

        registry_code = resolved["operation_code"]
        mode = (resolved.get("authorization_mode") or "hybrid").lower()
        if mode not in AUTHORIZATION_MODES:
            mode = "hybrid"

        rows = (
            await self.db.execute(
                select(Employees)
                .where(Employees.status == "active")
                .order_by(Employees.name.asc())
            )
        ).scalars().all()

        explicit_ids = set(await self.get_operation_employee_ids(registry_code))
        items: List[Dict[str, Any]] = []
        for emp in rows:
            auth = await self.get_employee_authorizations(emp.id)
            skill_match = self._employee_matches_mapping_rules(
                auth, resolved, machine_type=machine_type
            )
            if mode == "explicit":
                eligible = emp.id in explicit_ids
            elif mode == "skill":
                eligible = skill_match
            else:
                eligible = (emp.id in explicit_ids) if explicit_ids else skill_match
                if explicit_ids:
                    eligible = emp.id in explicit_ids or skill_match

            payload = self._employee_registry_dict(emp, auth)
            payload["eligibility"] = "authorized" if eligible else "not_authorized"
            payload["skill_match"] = skill_match
            payload["explicit_override"] = emp.id in explicit_ids
            if eligible:
                items.append(payload)

        return {
            "operation_code": operation_code,
            "resolved_operation_code": registry_code,
            "authorization_mode": mode,
            "resolution": resolved.get("resolution"),
            "required_skill_codes": resolved.get("required_skill_codes") or [],
            "allowed_workcenter_codes": resolved.get("allowed_workcenter_codes") or [],
            "allowed_resource_codes": resolved.get("allowed_resource_codes") or [],
            "default_resource_code": resolved.get("default_resource_code"),
            "authorized_employee_ids": sorted(explicit_ids),
            "items": items,
            "total": len(items),
        }

    async def get_catalog(self) -> Dict[str, Any]:
        from services.operational_catalog import get_operational_catalog

        catalog = get_operational_catalog()
        resources = await self.list_resources()
        catalog["resources"] = resources
        return catalog

    async def get_operation_mapping(self, operation_code: str) -> Optional[Dict[str, Any]]:
        row = (
            await self.db.execute(
                select(OperationResourceRequirement).where(
                    OperationResourceRequirement.operation_code == operation_code
                )
            )
        ).scalar_one_or_none()
        return await self._operation_mapping_dict(row) if row else None

    async def upsert_operation_mapping(self, data: Dict[str, Any]) -> OperationResourceRequirement:
        code = str(data["operation_code"]).strip()
        existing = (
            await self.db.execute(
                select(OperationResourceRequirement).where(
                    OperationResourceRequirement.operation_code == code
                )
            )
        ).scalar_one_or_none()

        mode = (data.get("authorization_mode") or "hybrid").lower()
        if mode not in AUTHORIZATION_MODES:
            mode = "hybrid"

        payload = {
            "required_skill_codes": _dump_json_list(data.get("required_skill_codes")),
            "allowed_workcenter_codes": _dump_json_list(data.get("allowed_workcenter_codes")),
            "allowed_resource_codes": _dump_json_list(data.get("allowed_resource_codes")),
            "authorization_mode": mode,
            "default_resource_code": data.get("default_resource_code"),
            "product_system_aliases": _dump_json_list(data.get("product_system_aliases")),
            "notes": data.get("notes"),
        }

        if existing is None:
            obj = OperationResourceRequirement(operation_code=code, **payload)
            self.db.add(obj)
        else:
            for k, v in payload.items():
                setattr(existing, k, v)
            obj = existing

        await self.db.commit()
        await self.db.refresh(obj)

        if "authorized_employee_ids" in data:
            await self.set_operation_employee_authorizations(
                code, data.get("authorized_employee_ids")
            )

        return obj

    async def _operation_mapping_dict(self, row: OperationResourceRequirement) -> Dict[str, Any]:
        employee_ids = await self.get_operation_employee_ids(row.operation_code)
        return {
            "operation_code": row.operation_code,
            "required_skill_codes": _parse_json_list(row.required_skill_codes),
            "allowed_workcenter_codes": _parse_json_list(row.allowed_workcenter_codes),
            "allowed_resource_codes": _parse_json_list(row.allowed_resource_codes),
            "authorization_mode": row.authorization_mode or "hybrid",
            "default_resource_code": row.default_resource_code,
            "product_system_aliases": _parse_json_list(row.product_system_aliases),
            "authorized_employee_ids": employee_ids,
            "notes": row.notes,
        }

    async def get_authorized_employees_for_resource(self, resource_code: str) -> List[Dict[str, Any]]:
        employee_ids = list(
            (
                await self.db.execute(
                    select(EmployeeResourceAuthorization.employee_id).where(
                        EmployeeResourceAuthorization.resource_code == resource_code
                    )
                )
            ).scalars().all()
        )
        if not employee_ids:
            return []

        rows = (
            await self.db.execute(select(Employees).where(Employees.id.in_(employee_ids)))
        ).scalars().all()
        result = []
        for emp in rows:
            auth = await self.get_employee_authorizations(emp.id)
            result.append(self._employee_registry_dict(emp, auth))
        return result

    async def _get_active_employee(self, employee_id: int) -> Employees:
        emp = (
            await self.db.execute(select(Employees).where(Employees.id == employee_id))
        ).scalar_one_or_none()
        if emp is None:
            raise ValueError("employee_not_found")
        if (emp.status or "").lower() != "active":
            raise ValueError("employee_inactive")
        return emp

    async def _serialize_field_installation_team(self, team: FieldInstallationTeam) -> Dict[str, Any]:
        members = (
            await self.db.execute(
                select(FieldInstallationTeamMember).where(
                    FieldInstallationTeamMember.team_id == team.id
                )
            )
        ).scalars().all()

        member_payload = []
        for m in members:
            emp = (
                await self.db.execute(select(Employees).where(Employees.id == m.employee_id))
            ).scalar_one_or_none()
            if emp:
                auth = await self.get_employee_authorizations(emp.id)
                member_payload.append(
                    {
                        "employee_id": emp.id,
                        "employee_name": emp.name,
                        "employee_role": emp.role,
                        "role_on_site": m.role_on_site,
                        "skill_codes": auth["skill_codes"],
                    }
                )

        order_id = parse_order_id_from_installation_ref(team.installation_ref)
        reporting = self._parse_reporting_json(team.reporting_json)
        return {
            "id": team.id,
            "installation_ref": team.installation_ref,
            "order_id": order_id,
            "status": team.status,
            "site_address": team.site_address,
            "scheduled_at": team.scheduled_at.isoformat() if team.scheduled_at else None,
            "notes": team.notes,
            "members": member_payload,
            "member_count": len(member_payload),
            "reporting_ready": team.started_at is not None,
            "started_at": team.started_at.isoformat() if team.started_at else None,
            "ended_at": team.ended_at.isoformat() if team.ended_at else None,
            "client_observations": team.client_observations,
            "completion_photos": reporting.get("completion_photos") or [],
            "members_present": reporting.get("members_present") or [],
            "materials_consumed": reporting.get("materials_consumed") or [],
            "internal_notes": reporting.get("internal_notes"),
            "started_by_employee_id": reporting.get("started_by_employee_id"),
            "warnings": reporting.get("warnings") or [],
        }

    @staticmethod
    def _parse_reporting_json(raw: Optional[str]) -> Dict[str, Any]:
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    async def _load_field_team(self, team_id: int) -> FieldInstallationTeam:
        team = (
            await self.db.execute(
                select(FieldInstallationTeam).where(FieldInstallationTeam.id == team_id)
            )
        ).scalar_one_or_none()
        if team is None:
            raise ValueError("team_not_found")
        return team

    async def start_field_installation_reporting(
        self,
        team_id: int,
        *,
        started_by_employee_id: Optional[int] = None,
        members_present: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        team = await self._load_field_team(team_id)
        if team.started_at is not None and team.status == "in_progress":
            raise ValueError("installation_already_started")

        warnings: List[str] = []
        member_count = (
            await self.db.execute(
                select(FieldInstallationTeamMember).where(
                    FieldInstallationTeamMember.team_id == team_id
                )
            )
        ).scalars().all()
        if len(member_count) == 0:
            warnings.append("no_team_members_allocated")

        started_by_name: Optional[str] = None
        if started_by_employee_id is not None:
            emp = await self._get_active_employee(started_by_employee_id)
            started_by_name = emp.name

        now = datetime.now(timezone.utc)
        team.started_at = now
        team.status = "in_progress"

        reporting = self._parse_reporting_json(team.reporting_json)
        reporting["started_by_employee_id"] = started_by_employee_id
        reporting["warnings"] = warnings

        present_payload = []
        for emp_id in members_present or []:
            try:
                emp = await self._get_active_employee(emp_id)
                present_payload.append(
                    {
                        "employee_id": emp.id,
                        "employee_name": emp.name,
                        "present_at": now.isoformat(),
                    }
                )
            except ValueError:
                warnings.append(f"invalid_member_present:{emp_id}")
        if present_payload:
            reporting["members_present"] = present_payload

        team.reporting_json = json.dumps(reporting, ensure_ascii=False)
        await self.db.commit()
        await self.db.refresh(team)
        row = await self.get_field_installation_team(team_id)
        assert row is not None
        return row

    async def complete_field_installation_reporting(
        self,
        team_id: int,
        *,
        client_observations: Optional[str] = None,
        completion_photos: Optional[List[str]] = None,
        internal_notes: Optional[str] = None,
        members_present: Optional[List[int]] = None,
        materials_consumed: Optional[List[Dict[str, Any]]] = None,
        completed_by_employee_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        team = await self._load_field_team(team_id)
        if team.started_at is None:
            raise ValueError("installation_not_started")

        now = datetime.now(timezone.utc)
        team.ended_at = now
        team.status = "completed"
        if client_observations is not None:
            team.client_observations = client_observations

        reporting = self._parse_reporting_json(team.reporting_json)
        if completion_photos is not None:
            reporting["completion_photos"] = [p for p in completion_photos if p and str(p).strip()]
        if internal_notes is not None:
            reporting["internal_notes"] = internal_notes

        if completed_by_employee_id is not None:
            emp = await self._get_active_employee(completed_by_employee_id)
            reporting["completed_by_employee_id"] = emp.id
            reporting["completed_by_employee_name"] = emp.name

        if members_present is not None:
            present_payload = []
            for emp_id in members_present:
                emp = await self._get_active_employee(emp_id)
                present_payload.append(
                    {
                        "employee_id": emp.id,
                        "employee_name": emp.name,
                        "present_at": now.isoformat(),
                    }
                )
            reporting["members_present"] = present_payload

        if materials_consumed:
            normalized_materials = []
            for mat in materials_consumed:
                if not isinstance(mat, dict):
                    continue
                row = {
                    "material_name": str(mat.get("material_name") or "").strip(),
                    "quantity": float(mat.get("quantity") or 0),
                    "unit": str(mat.get("unit") or "buc").strip().lower(),
                    "reported_at": now.isoformat(),
                }
                if mat.get("reported_by_employee_id") is not None:
                    await self._get_active_employee(int(mat["reported_by_employee_id"]))
                    row["reported_by_employee_id"] = int(mat["reported_by_employee_id"])
                if mat.get("consumption_notes"):
                    row["consumption_notes"] = mat.get("consumption_notes")
                if row["material_name"] and row["quantity"] > 0:
                    normalized_materials.append(row)
            reporting["materials_consumed"] = normalized_materials

        team.reporting_json = json.dumps(reporting, ensure_ascii=False)
        await self.db.commit()
        await self.db.refresh(team)
        row = await self.get_field_installation_team(team_id)
        assert row is not None
        return row

    async def update_field_installation_reporting(
        self,
        team_id: int,
        *,
        client_observations: Optional[str] = None,
        completion_photos: Optional[List[str]] = None,
        members_present: Optional[List[int]] = None,
        internal_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        team = await self._load_field_team(team_id)
        reporting = self._parse_reporting_json(team.reporting_json)

        if client_observations is not None:
            team.client_observations = client_observations
        if completion_photos is not None:
            reporting["completion_photos"] = [p for p in completion_photos if p and str(p).strip()]
        if internal_notes is not None:
            reporting["internal_notes"] = internal_notes
        if members_present is not None:
            now = datetime.now(timezone.utc).isoformat()
            present_payload = []
            for emp_id in members_present:
                emp = await self._get_active_employee(emp_id)
                present_payload.append(
                    {
                        "employee_id": emp.id,
                        "employee_name": emp.name,
                        "present_at": now,
                    }
                )
            reporting["members_present"] = present_payload

        team.reporting_json = json.dumps(reporting, ensure_ascii=False)
        await self.db.commit()
        await self.db.refresh(team)
        row = await self.get_field_installation_team(team_id)
        assert row is not None
        return row

    async def list_field_installation_teams(
        self, installation_ref: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        stmt = select(FieldInstallationTeam).order_by(FieldInstallationTeam.id.desc())
        if installation_ref:
            stmt = stmt.where(FieldInstallationTeam.installation_ref == installation_ref)
        teams = (await self.db.execute(stmt)).scalars().all()
        return [await self._serialize_field_installation_team(team) for team in teams]

    async def create_field_installation_team(
        self,
        installation_ref: str,
        member_employee_ids: Optional[List[int]] = None,
        *,
        site_address: Optional[str] = None,
        notes: Optional[str] = None,
        roles_on_site: Optional[Dict[int, str]] = None,
        status: str = "draft",
    ) -> Dict[str, Any]:
        if status not in FIELD_INSTALLATION_TEAM_STATUSES:
            raise ValueError("invalid_team_status")

        team = FieldInstallationTeam(
            installation_ref=installation_ref.strip(),
            status=status,
            site_address=site_address,
            notes=notes,
        )
        self.db.add(team)
        await self.db.flush()

        roles_on_site = roles_on_site or {}
        for emp_id in member_employee_ids or []:
            await self._get_active_employee(emp_id)
            self.db.add(
                FieldInstallationTeamMember(
                    team_id=team.id,
                    employee_id=emp_id,
                    role_on_site=roles_on_site.get(emp_id),
                )
            )
        await self.db.commit()
        await self.db.refresh(team)
        row = await self.get_field_installation_team(team.id)
        assert row is not None
        return row

    async def get_field_installation_team(self, team_id: int) -> Optional[Dict[str, Any]]:
        team = (
            await self.db.execute(
                select(FieldInstallationTeam).where(FieldInstallationTeam.id == team_id)
            )
        ).scalar_one_or_none()
        if team is None:
            return None
        return await self._serialize_field_installation_team(team)

    async def update_field_installation_team(
        self,
        team_id: int,
        *,
        status: Optional[str] = None,
        site_address: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        team = (
            await self.db.execute(
                select(FieldInstallationTeam).where(FieldInstallationTeam.id == team_id)
            )
        ).scalar_one_or_none()
        if team is None:
            raise ValueError("team_not_found")
        if status is not None:
            if status not in FIELD_INSTALLATION_TEAM_STATUSES:
                raise ValueError("invalid_team_status")
            team.status = status
        if site_address is not None:
            team.site_address = site_address
        if notes is not None:
            team.notes = notes
        await self.db.commit()
        await self.db.refresh(team)
        row = await self.get_field_installation_team(team_id)
        assert row is not None
        return row

    async def add_field_installation_team_member(
        self,
        team_id: int,
        employee_id: int,
        *,
        role_on_site: Optional[str] = None,
    ) -> Dict[str, Any]:
        team = (
            await self.db.execute(
                select(FieldInstallationTeam).where(FieldInstallationTeam.id == team_id)
            )
        ).scalar_one_or_none()
        if team is None:
            raise ValueError("team_not_found")

        await self._get_active_employee(employee_id)

        existing = (
            await self.db.execute(
                select(FieldInstallationTeamMember).where(
                    FieldInstallationTeamMember.team_id == team_id,
                    FieldInstallationTeamMember.employee_id == employee_id,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise ValueError("member_already_exists")

        self.db.add(
            FieldInstallationTeamMember(
                team_id=team_id,
                employee_id=employee_id,
                role_on_site=role_on_site,
            )
        )
        await self.db.commit()
        row = await self.get_field_installation_team(team_id)
        assert row is not None
        return row

    async def remove_field_installation_team_member(
        self, team_id: int, employee_id: int
    ) -> Dict[str, Any]:
        team = (
            await self.db.execute(
                select(FieldInstallationTeam).where(FieldInstallationTeam.id == team_id)
            )
        ).scalar_one_or_none()
        if team is None:
            raise ValueError("team_not_found")

        member = (
            await self.db.execute(
                select(FieldInstallationTeamMember).where(
                    FieldInstallationTeamMember.team_id == team_id,
                    FieldInstallationTeamMember.employee_id == employee_id,
                )
            )
        ).scalar_one_or_none()
        if member is None:
            raise ValueError("member_not_found")

        await self.db.delete(member)
        await self.db.commit()
        row = await self.get_field_installation_team(team_id)
        assert row is not None
        return row
