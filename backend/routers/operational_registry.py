"""Operational Workforce & Resource Registry API.

Admin/read endpoints for the canonical employee + resource registry.
Consumption surfaces (/operator, /tablet, montaj) read from here — they
do NOT own employee or machine data.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from schemas.auth import UserResponse
from services.operational_registry_service import OperationalRegistryService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/operational-registry",
    tags=["operational-registry"],
    dependencies=[Depends(get_current_user)],
)


class EmployeeAuthorizationsUpdate(BaseModel):
    skill_codes: Optional[List[str]] = None
    workcenter_codes: Optional[List[str]] = None
    resource_codes: Optional[List[str]] = None


class OperationMappingData(BaseModel):
    operation_code: str
    required_skill_codes: Optional[List[str]] = None
    allowed_workcenter_codes: Optional[List[str]] = None
    allowed_resource_codes: Optional[List[str]] = None
    authorization_mode: Optional[str] = "hybrid"
    default_resource_code: Optional[str] = None
    product_system_aliases: Optional[List[str]] = None
    authorized_employee_ids: Optional[List[int]] = None
    notes: Optional[str] = None


class ResourceUpsertData(BaseModel):
    machine_code: str
    name: str
    machine_type: str
    resource_kind: str = "machine"
    workcenter_code: Optional[str] = None
    description: Optional[str] = None
    operational_status: str = "active"
    is_available: bool = True
    is_active: bool = True
    capabilities: Optional[List[str]] = None
    capacity_metadata: Optional[Dict[str, Any]] = None


class FieldInstallationTeamCreate(BaseModel):
    installation_ref: str
    member_employee_ids: List[int] = Field(default_factory=list)
    site_address: Optional[str] = None
    notes: Optional[str] = None
    roles_on_site: Optional[Dict[int, str]] = None
    status: str = "draft"


class FieldInstallationTeamUpdate(BaseModel):
    status: Optional[str] = None
    site_address: Optional[str] = None
    notes: Optional[str] = None


class FieldInstallationTeamMemberAdd(BaseModel):
    employee_id: int
    role_on_site: Optional[str] = None


class FieldInstallationStartReporting(BaseModel):
    started_by_employee_id: Optional[int] = None
    members_present: Optional[List[int]] = None


class FieldInstallationMaterialConsumed(BaseModel):
    material_name: str
    quantity: float
    unit: str = "buc"
    reported_by_employee_id: Optional[int] = None
    consumption_notes: Optional[str] = None


class FieldInstallationCompleteReporting(BaseModel):
    client_observations: Optional[str] = None
    completion_photos: Optional[List[str]] = None
    internal_notes: Optional[str] = None
    members_present: Optional[List[int]] = None
    materials_consumed: Optional[List[FieldInstallationMaterialConsumed]] = None
    completed_by_employee_id: Optional[int] = None


class FieldInstallationUpdateReporting(BaseModel):
    client_observations: Optional[str] = None
    completion_photos: Optional[List[str]] = None
    members_present: Optional[List[int]] = None
    internal_notes: Optional[str] = None


def _map_team_service_error(exc: ValueError) -> HTTPException:
    code = str(exc)
    status = 404 if code.endswith("_not_found") else 422
    return HTTPException(status_code=status, detail=code)


@router.get("/catalog")
async def get_operational_catalog(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    return await svc.get_catalog()


@router.get("/employees")
async def list_registry_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    return await svc.list_employees_with_authorizations(skip=skip, limit=limit)


@router.get("/employees/{employee_id}")
async def get_registry_employee(employee_id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    row = await svc.get_employee_registry(employee_id)
    if row is None:
        raise HTTPException(status_code=404, detail="employee_not_found")
    return row


@router.put("/employees/{employee_id}/authorizations")
async def update_employee_authorizations(
    employee_id: int,
    data: EmployeeAuthorizationsUpdate,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("employee.update")),
) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    existing = await svc.get_employee_registry(employee_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="employee_not_found")
    auth = await svc.set_employee_authorizations(
        employee_id,
        skill_codes=data.skill_codes,
        workcenter_codes=data.workcenter_codes,
        resource_codes=data.resource_codes,
    )
    return {"employee_id": employee_id, **auth}


@router.put("/resources")
async def upsert_registry_resource(
    data: ResourceUpsertData,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("employee.update")),
) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    row = await svc.upsert_resource(data.model_dump())
    mapped = await svc.get_resource(row.machine_code)
    return mapped or {"resource_code": row.machine_code}


@router.get("/resources")
async def list_registry_resources(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    items = await svc.list_resources()
    return {"items": items, "total": len(items)}


@router.get("/resources/{resource_code}")
async def get_registry_resource(resource_code: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    row = await svc.get_resource(resource_code)
    if row is None:
        raise HTTPException(status_code=404, detail="resource_not_found")
    return row


@router.get("/resources/{resource_code}/authorized-employees")
async def list_authorized_employees_for_resource(
    resource_code: str, db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    items = await svc.get_authorized_employees_for_resource(resource_code)
    return {"resource_code": resource_code, "items": items, "total": len(items)}


@router.get("/operation-mappings/{operation_code}/eligible-employees")
async def list_eligible_employees_for_operation(
    operation_code: str,
    machine_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    result = await svc.get_eligible_employees_for_operation(
        operation_code, machine_type=machine_type
    )
    from services.parity_observe.eligibility_endpoint import observe_eligible_employees_endpoint

    await observe_eligible_employees_endpoint(
        db, operation_code, result, machine_type=machine_type
    )
    return result


@router.get("/operation-mappings/{operation_code}/resolve")
async def resolve_operation_mapping(
    operation_code: str, db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    row = await svc.resolve_operation_mapping(operation_code)
    if row is None:
        raise HTTPException(status_code=404, detail="operation_mapping_not_found")
    return row


@router.get("/operation-mappings")
async def list_operation_mappings(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    items = await svc.list_operation_mappings()
    return {"items": items, "total": len(items)}


@router.get("/operation-mappings/{operation_code}")
async def get_operation_mapping(operation_code: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    row = await svc.get_operation_mapping(operation_code)
    if row is None:
        raise HTTPException(status_code=404, detail="operation_mapping_not_found")
    return row


@router.put("/operation-mappings")
async def upsert_operation_mapping(
    data: OperationMappingData,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("employee.update")),
) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    row = await svc.upsert_operation_mapping(data.model_dump())
    mapped = await svc.get_operation_mapping(row.operation_code)
    return mapped or {"operation_code": row.operation_code}


@router.get("/field-installation-teams")
async def list_field_installation_teams(
    installation_ref: Optional[str] = Query(None),
    order_id: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    from services.operational_registry_service import build_order_installation_ref

    svc = OperationalRegistryService(db)
    ref = installation_ref
    if order_id is not None:
        ref = build_order_installation_ref(order_id)
    items = await svc.list_field_installation_teams(ref)
    return {"items": items, "total": len(items), "installation_ref": ref}


@router.post("/field-installation-teams", status_code=201)
async def create_field_installation_team(
    data: FieldInstallationTeamCreate,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    try:
        return await svc.create_field_installation_team(
            data.installation_ref,
            data.member_employee_ids,
            site_address=data.site_address,
            notes=data.notes,
            roles_on_site=data.roles_on_site,
            status=data.status,
        )
    except ValueError as exc:
        raise _map_team_service_error(exc) from exc


@router.get("/field-installation-teams/{team_id}")
async def get_field_installation_team(team_id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    row = await svc.get_field_installation_team(team_id)
    if row is None:
        raise HTTPException(status_code=404, detail="team_not_found")
    return row


@router.patch("/field-installation-teams/{team_id}")
async def update_field_installation_team(
    team_id: int,
    data: FieldInstallationTeamUpdate,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    try:
        return await svc.update_field_installation_team(
            team_id,
            status=data.status,
            site_address=data.site_address,
            notes=data.notes,
        )
    except ValueError as exc:
        raise _map_team_service_error(exc) from exc


@router.post("/field-installation-teams/{team_id}/members", status_code=201)
async def add_field_installation_team_member(
    team_id: int,
    data: FieldInstallationTeamMemberAdd,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    try:
        return await svc.add_field_installation_team_member(
            team_id,
            data.employee_id,
            role_on_site=data.role_on_site,
        )
    except ValueError as exc:
        raise _map_team_service_error(exc) from exc


@router.delete("/field-installation-teams/{team_id}/members/{employee_id}")
async def remove_field_installation_team_member(
    team_id: int,
    employee_id: int,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    try:
        return await svc.remove_field_installation_team_member(team_id, employee_id)
    except ValueError as exc:
        raise _map_team_service_error(exc) from exc


@router.post("/field-installation-teams/{team_id}/start-reporting")
async def start_field_installation_reporting(
    team_id: int,
    data: FieldInstallationStartReporting,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    try:
        return await svc.start_field_installation_reporting(
            team_id,
            started_by_employee_id=data.started_by_employee_id,
            members_present=data.members_present,
        )
    except ValueError as exc:
        raise _map_team_service_error(exc) from exc


@router.post("/field-installation-teams/{team_id}/complete-reporting")
async def complete_field_installation_reporting(
    team_id: int,
    data: FieldInstallationCompleteReporting,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    try:
        materials = (
            [m.model_dump() for m in data.materials_consumed]
            if data.materials_consumed
            else None
        )
        return await svc.complete_field_installation_reporting(
            team_id,
            client_observations=data.client_observations,
            completion_photos=data.completion_photos,
            internal_notes=data.internal_notes,
            members_present=data.members_present,
            materials_consumed=materials,
            completed_by_employee_id=data.completed_by_employee_id,
        )
    except ValueError as exc:
        raise _map_team_service_error(exc) from exc


@router.patch("/field-installation-teams/{team_id}/reporting")
async def update_field_installation_reporting(
    team_id: int,
    data: FieldInstallationUpdateReporting,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    svc = OperationalRegistryService(db)
    try:
        return await svc.update_field_installation_reporting(
            team_id,
            client_observations=data.client_observations,
            completion_photos=data.completion_photos,
            members_present=data.members_present,
            internal_notes=data.internal_notes,
        )
    except ValueError as exc:
        raise _map_team_service_error(exc) from exc
