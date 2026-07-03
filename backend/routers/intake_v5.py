"""Intake V5 router — simplified end-to-end flow.

Endpoints:
  POST   /analyze-svg        → parse SVG, extract geometry
  POST   /calculate          → preview BOM (no save)
  POST   /projects           → create project
  GET    /projects           → list projects
  GET    /projects/{id}      → get project + BOM
  PUT    /projects/{id}      → update inputs
  POST   /projects/{id}/quote  → create quote
  POST   /projects/{id}/order  → create order
  POST   /projects/{id}/tasks  → generate tasks
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import db_manager
from schemas.intake_v5 import (
    BomResult,
    IntakeV5CreateRequest,
    IntakeV5Inputs,
    IntakeV5ListItem,
    IntakeV5ProjectResponse,
    IntakeV5UpdateRequest,
)
from services import intake_v5_service as svc
from services.svg_analyzer import analyze_svg

router = APIRouter(prefix="/api/v1/intake-v5", tags=["intake-v5"])


async def _get_db():
    async with db_manager.async_session_maker() as session:
        yield session


# ── SVG Analysis ──

@router.get("/config")
async def get_config(db: AsyncSession = Depends(_get_db)):
    """Return template options and DB pricing readiness for the simplified V5 form."""
    return await svc.get_template_config(db)


# ── SVG Analysis ──

@router.post("/analyze-svg")
async def analyze_svg_endpoint(file: UploadFile = File(...)):
    """Parse an SVG file and return extracted geometry for auto-fill."""
    if not file.filename or not file.filename.lower().endswith(".svg"):
        from fastapi import HTTPException
        raise HTTPException(400, "Doar fișiere SVG sunt acceptate.")
    content = await file.read()
    if len(content) > 10_000_000:  # 10 MB limit
        from fastapi import HTTPException
        raise HTTPException(400, "Fișierul SVG depășește limita de 10 MB.")
    svg_text = content.decode("utf-8", errors="replace")
    return analyze_svg(svg_text, file.filename)


# ── BOM Preview (no save) ──

@router.post("/calculate", response_model=BomResult)
async def calculate_bom(
    inputs: IntakeV5Inputs,
    db: AsyncSession = Depends(_get_db),
):
    """Preview BOM from inputs — no project created."""
    return await svc.preview_bom(db, inputs)


# ── Project CRUD ──

@router.post("/projects", response_model=IntakeV5ProjectResponse)
async def create_project(
    req: IntakeV5CreateRequest,
    db: AsyncSession = Depends(_get_db),
):
    project = await svc.create_project(db, req.client_name, req.job_title, req.inputs)
    return _to_response(project)


@router.get("/projects", response_model=list[IntakeV5ListItem])
async def list_projects(db: AsyncSession = Depends(_get_db)):
    projects = await svc.list_projects(db)
    return [_to_list_item(p) for p in projects]


@router.get("/projects/{project_id}", response_model=IntakeV5ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(_get_db),
):
    project = await svc.get_project(db, project_id)
    return _to_response(project)


@router.put("/projects/{project_id}", response_model=IntakeV5ProjectResponse)
async def update_project(
    project_id: int,
    req: IntakeV5UpdateRequest,
    db: AsyncSession = Depends(_get_db),
):
    project = await svc.update_project(
        db, project_id, req.client_name, req.job_title, req.inputs,
    )
    return _to_response(project)


# ── Flow actions ──

@router.post("/projects/{project_id}/quote")
async def create_quote(
    project_id: int,
    db: AsyncSession = Depends(_get_db),
):
    return await svc.create_quote(db, project_id)


@router.post("/projects/{project_id}/order")
async def create_order(
    project_id: int,
    db: AsyncSession = Depends(_get_db),
):
    return await svc.create_order(db, project_id)


@router.post("/projects/{project_id}/tasks")
async def generate_tasks(
    project_id: int,
    db: AsyncSession = Depends(_get_db),
):
    return await svc.generate_tasks(db, project_id)


# ── Helpers ──

def _to_response(p) -> IntakeV5ProjectResponse:
    return IntakeV5ProjectResponse(
        id=p.id,
        code=p.code,
        template_code=p.template_code,
        status=p.status,
        client_name=p.client_name,
        job_title=p.job_title,
        inputs=IntakeV5Inputs.model_validate_json(p.inputs_json),
        bom=BomResult.model_validate_json(p.bom_json) if p.bom_json else None,
        material_total_eur=p.material_total_eur,
        operation_total_eur=p.operation_total_eur,
        grand_total_eur=p.grand_total_eur,
        quote_id=p.quote_id,
        order_id=p.order_id,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _to_list_item(p) -> IntakeV5ListItem:
    return IntakeV5ListItem(
        id=p.id,
        code=p.code,
        status=p.status,
        client_name=p.client_name,
        job_title=p.job_title,
        grand_total_eur=p.grand_total_eur,
        quote_id=p.quote_id,
        order_id=p.order_id,
        created_at=p.created_at,
    )
