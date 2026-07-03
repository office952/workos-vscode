"""BUILD 27.08 — Rendered OutputBlock snapshot persistence service.

Creates immutable, backend-owned rendered OutputBlock snapshots from approved
OutputBlock definitions and explicit source payload.

Rules:
  - Preview route remains non-persistent.
  - Final snapshot rejects draft/needs_review/deprecated/blocked blocks.
  - Final snapshot rejects blockers and persists nothing on failure.
  - No Quote/Order/Inventory/Execution/ExecutionReality mutation.
  - No HTTP self-calls; renderer/service logic is called directly.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.orders import Orders
from models.output_blocks import OutputBlock
from models.quotes import Quotes
from models.rendered_output_snapshots import RenderedOutputSnapshot
from services.output_block_renderer_service import OutputBlockRendererService
from services.output_blocks_service import ALLOWED_AUDIENCES, ALLOWED_DOCUMENT_TYPES


SUPPORTED_SNAPSHOT_CONTEXTS = frozenset({"quote_snapshot", "order_snapshot"})
SUPPORTED_TARGET_TYPES = frozenset({"quote", "order"})


class RenderedOutputSnapshotValidationError(Exception):
    def __init__(self, violations: List[Dict[str, str]]):
        super().__init__("rendered_output_snapshot_validation_error")
        self.violations = violations


class RenderedOutputSnapshotBlockedError(Exception):
    def __init__(self, payload: Dict[str, Any]):
        super().__init__("rendered_output_snapshot_blocked")
        self.payload = payload


class RenderedOutputSnapshotDTO:
    def __init__(self, snapshot: RenderedOutputSnapshot):
        self.snapshot = snapshot

    def to_dict(self) -> Dict[str, Any]:
        row = self.snapshot
        return {
            "snapshot_id": row.id,
            "snapshot_uid": row.snapshot_uid,
            "preview_only": False,
            "snapshot_status": row.status,
            "context": row.context,
            "document_type": row.document_type,
            "audience": row.audience,
            "snapshot_purpose": row.snapshot_purpose,
            "target_type": row.target_type,
            "target_id": _deserialize_target_id(row.target_id),
            "rendered_blocks": _safe_json_load(row.rendered_blocks_json, []),
            "warnings": _safe_json_load(row.warnings_json, []),
            "blockers": _safe_json_load(row.blockers_json, []),
            "source_payload_hash": row.source_payload_hash,
            "created_by": row.created_by,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }


class OutputBlockSnapshotService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.renderer = OutputBlockRendererService(db)

    async def create_rendered_output_snapshot(
        self,
        *,
        context: str,
        block_ids: Optional[List[str]],
        block_types: Optional[List[str]],
        source_payload: Dict[str, Any],
        document_type: str,
        audience: str,
        snapshot_purpose: str,
        target_type: Optional[str] = None,
        target_id: Optional[int | str] = None,
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        normalized_block_ids = [str(item).strip() for item in (block_ids or []) if str(item).strip()]
        normalized_block_types = [str(item).strip() for item in (block_types or []) if str(item).strip()]
        normalized_target_type = str(target_type).strip() if target_type is not None else None
        normalized_target_id = str(target_id).strip() if target_id is not None else None
        normalized_snapshot_purpose = str(snapshot_purpose).strip()

        violations: List[Dict[str, str]] = []
        if context not in SUPPORTED_SNAPSHOT_CONTEXTS:
            violations.append({"field": "context", "error": f"invalid:{context}"})
        if not normalized_block_ids and not normalized_block_types:
            violations.append({"field": "block_ids|block_types", "error": "at_least_one_selector_required"})
        if not isinstance(source_payload, dict):
            violations.append({"field": "source_payload", "error": "must_be_object"})
        if document_type not in ALLOWED_DOCUMENT_TYPES:
            violations.append({"field": "document_type", "error": f"invalid:{document_type}"})
        if audience not in ALLOWED_AUDIENCES:
            violations.append({"field": "audience", "error": f"invalid:{audience}"})
        if not normalized_snapshot_purpose:
            violations.append({"field": "snapshot_purpose", "error": "required"})
        if normalized_target_type and normalized_target_type not in SUPPORTED_TARGET_TYPES:
            violations.append({"field": "target_type", "error": f"invalid:{normalized_target_type}"})
        if normalized_target_type and not normalized_target_id:
            violations.append({"field": "target_id", "error": "required_when_target_type_present"})
        if normalized_target_id and not normalized_target_type:
            violations.append({"field": "target_type", "error": "required_when_target_id_present"})
        if context == "quote_snapshot" and normalized_target_type == "order":
            violations.append({"field": "target_type", "error": "context_target_mismatch"})
        if context == "order_snapshot" and normalized_target_type == "quote":
            violations.append({"field": "target_type", "error": "context_target_mismatch"})

        if violations:
            raise RenderedOutputSnapshotValidationError(violations)

        if normalized_target_type and normalized_target_id:
            await self._assert_target_exists(normalized_target_type, normalized_target_id)

        query = select(OutputBlock)
        if normalized_block_ids:
            query = query.where(OutputBlock.block_id.in_(normalized_block_ids))
        if normalized_block_types:
            query = query.where(OutputBlock.block_type.in_(normalized_block_types))

        if normalized_block_ids:
            order_mapping = {block_id: index for index, block_id in enumerate(normalized_block_ids)}
            order_case = case(order_mapping, value=OutputBlock.block_id, else_=len(normalized_block_ids))
            query = query.order_by(order_case.asc(), OutputBlock.block_id.asc())
        else:
            query = query.order_by(OutputBlock.block_id.asc())

        rows = (await self.db.execute(query)).scalars().all()

        top_level_blockers: List[Dict[str, Any]] = []
        top_level_warnings: List[Dict[str, Any]] = []
        rendered_blocks: List[Dict[str, Any]] = []

        if normalized_block_ids:
            found = {row.block_id for row in rows}
            for block_id in normalized_block_ids:
                if block_id not in found:
                    top_level_blockers.append(
                        {
                            "code": "block_id_not_found",
                            "block_id": block_id,
                            "message": "Requested block_id was not found",
                        }
                    )

        for row in rows:
            rendered = self._render_snapshot_block(row=row, source_payload=source_payload)
            rendered_blocks.append(rendered)
            top_level_warnings.extend(rendered.get("warnings", []))
            top_level_blockers.extend(rendered.get("blockers", []))

        if top_level_blockers:
            raise RenderedOutputSnapshotBlockedError(
                {
                    "preview_only": False,
                    "snapshot_status": "blocked",
                    "context": context,
                    "document_type": document_type,
                    "audience": audience,
                    "snapshot_purpose": normalized_snapshot_purpose,
                    "target_type": normalized_target_type,
                    "target_id": _deserialize_target_id(normalized_target_id),
                    "rendered_blocks": rendered_blocks,
                    "warnings": top_level_warnings,
                    "blockers": top_level_blockers,
                }
            )

        source_payload_json = json.dumps(source_payload, ensure_ascii=True, sort_keys=True)
        source_payload_hash = hashlib.sha256(source_payload_json.encode("utf-8")).hexdigest()[:32]
        trace = {
            "snapshot_owner": "product_system",
            "preview_only": False,
            "quote_mutated": False,
            "order_mutated": False,
            "inventory_mutated": False,
            "execution_mutated": False,
            "execution_reality_mutated": False,
            "costengine_formula_changed": False,
            "pdf_generated": False,
            "ai_called": False,
            "target_type": normalized_target_type,
            "target_id": _deserialize_target_id(normalized_target_id),
        }

        snapshot = RenderedOutputSnapshot(
            snapshot_uid=str(uuid.uuid4()),
            context=context,
            document_type=document_type,
            audience=audience,
            snapshot_purpose=normalized_snapshot_purpose,
            target_type=normalized_target_type,
            target_id=normalized_target_id,
            source_payload_json=source_payload_json,
            source_payload_hash=source_payload_hash,
            rendered_blocks_json=json.dumps(rendered_blocks, ensure_ascii=True, sort_keys=True),
            warnings_json=json.dumps(top_level_warnings, ensure_ascii=True, sort_keys=True),
            blockers_json=json.dumps([], ensure_ascii=True),
            status="created",
            created_by=created_by,
            trace_json=json.dumps(trace, ensure_ascii=True, sort_keys=True),
        )
        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)
        return RenderedOutputSnapshotDTO(snapshot).to_dict()

    def _render_snapshot_block(self, *, row: OutputBlock, source_payload: Dict[str, Any]) -> Dict[str, Any]:
        block_payload = self.renderer._serialize_row(row)
        approval_status = str(block_payload.get("approval_status", "")).strip()

        result: Dict[str, Any] = {
            "block_id": row.block_id,
            "block_type": row.block_type,
            "title": row.title,
            "approval_status": approval_status,
            "block_version": row.version,
            "template_text_hash": hashlib.sha256((row.template_text or "").encode("utf-8")).hexdigest()[:32],
            "rendered_text": None,
            "variables_used": {},
            "source_fields_used": [],
            "skipped": False,
            "skip_reason": None,
            "warnings": [],
            "blockers": [],
        }

        if approval_status != "approved":
            result["skipped"] = True
            result["skip_reason"] = f"approval_status_{approval_status or 'unknown'}"
            result["blockers"].append(
                {
                    "code": "approval_status_not_allowed_for_snapshot",
                    "block_id": row.block_id,
                    "approval_status": approval_status,
                    "message": "Only approved blocks can be used in final rendered snapshots",
                }
            )
            return result

        rendered = self.renderer._render_single_block(block_payload=block_payload, source_payload=source_payload)
        result.update(
            {
                "rendered_text": rendered.get("rendered_text"),
                "variables_used": rendered.get("variables_used", {}),
                "source_fields_used": rendered.get("source_fields_used", []),
                "skipped": rendered.get("skipped", False),
                "skip_reason": rendered.get("skip_reason"),
                "warnings": rendered.get("warnings", []),
                "blockers": rendered.get("blockers", []),
            }
        )
        return result

    async def _assert_target_exists(self, target_type: str, target_id: str) -> None:
        if target_type == "quote":
            target_pk = _parse_numeric_target_id(target_type, target_id)
            query = select(Quotes.id).where(Quotes.id == target_pk)
        else:
            target_pk = _parse_numeric_target_id(target_type, target_id)
            query = select(Orders.id).where(Orders.id == target_pk)

        if (await self.db.execute(query)).scalar_one_or_none() is None:
            raise LookupError(f"{target_type}_not_found")


def _parse_numeric_target_id(target_type: str, target_id: str) -> int:
    try:
        return int(str(target_id).strip())
    except (TypeError, ValueError) as exc:
        raise RenderedOutputSnapshotValidationError(
            [{"field": "target_id", "error": f"must_be_integer_for_target_type:{target_type}"}]
        ) from exc


def _deserialize_target_id(value: Optional[str]) -> Optional[int | str]:
    if value is None:
        return None
    if str(value).isdigit():
        return int(str(value))
    return value


def _safe_json_load(raw: Optional[str], fallback: Any) -> Any:
    if raw is None:
        return fallback
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return fallback
