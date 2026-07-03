"""Employees router — CRUD for personal/angajati."""
import json
import logging
from datetime import datetime
from typing import Any, List, Optional

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from fastapi import APIRouter, Depends, HTTPException, Query
from models.auth import User
from schemas.auth import UserResponse
from pydantic import BaseModel
from services.employees import (
    EmployeesService,
    compute_cost_ora_calculat,
    is_valid_for_cost_engine,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

EMPLOYEE_MOBILE_ACCESS_ROLES = frozenset({"employee_mobile", "manager", "admin"})

router = APIRouter(
    prefix="/api/v1/entities/employees",
    tags=["employees"],
    dependencies=[Depends(get_current_user)],
)


class EmployeeData(BaseModel):
    name: str
    role: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = "active"
    employee_type: Optional[str] = "productive"
    user_id: Optional[str] = None
    cost_lunar_firma: Optional[float] = None
    monthly_internal_pay_amount: Optional[float] = None
    salary_currency: Optional[str] = "RON"
    salary_period: Optional[str] = "monthly"
    ore_lucru_luna: Optional[float] = None
    ore_productive_luna: Optional[float] = None
    skills: Optional[Any] = None
    machines: Optional[Any] = None
    data_angajare: Optional[datetime] = None
    observatii: Optional[str] = None


class EmployeeUpdateData(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None
    employee_type: Optional[str] = None
    user_id: Optional[str] = None
    cost_lunar_firma: Optional[float] = None
    monthly_internal_pay_amount: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[str] = None
    ore_lucru_luna: Optional[float] = None
    ore_productive_luna: Optional[float] = None
    skills: Optional[Any] = None
    machines: Optional[Any] = None
    data_angajare: Optional[datetime] = None
    observatii: Optional[str] = None


class EmployeeResponse(BaseModel):
    id: int
    name: str
    role: Optional[str] = None
    department: Optional[str] = None
    status: str
    employee_type: str
    user_id: Optional[str] = None
    auth_email: Optional[str] = None
    auth_role: Optional[str] = None
    is_linked_to_user: bool = False
    has_mobile_access: bool = False
    cost_lunar_firma: Optional[float] = None
    monthly_internal_pay_amount: Optional[float] = None
    salary_amount: Optional[float] = None
    salary_currency: Optional[str] = "RON"
    salary_period: Optional[str] = "monthly"
    ore_lucru_luna: Optional[float] = None
    ore_productive_luna: Optional[float] = None
    cost_ora_calculat: Optional[float] = None
    valid_for_cost_engine: bool = True
    skills: Optional[List[str]] = None
    machines: Optional[List[str]] = None
    data_angajare: Optional[datetime] = None
    observatii: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmployeeListResponse(BaseModel):
    items: List[EmployeeResponse]
    total: int
    skip: int
    limit: int


def _mobile_access_flags(
    user_id: Optional[str],
    status: str,
    user: User | None,
) -> tuple[bool, bool]:
    is_linked = bool((user_id or "").strip())
    has_mobile = (
        is_linked
        and status == "active"
        and user is not None
        and (user.role or "") in EMPLOYEE_MOBILE_ACCESS_ROLES
    )
    return is_linked, has_mobile


def _serialize(row, user: User | None = None) -> EmployeeResponse:
    def _parse_list(val: Optional[str]) -> Optional[List[str]]:
        if val is None:
            return None
        if isinstance(val, list):
            return val
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, list) else None
        except (TypeError, ValueError):
            return None

    user_id = getattr(row, "user_id", None)
    is_linked, has_mobile = _mobile_access_flags(user_id, row.status, user)

    return EmployeeResponse(
        id=row.id,
        name=row.name,
        role=row.role,
        department=row.department,
        status=row.status,
        employee_type=row.employee_type,
        user_id=user_id,
        auth_email=user.email if user else None,
        auth_role=user.role if user else None,
        is_linked_to_user=is_linked,
        has_mobile_access=has_mobile,
        cost_lunar_firma=row.cost_lunar_firma,
        monthly_internal_pay_amount=getattr(row, "monthly_internal_pay_amount", None),
        salary_amount=row.cost_lunar_firma,
        salary_currency=getattr(row, "salary_currency", None) or "RON",
        salary_period=getattr(row, "salary_period", None) or "monthly",
        ore_lucru_luna=row.ore_lucru_luna,
        ore_productive_luna=row.ore_productive_luna,
        cost_ora_calculat=compute_cost_ora_calculat(row.cost_lunar_firma, row.ore_productive_luna),
        valid_for_cost_engine=is_valid_for_cost_engine(row),
        skills=_parse_list(row.skills),
        machines=_parse_list(row.machines),
        data_angajare=row.data_angajare,
        observatii=row.observatii,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _users_by_id(db: AsyncSession, user_ids: set[str]) -> dict[str, User]:
    if not user_ids:
        return {}
    result = await db.execute(select(User).where(User.id.in_(user_ids)))
    return {user.id: user for user in result.scalars().all()}


async def _user_for_employee(db: AsyncSession, user_id: Optional[str]) -> User | None:
    if not (user_id or "").strip():
        return None
    return await db.get(User, user_id)


@router.get("", response_model=EmployeeListResponse)
async def list_employees(
    query: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
):
    svc = EmployeesService(db)
    query_dict = None
    if query:
        try:
            query_dict = json.loads(query)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid query JSON format")
    result = await svc.get_list(skip=skip, limit=limit, query_dict=query_dict, sort=sort)
    user_ids = {
        (getattr(row, "user_id", None) or "").strip()
        for row in result["items"]
        if getattr(row, "user_id", None)
    }
    users_by_id = await _users_by_id(db, user_ids)
    return EmployeeListResponse(
        items=[
            _serialize(r, users_by_id.get((getattr(r, "user_id", None) or "").strip()))
            for r in result["items"]
        ],
        total=result["total"],
        skip=result["skip"],
        limit=result["limit"],
    )


@router.get("/{id}", response_model=EmployeeResponse)
async def get_employee(id: int, db: AsyncSession = Depends(get_db)):
    svc = EmployeesService(db)
    row = await svc.get_by_id(id)
    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")
    user = await _user_for_employee(db, getattr(row, "user_id", None))
    return _serialize(row, user)


@router.post("", response_model=EmployeeResponse, status_code=201)
async def create_employee(data: EmployeeData, db: AsyncSession = Depends(get_db), _user: UserResponse = Depends(require_permission("employee.create"))):
    svc = EmployeesService(db)
    try:
        row = await svc.create(data.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    user = await _user_for_employee(db, getattr(row, "user_id", None))
    return _serialize(row, user)


@router.put("/{id}", response_model=EmployeeResponse)
async def update_employee(id: int, data: EmployeeUpdateData, db: AsyncSession = Depends(get_db), _user: UserResponse = Depends(require_permission("employee.update"))):
    svc = EmployeesService(db)
    try:
        row = await svc.update(id, data.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")
    user = await _user_for_employee(db, getattr(row, "user_id", None))
    return _serialize(row, user)


@router.delete("/{id}")
async def delete_employee(id: int, db: AsyncSession = Depends(get_db), _user: UserResponse = Depends(require_permission("employee.delete"))):
    svc = EmployeesService(db)
    ok = await svc.delete(id)
    if not ok:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee deleted successfully", "id": id}