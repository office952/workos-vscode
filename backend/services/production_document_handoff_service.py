"""Production document handoff — eligible intake work-files for execution plan tasks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.intake_requests import Intake_requestsService

BLOCKED_DOCUMENT_SOURCES = frozenset({
    "quote_pdf",
    "quote_documents_archive",
    "commercial_offer",
    "commercial_quote",
    "quote_document",
    "order_snapshot",
    "commercial",
})

BLOCKED_DOCUMENT_TYPES = frozenset({
    "quote_pdf",
    "commercial_pdf",
    "offer_pdf",
    "order_snapshot",
})

BLOCKED_URL_FRAGMENTS = (
    "/pdf/",
    "quote_documents",
    "generated_documents/quotes",
    "quote.export",
    "snapshot",
)


def employee_mobile_work_file_download_path(order_id: int, file_id: str) -> str:
    return f"/api/v1/employee-mobile/orders/{order_id}/work-files/{file_id}/download"


def _extension_to_doc_type(extension: str, mime_type: str = "") -> str:
    ext = (extension or "").strip().lower().lstrip(".")
    if ext:
        return ext
    mime = (mime_type or "").strip().lower()
    if "svg" in mime:
        return "svg"
    if "pdf" in mime:
        return "pdf"
    if "png" in mime:
        return "png"
    return "file"


def _is_blocked_production_document(doc: dict) -> bool:
    source = str(doc.get("source") or "").strip().lower()
    doc_type = str(doc.get("type") or "").strip().lower()
    url = str(doc.get("url") or "").strip().lower()
    name = str(doc.get("name") or "").strip().lower()
    if source in BLOCKED_DOCUMENT_SOURCES:
        return True
    if doc_type in BLOCKED_DOCUMENT_TYPES:
        return True
    if any(fragment in url for fragment in BLOCKED_URL_FRAGMENTS):
        return True
    if "quote" in name and "pdf" in name:
        return True
    if "oferta" in name and doc_type == "pdf":
        return True
    return False


def _document_dedupe_key(doc: dict) -> str:
    doc_id = str(doc.get("id") or "").strip()
    source = str(doc.get("source") or "task").strip().lower()
    if not doc_id:
        return ""
    return f"{source}:{doc_id}"


def _prefer_richer_document(existing: dict, candidate: dict) -> dict:
    if candidate.get("url") and not existing.get("url"):
        return candidate
    if candidate.get("downloadable") and not existing.get("downloadable"):
        return candidate
    return existing


def normalize_intake_work_file_for_plan(row: dict) -> Optional[dict]:
    """Plan storage metadata — no employee-scoped download URL."""
    file_id = str(row.get("id") or "").strip()
    if not file_id:
        return None

    file_name = str(row.get("fileName") or row.get("storedFileName") or "Fișier producție").strip()
    extension = str(row.get("extension") or Path(file_name).suffix or "")
    mime_type = str(row.get("mimeType") or "")

    doc = {
        "id": file_id,
        "name": file_name,
        "type": _extension_to_doc_type(extension, mime_type),
        "mime_type": mime_type or None,
        "source": "intake_work_file",
        "downloadable": True,
    }
    if _is_blocked_production_document(doc):
        return None
    return doc


def normalize_intake_work_file_for_mobile(row: dict, *, order_id: int) -> Optional[dict]:
    doc = normalize_intake_work_file_for_plan(row)
    if doc is None:
        return None
    doc = dict(doc)
    doc["url"] = employee_mobile_work_file_download_path(order_id, str(doc["id"]))
    return doc


def merge_production_documents(
    task_documents: List[dict],
    order_documents: List[dict],
) -> List[dict]:
    merged: List[dict] = []
    index_by_key: Dict[str, int] = {}

    for doc in task_documents + order_documents:
        if not isinstance(doc, dict):
            continue
        if _is_blocked_production_document(doc):
            continue
        key = _document_dedupe_key(doc)
        if not key:
            merged.append(dict(doc))
            continue
        if key in index_by_key:
            idx = index_by_key[key]
            merged[idx] = _prefer_richer_document(merged[idx], doc)
        else:
            index_by_key[key] = len(merged)
            merged.append(dict(doc))

    return merged


async def resolve_order_intake_code(db: AsyncSession, order_id: int) -> str:
    sql = text(
        "SELECT q.intake_code "
        "FROM orders o "
        "LEFT JOIN quotes q ON q.id = o.quote_id "
        "WHERE o.id = :oid LIMIT 1"
    )
    row = (await db.execute(sql, {"oid": order_id})).mappings().first()
    if not row:
        return ""
    return str(row.get("intake_code") or "").strip()


async def load_eligible_intake_documents_for_plan(
    db: AsyncSession,
    *,
    order_id: int,
    intake_code: str | None = None,
) -> List[dict]:
    code = (intake_code or "").strip()
    if not code:
        code = await resolve_order_intake_code(db, order_id)
    if not code:
        return []

    intake_service = Intake_requestsService(db)
    intake = await intake_service.get_by_field("code", code)
    if not intake or not intake.product_spec_json:
        return []

    try:
        spec = json.loads(intake.product_spec_json)
    except json.JSONDecodeError:
        return []

    if not isinstance(spec, dict):
        return []

    rows = spec.get("workFileAttachments")
    if not isinstance(rows, list):
        return []

    documents: List[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        doc = normalize_intake_work_file_for_plan(row)
        if doc:
            documents.append(doc)
    return documents


async def load_intake_work_files_for_order(
    db: AsyncSession,
    *,
    order_id: int,
    intake_code: str,
) -> List[dict]:
    plan_docs = await load_eligible_intake_documents_for_plan(
        db,
        order_id=order_id,
        intake_code=intake_code,
    )
    mobile_docs: List[dict] = []
    for doc in plan_docs:
        file_id = str(doc.get("id") or "").strip()
        if not file_id:
            continue
        enriched = dict(doc)
        enriched["url"] = employee_mobile_work_file_download_path(order_id, file_id)
        mobile_docs.append(enriched)
    return mobile_docs


def attach_documents_to_planned_tasks(
    task_dicts: List[dict],
    documents: List[dict],
) -> List[dict]:
    if not documents:
        return task_dicts

    result: List[dict] = []
    for task in task_dicts:
        if not isinstance(task, dict):
            result.append(task)
            continue
        updated = dict(task)
        existing = updated.get("documents") if isinstance(updated.get("documents"), list) else []
        updated["documents"] = merge_production_documents(existing, documents)
        result.append(updated)
    return result
