"""Dev-only reproducible fixture for Employee Mobile — Sandu tasks + intake work-file.

Manual script target; not invoked at app startup or in migrations.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.environment import get_runtime_environment, is_development_environment
from dependencies.permissions import VALID_ROLES
from models.auth import User
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.intake_requests import Intake_requests
from models.orders import Orders
from models.quotes import Quotes
from services.execution_task_assignment_service import assign_plan_task
from services.production_document_handoff_service import (
    attach_documents_to_planned_tasks,
    load_eligible_intake_documents_for_plan,
)
from services.task_dependency_rules_service import backfill_plan_task_dependencies
from services.volumetric_return_task_taxonomy_service import (
    apply_volumetric_return_taxonomy_to_plan_tasks,
)
from services.work_intake_work_file_service import STORAGE_ROOT, _work_file_download_path
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from validators.intake_product_spec import validate_intake_product_spec

SANDU_USER_ID = "dev-sandu-employee-001"
SANDU_EMAIL = "sandu.employee@local"
SANDU_NAME = "Putaru Sandu"
SANDU_EMPLOYEE_NAME = "Putaru Sandu"
SANDU_USER_ROLE = "employee_mobile"
DEV_PREPARED_BY_USER_ID = "dev-admin-user-00000000"

FIXTURE_INTAKE_CODE = "WI-E2E-COMMERCIAL-001"
PREFERRED_ORDER_ID = 1
SANDU_TASK_IDS: Tuple[str, ...] = ("T-004", "T-006", "T-007", "T-008", "T-009", "T-010")
CALIN_TASK_ID = "T-001"
SANDU_SMOKE_INSTRUCTION_TASK_ID = "T-008"
SANDU_SMOKE_INSTRUCTION_TEXT = (
    "Vezi schița atașată. Pregătește barele conform cotei din desen "
    "și verifică poziționarea înainte de montaj."
)

WORK_FILE_ID = "sandu-sketch-001"
WORK_FILE_DISPLAY_NAME = "Schiță litere volumetrice.svg"
WORK_FILE_STORED_NAME = "sandu-sketch-001_Schita_litere_volumetrice.svg"
MINIMAL_DEV_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="100">'
    '<rect width="240" height="100" fill="#eef2f7" stroke="#94a3b8"/>'
    '<text x="12" y="56" font-family="sans-serif" font-size="14">Dev production sketch</text>'
    "</svg>"
)


@dataclass
class DevSanduFixtureConfig:
    apply: bool = False
    force_non_sqlite: bool = False


@dataclass
class DevSanduFixtureResult:
    success: bool
    dry_run: bool
    actions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    sandu_employee_id: Optional[int] = None
    user_id: Optional[str] = None
    order_id: Optional[int] = None
    intake_code: Optional[str] = None
    assigned_task_ids: List[str] = field(default_factory=list)
    work_file_id: Optional[str] = None
    work_file_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def assert_dev_fixture_environment(config: DevSanduFixtureConfig) -> Optional[str]:
    env = get_runtime_environment()
    if env in {"staging", "production"}:
        return f"refusing_fixture_in_{env}"

    if not is_development_environment():
        return "refusing_fixture_outside_dev_environments"

    db_url = os.environ.get("DATABASE_URL", "").strip().lower()
    if not db_url:
        return "database_url_missing"

    looks_local = "sqlite" in db_url or "dev.db" in db_url or "local_dev.db" in db_url
    if not looks_local and not config.force_non_sqlite:
        return "database_url_not_local_sqlite_set_WORKOS_DEV_SANDU_FIXTURE_FORCE=1_with_--apply"
    return None


def build_work_file_attachment_metadata(
    *,
    intake_code: str,
    stored_file_name: str = WORK_FILE_STORED_NAME,
    size_bytes: int = 0,
) -> dict[str, Any]:
    uploaded_at = datetime.now(timezone.utc).isoformat()
    return {
        "id": WORK_FILE_ID,
        "fileName": WORK_FILE_DISPLAY_NAME,
        "storedFileName": stored_file_name,
        "fileUrl": _work_file_download_path(intake_code, WORK_FILE_ID),
        "mimeType": "image/svg+xml",
        "extension": ".svg",
        "sizeBytes": size_bytes,
        "role": "master_work_file",
        "usableFor": ["general_production", "mounting", "modeling"],
        "uploadedAt": uploaded_at,
        "isPrimary": True,
    }


_CANONICAL_WORK_FILE_KEYS = frozenset({
    "id",
    "fileName",
    "fileUrl",
    "storedFileName",
    "mimeType",
    "extension",
    "sizeBytes",
    "role",
    "usableFor",
    "isPrimary",
})


def merge_work_file_attachment_into_spec(
    product_spec: dict[str, Any],
    attachment: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    """Return merged spec and action label (added|updated|unchanged)."""
    spec = dict(product_spec or {})
    rows_raw = spec.get("workFileAttachments")
    rows: list[dict[str, Any]] = []
    if isinstance(rows_raw, list):
        rows = [dict(item) for item in rows_raw if isinstance(item, dict)]

    existing = next((row for row in rows if str(row.get("id") or "") == WORK_FILE_ID), None)
    if existing is None:
        for row in rows:
            row["isPrimary"] = False
        rows.append(dict(attachment))
        spec["workFileAttachments"] = rows
        return spec, "added"

    merged = dict(existing)
    changed = False
    for key in _CANONICAL_WORK_FILE_KEYS:
        if key not in attachment:
            continue
        value = attachment[key]
        if key == "uploadedAt" and existing.get("uploadedAt"):
            continue
        left = merged.get(key)
        right = value
        if key == "sizeBytes":
            try:
                left = int(left) if left is not None else None
                right = int(right) if right is not None else None
            except (TypeError, ValueError):
                pass
        if left != right:
            merged[key] = value
            changed = True

    if not changed:
        return spec, "unchanged"

    updated_rows = []
    for row in rows:
        if str(row.get("id") or "") == WORK_FILE_ID:
            updated_rows.append(merged)
        else:
            updated_rows.append(row)
    spec["workFileAttachments"] = updated_rows
    return spec, "updated"


def plan_sandu_task_assignment_actions(
    tasks: list,
    *,
    sandu_employee_id: int,
    reality_lookup: dict[str, dict],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    task_by_id = {
        str(t.get("task_id")): t for t in tasks if isinstance(t, dict) and t.get("task_id")
    }

    for task_id in SANDU_TASK_IDS:
        entry = task_by_id.get(task_id)
        if entry is None:
            actions.append({"task_id": task_id, "action": "missing", "reason": "task_not_in_plan"})
            continue

        current = entry.get("assigned_employee_id")
        try:
            current_int = int(current) if current is not None else None
        except (TypeError, ValueError):
            current_int = None

        if current_int == sandu_employee_id:
            actions.append({"task_id": task_id, "action": "skip", "reason": "already_assigned_to_sandu"})
            continue

        if task_id == CALIN_TASK_ID:
            actions.append({"task_id": task_id, "action": "skip", "reason": "calin_task_protected"})
            continue

        rt = reality_lookup.get(task_id, {})
        status = str(rt.get("status") or "").strip().lower()
        if rt.get("ended_at") or status in {"done", "completed"}:
            actions.append({"task_id": task_id, "action": "skip", "reason": "task_completed"})
            continue
        if status in {"started", "blocked"}:
            actions.append(
                {
                    "task_id": task_id,
                    "action": "warn",
                    "reason": f"task_status_{status}",
                    "current_assignee": current_int,
                }
            )
            continue

        if current_int is not None and current_int != sandu_employee_id:
            actions.append(
                {
                    "task_id": task_id,
                    "action": "assign",
                    "reason": "reassign_to_sandu",
                    "from_employee_id": current_int,
                    "to_employee_id": sandu_employee_id,
                }
            )
        else:
            actions.append(
                {
                    "task_id": task_id,
                    "action": "assign",
                    "reason": "assign_to_sandu",
                    "to_employee_id": sandu_employee_id,
                }
            )
    return actions


def plan_document_backfill_action(
    tasks: list,
    *,
    documents: list[dict[str, Any]],
) -> tuple[list, str]:
    """Idempotently attach eligible documents to every planned task."""
    if not documents:
        return tasks, "no_documents"

    task_dicts = [dict(t) for t in tasks if isinstance(t, dict)]
    before = json.dumps(task_dicts, sort_keys=True)
    updated = attach_documents_to_planned_tasks(task_dicts, documents)
    after = json.dumps(updated, sort_keys=True)
    if before == after:
        return updated, "unchanged"
    return updated, "updated"


def plan_smoke_instruction_action(
    tasks: list,
    *,
    task_id: str,
    instructions: str,
) -> tuple[list, str]:
    normalized = (instructions or "").strip()
    updated: list = []
    found = False
    changed = False
    for entry in tasks:
        if not isinstance(entry, dict):
            updated.append(entry)
            continue
        row = dict(entry)
        if str(row.get("task_id")) != task_id:
            updated.append(row)
            continue
        found = True
        current = str(row.get("instructions") or "").strip()
        if normalized:
            if current != normalized:
                row["instructions"] = normalized
                changed = True
        elif "instructions" in row:
            del row["instructions"]
            changed = True
        updated.append(row)

    if not found:
        return tasks, "task_missing"
    if not changed:
        return updated, "unchanged"
    return updated, "updated"


async def _find_sandu_employee(db: AsyncSession) -> tuple[Optional[Employees], Optional[str]]:
    rows = (
        await db.execute(
            select(Employees).where(Employees.name == SANDU_EMPLOYEE_NAME)
        )
    ).scalars().all()
    if len(rows) > 1:
        return None, "multiple_employees_named_putaru_sandu"
    if not rows:
        return None, "sandu_employee_not_found"
    return rows[0], None


async def _resolve_target_order(db: AsyncSession) -> tuple[Optional[int], Optional[str], Optional[str]]:
    order = await db.get(Orders, PREFERRED_ORDER_ID)
    if order is not None:
        quote = await db.get(Quotes, order.quote_id) if order.quote_id else None
        intake_code = (quote.intake_code if quote else "") or FIXTURE_INTAKE_CODE
        if intake_code == FIXTURE_INTAKE_CODE:
            return order.id, intake_code, None
        return None, None, f"order_{PREFERRED_ORDER_ID}_intake_mismatch:{intake_code}"

    quote = (
        await db.execute(select(Quotes).where(Quotes.intake_code == FIXTURE_INTAKE_CODE))
    ).scalar_one_or_none()
    if quote is None:
        return None, None, "fixture_intake_quote_not_found"

    order_row = (
        await db.execute(select(Orders).where(Orders.quote_id == quote.id))
    ).scalar_one_or_none()
    if order_row is None:
        return None, None, "fixture_order_not_found_for_intake"
    return order_row.id, FIXTURE_INTAKE_CODE, None


def _parse_tasks_json(raw: Any) -> list:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str) and raw.strip():
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    return []


def _reality_lookup(raw: Any) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for item in _parse_tasks_json(raw):
        if isinstance(item, dict) and item.get("task_id"):
            lookup[str(item["task_id"])] = item
    return lookup


async def seed_dev_employee_mobile_sandu_fixture(
    db: AsyncSession,
    config: DevSanduFixtureConfig,
) -> DevSanduFixtureResult:
    result = DevSanduFixtureResult(success=False, dry_run=not config.apply)

    env_error = assert_dev_fixture_environment(config)
    if env_error:
        result.errors.append(env_error)
        return result

    # --- User ---
    user = await db.get(User, SANDU_USER_ID)
    if user is None:
        by_email = (
            await db.execute(select(User).where(func.lower(User.email) == SANDU_EMAIL.lower()))
        ).scalar_one_or_none()
        if by_email:
            result.errors.append("email_exists_with_different_user_id")
            return result
        if config.apply:
            user = User(id=SANDU_USER_ID, email=SANDU_EMAIL, name=SANDU_NAME, role=SANDU_USER_ROLE)
            db.add(user)
            await db.flush()
            result.actions.append("user_created")
        else:
            result.actions.append("dry_run_would_create_user")
    else:
        result.actions.append("user_exists")
        updates = {}
        if user.email != SANDU_EMAIL:
            updates["email"] = SANDU_EMAIL
        if user.name != SANDU_NAME:
            updates["name"] = SANDU_NAME
        if user.role != SANDU_USER_ROLE:
            updates["role"] = SANDU_USER_ROLE
        if updates:
            if config.apply:
                for key, val in updates.items():
                    setattr(user, key, val)
                await db.flush()
                result.actions.append(f"user_updated:{','.join(sorted(updates))}")
            else:
                result.actions.append(f"dry_run_would_update_user:{','.join(sorted(updates))}")

    result.user_id = SANDU_USER_ID

    if SANDU_USER_ROLE not in VALID_ROLES:
        result.errors.append(f"invalid_role:{SANDU_USER_ROLE}")
        return result

    # --- Employee link ---
    sandu, sandu_error = await _find_sandu_employee(db)
    if sandu_error:
        result.errors.append(sandu_error)
        return result
    assert sandu is not None
    result.sandu_employee_id = sandu.id

    if sandu.user_id != SANDU_USER_ID:
        if config.apply:
            sandu.user_id = SANDU_USER_ID
            await db.flush()
            result.actions.append("employee_user_id_linked")
        else:
            result.actions.append("dry_run_would_link_employee_user_id")
    else:
        result.actions.append("employee_user_id_ok")

    if sandu.status != "active":
        result.warnings.append(f"sandu_status_{sandu.status}")

    # --- Order / plan ---
    order_id, intake_code, order_error = await _resolve_target_order(db)
    if order_error:
        result.errors.append(order_error)
        return result
    assert order_id is not None and intake_code is not None
    result.order_id = order_id
    result.intake_code = intake_code

    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    if plan is None:
        result.errors.append("execution_plan_not_found")
        return result

    reality = (
        await db.execute(select(ExecutionReality).where(ExecutionReality.order_id == order_id))
    ).scalar_one_or_none()
    tasks = _parse_tasks_json(plan.tasks_json)
    assignment_actions = plan_sandu_task_assignment_actions(
        tasks,
        sandu_employee_id=sandu.id,
        reality_lookup=_reality_lookup(reality.tasks_json if reality else None),
    )

    assigned: list[str] = []
    for action in assignment_actions:
        task_id = action["task_id"]
        act = action["action"]
        if act == "missing":
            result.warnings.append(f"{task_id}:missing_from_plan")
            continue
        if act == "skip":
            if action.get("reason") == "already_assigned_to_sandu":
                assigned.append(task_id)
            continue
        if act == "warn":
            result.warnings.append(f"{task_id}:{action.get('reason')}")
            continue
        if act == "assign":
            if config.apply:
                await assign_plan_task(
                    db,
                    order_id=order_id,
                    task_id=task_id,
                    assigned_employee_id=sandu.id,
                )
                result.actions.append(f"assigned:{task_id}")
            else:
                result.actions.append(f"dry_run_would_assign:{task_id}")
            assigned.append(task_id)

    result.assigned_task_ids = sorted(set(assigned))

    # --- Intake work-file ---
    intake = (
        await db.execute(select(Intake_requests).where(Intake_requests.code == intake_code))
    ).scalar_one_or_none()
    if intake is None:
        result.errors.append("intake_not_found")
        return result

    existing_spec: dict[str, Any] = {}
    if intake.product_spec_json:
        try:
            parsed = json.loads(intake.product_spec_json)
            if isinstance(parsed, dict):
                existing_spec = parsed
        except json.JSONDecodeError:
            result.warnings.append("intake_product_spec_json_invalid_will_replace_attachment_section")

    storage_dir = STORAGE_ROOT / intake_code
    existing_rows = existing_spec.get("workFileAttachments")
    stored_name = WORK_FILE_STORED_NAME
    if isinstance(existing_rows, list):
        match = next(
            (
                row
                for row in existing_rows
                if isinstance(row, dict) and str(row.get("id") or "") == WORK_FILE_ID
            ),
            None,
        )
        if match and match.get("storedFileName"):
            stored_name = str(match["storedFileName"])

    storage_path = storage_dir / stored_name
    svg_bytes = MINIMAL_DEV_SVG.encode("utf-8")
    size_bytes = len(svg_bytes)

    if storage_path.is_file():
        size_bytes = storage_path.stat().st_size
        result.actions.append("work_file_exists_on_disk")
    elif config.apply:
        storage_dir.mkdir(parents=True, exist_ok=True)
        storage_path.write_bytes(svg_bytes)
        result.actions.append("work_file_written")
    else:
        result.actions.append("dry_run_would_write_work_file")

    attachment = build_work_file_attachment_metadata(
        intake_code=intake_code,
        stored_file_name=stored_name,
        size_bytes=size_bytes,
    )
    merged_spec, merge_action = merge_work_file_attachment_into_spec(existing_spec, attachment)
    if merge_action == "unchanged":
        result.actions.append("work_file_metadata_unchanged")
    elif config.apply:
        validated = validate_intake_product_spec(merged_spec) or {}
        intake.product_spec_json = json.dumps(validated, ensure_ascii=False)
        await db.flush()
        result.actions.append(f"work_file_metadata_{merge_action}")
    else:
        result.actions.append(f"dry_run_would_{merge_action}_work_file_metadata")

    result.work_file_id = WORK_FILE_ID
    result.work_file_path = str(storage_path)

    # --- Existing plan backfill: documents on tasks + smoke instruction (dev-only) ---
    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    if plan is None:
        result.errors.append("execution_plan_not_found_for_backfill")
    else:
        tasks = _parse_tasks_json(plan.tasks_json)
        eligible_docs = await load_eligible_intake_documents_for_plan(
            db,
            order_id=order_id,
            intake_code=intake_code,
        )
        tasks, doc_action = plan_document_backfill_action(tasks, documents=eligible_docs)
        if doc_action == "updated":
            result.actions.append("plan_documents_backfilled" if config.apply else "dry_run_would_backfill_plan_documents")
        elif doc_action == "unchanged" and eligible_docs:
            result.actions.append("plan_documents_ok")

        tasks, tax_action = apply_volumetric_return_taxonomy_to_plan_tasks(
            tasks,
            set_owner_instructions=True,
        )
        if tax_action == "updated":
            result.actions.append(
                "plan_return_taxonomy_fixed" if config.apply else "dry_run_would_fix_return_taxonomy"
            )
        elif tax_action == "unchanged":
            result.actions.append("plan_return_taxonomy_ok")

        tasks, dep_action = backfill_plan_task_dependencies(tasks)
        if dep_action == "updated":
            result.actions.append(
                "plan_dependencies_backfilled" if config.apply else "dry_run_would_backfill_plan_dependencies"
            )
        elif dep_action == "unchanged":
            result.actions.append("plan_dependencies_ok")

        tasks, instr_action = plan_smoke_instruction_action(
            tasks,
            task_id=SANDU_SMOKE_INSTRUCTION_TASK_ID,
            instructions=SANDU_SMOKE_INSTRUCTION_TEXT,
        )
        if instr_action == "updated":
            result.actions.append(
                f"plan_instruction_set:{SANDU_SMOKE_INSTRUCTION_TASK_ID}"
                if config.apply
                else f"dry_run_would_set_instruction:{SANDU_SMOKE_INSTRUCTION_TASK_ID}"
            )
        elif instr_action == "unchanged":
            result.actions.append(f"plan_instruction_ok:{SANDU_SMOKE_INSTRUCTION_TASK_ID}")
        elif instr_action == "task_missing":
            result.warnings.append(f"{SANDU_SMOKE_INSTRUCTION_TASK_ID}:missing_from_plan")

        plan_dirty = (
            doc_action == "updated"
            or tax_action == "updated"
            or dep_action == "updated"
            or instr_action == "updated"
        )
        if plan_dirty and config.apply:
            plan.tasks_json = json.dumps(tasks)
            await db.flush()

        current_prepared = str(getattr(plan, "prepared_by_user_id", None) or "").strip()
        if current_prepared != DEV_PREPARED_BY_USER_ID:
            if config.apply:
                plan.prepared_by_user_id = DEV_PREPARED_BY_USER_ID
                await db.flush()
                result.actions.append("plan_prepared_by_set")
            else:
                result.actions.append("dry_run_would_set_plan_prepared_by")
        else:
            result.actions.append("plan_prepared_by_ok")

    result.success = not result.errors

    if config.apply:
        await db.commit()

    return result


def smoke_commands_text() -> str:
    return (
        "$env:WORKOS_DEV_AUTH_USER_ID='dev-sandu-employee-001'\n"
        "Invoke-RestMethod http://127.0.0.1:8000/api/v1/auth/me\n"
        "Invoke-RestMethod http://127.0.0.1:8000/api/v1/employee-mobile/tasks"
    )
