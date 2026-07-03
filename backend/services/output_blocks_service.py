"""BUILD 27.06 — OutputBlock entity/API contract service.

Responsibilities:
- validate enum contracts
- validate source mapping allowlist
- validate variable contract
- validate condition contract
- create/list/read/update/approve OutputBlock definitions

This service does not render template text and does not mutate quote/order flows.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional, Union

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.output_blocks import OutputBlock


ALLOWED_BLOCK_TYPES = frozenset(
    [
        "offer_short_description",
        "offer_technical_description",
        "contract_scope_included",
        "contract_scope_excluded",
        "technical_memo_description",
        "production_instruction",
        "qc_note",
        "exclusion_assumption",
    ]
)

ALLOWED_AUDIENCES = frozenset(
    ["client", "internal", "production", "technical", "legal_commercial"]
)

ALLOWED_DOCUMENT_TYPES = frozenset(
    ["offer", "contract_scope", "technical_memo", "production_sheet"]
)

ALLOWED_APPROVAL_STATUSES = frozenset(
    ["draft", "needs_review", "approved", "deprecated", "blocked"]
)

ALLOWED_CONDITION_OPERATORS = frozenset(
    ["equals", "not_equals", "in", "exists", "not_exists"]
)

ALLOWED_VARIABLE_FORMATS = frozenset(
    [
        "plain_text",
        "number",
        "dimension",
        "quantity",
        "boolean_label",
        "enum_label",
        "list_joined",
        "money_summary_public_only",
    ]
)

ALLOWED_MISSING_BEHAVIORS = frozenset(
    [
        "block_rendering",
        "render_with_warning",
        "use_approved_fallback",
        "hide_block",
        "require_manual_review",
    ]
)

ALLOWED_SOURCE_PREFIXES = (
    "identity.",
    "product_family.",
    "quote.",
    "order.",
    "materials.",
    "components.",
    "operations.",
    "finishes.",
    "options.",
    "qc_checkpoints.",
    "risks.",
    "cost_snapshot.",
)

FORBIDDEN_SOURCE_PREFIXES = (
    "frontend.",
    "ui.",
    "ai.",
    "visual_simulation.",
    "execution_reality.",
    "operator_notes.",
    "free_text.",
    "external.",
)

FORBIDDEN_SOURCE_FIELDS = {"inventory.stock_current", "inventory.live_stock"}
FORBIDDEN_CONDITION_KEYS = {"regex", "pattern", "expression", "script", "code", "js", "python", "eval"}


class OutputBlockValidationError(Exception):
    def __init__(self, violations: List[Dict[str, str]]):
        super().__init__("output_block_validation_error")
        self.violations = violations


class OutputBlockPolicyError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class OutputBlocksService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_blocks(
        self,
        *,
        block_type: Optional[str] = None,
        audience: Optional[str] = None,
        document_type: Optional[str] = None,
        approval_status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        query = select(OutputBlock)
        count_query = select(func.count(OutputBlock.id))

        if block_type:
            query = query.where(OutputBlock.block_type == block_type)
            count_query = count_query.where(OutputBlock.block_type == block_type)
        if audience:
            query = query.where(OutputBlock.audience == audience)
            count_query = count_query.where(OutputBlock.audience == audience)
        if document_type:
            query = query.where(OutputBlock.document_type == document_type)
            count_query = count_query.where(OutputBlock.document_type == document_type)
        if approval_status:
            query = query.where(OutputBlock.approval_status == approval_status)
            count_query = count_query.where(OutputBlock.approval_status == approval_status)

        query = query.order_by(OutputBlock.updated_at.desc())

        total = (await self.db.execute(count_query)).scalar() or 0
        rows = (await self.db.execute(query.offset(skip).limit(limit))).scalars().all()
        return {
            "items": [self._serialize(row) for row in rows],
            "total": int(total),
            "skip": skip,
            "limit": limit,
        }

    async def get_block(self, block_id: str) -> Optional[Dict[str, Any]]:
        row = await self._get_row_by_block_id(block_id)
        if not row:
            return None
        return self._serialize(row)

    async def create_block(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._validate_and_normalize(payload)

        exists = await self._get_row_by_block_id(normalized["block_id"])
        if exists:
            raise OutputBlockPolicyError(
                code="block_id_already_exists",
                message=f"OutputBlock with block_id '{normalized['block_id']}' already exists",
            )

        row = OutputBlock(**normalized)
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return self._serialize(row)

    async def update_block(self, block_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        row = await self._get_row_by_block_id(block_id)
        if not row:
            return None

        if row.approval_status in {"approved", "deprecated"}:
            raise OutputBlockPolicyError(
                code="unsafe_update_blocked",
                message=f"Cannot update block in status '{row.approval_status}'",
            )

        current = self._serialize(row)
        merged = {**current, **payload}
        normalized = self._validate_and_normalize(merged, for_update=True)

        # block_id remains immutable via path.
        normalized["block_id"] = block_id

        for key, value in normalized.items():
            setattr(row, key, value)

        await self.db.commit()
        await self.db.refresh(row)
        return self._serialize(row)

    async def approve_block(self, block_id: str, reviewer_role: Optional[str] = None) -> Optional[Dict[str, Any]]:
        row = await self._get_row_by_block_id(block_id)
        if not row:
            return None

        if row.approval_status == "deprecated":
            raise OutputBlockPolicyError(
                code="deprecated_block_cannot_be_approved",
                message="Deprecated blocks cannot be approved directly",
            )

        if row.approval_status not in {"draft", "needs_review"}:
            raise OutputBlockPolicyError(
                code="invalid_approval_transition",
                message=f"Cannot approve block in status '{row.approval_status}'",
            )

        row.approval_status = "approved"
        if reviewer_role:
            row.reviewer_role = reviewer_role

        await self.db.commit()
        await self.db.refresh(row)
        return self._serialize(row)

    async def _get_row_by_block_id(self, block_id: str) -> Optional[OutputBlock]:
        result = await self.db.execute(select(OutputBlock).where(OutputBlock.block_id == block_id))
        return result.scalar_one_or_none()

    def _validate_and_normalize(self, payload: Dict[str, Any], for_update: bool = False) -> Dict[str, Any]:
        violations: List[Dict[str, str]] = []

        block_id = str(payload.get("block_id", "")).strip()
        block_type = str(payload.get("block_type", "")).strip()
        title = str(payload.get("title", "")).strip()
        purpose = payload.get("purpose")
        audience = str(payload.get("audience", "")).strip()
        document_type = str(payload.get("document_type", "")).strip()
        source_fields = payload.get("source_fields")
        variables = payload.get("variables")
        template_text = str(payload.get("template_text", "")).strip()
        conditions = payload.get("conditions", {})
        approval_status = str(payload.get("approval_status", "draft")).strip() or "draft"
        version = str(payload.get("version", "v1")).strip() or "v1"
        owner_role = payload.get("owner_role")
        reviewer_role = payload.get("reviewer_role")
        snapshot_policy = payload.get("snapshot_policy", {})

        if not block_id:
            violations.append({"field": "block_id", "error": "required"})
        if not block_type:
            violations.append({"field": "block_type", "error": "required"})
        elif block_type not in ALLOWED_BLOCK_TYPES:
            violations.append({"field": "block_type", "error": f"invalid:{block_type}"})

        if not title:
            violations.append({"field": "title", "error": "required"})

        if not audience:
            violations.append({"field": "audience", "error": "required"})
        elif audience not in ALLOWED_AUDIENCES:
            violations.append({"field": "audience", "error": f"invalid:{audience}"})

        if not document_type:
            violations.append({"field": "document_type", "error": "required"})
        elif document_type not in ALLOWED_DOCUMENT_TYPES:
            violations.append({"field": "document_type", "error": f"invalid:{document_type}"})

        if approval_status not in ALLOWED_APPROVAL_STATUSES:
            violations.append({"field": "approval_status", "error": f"invalid:{approval_status}"})

        if not template_text:
            violations.append({"field": "template_text", "error": "required"})

        self._validate_source_fields(source_fields, violations)
        self._validate_variables(variables, audience, violations)
        self._validate_conditions(conditions, violations)

        if snapshot_policy is not None and not isinstance(snapshot_policy, dict):
            violations.append({"field": "snapshot_policy", "error": "must_be_object"})

        if violations:
            raise OutputBlockValidationError(violations)

        return {
            "block_id": block_id,
            "block_type": block_type,
            "title": title,
            "purpose": purpose,
            "audience": audience,
            "document_type": document_type,
            "source_fields": json.dumps(source_fields),
            "variables": json.dumps(variables),
            "template_text": template_text,
            "conditions": json.dumps(conditions),
            "approval_status": approval_status,
            "version": version,
            "owner_role": owner_role,
            "reviewer_role": reviewer_role,
            "snapshot_policy": json.dumps(snapshot_policy),
        }

    def _validate_source_fields(self, source_fields: Any, violations: List[Dict[str, str]]) -> None:
        if not isinstance(source_fields, list) or not source_fields:
            violations.append({"field": "source_fields", "error": "must_be_non_empty_array"})
            return

        for idx, source_field in enumerate(source_fields):
            self._validate_source_field(source_field, f"source_fields[{idx}]", violations)

    def _validate_variables(self, variables: Any, audience: str, violations: List[Dict[str, str]]) -> None:
        if not isinstance(variables, list):
            violations.append({"field": "variables", "error": "must_be_array"})
            return

        seen_keys = set()
        for idx, var in enumerate(variables):
            path = f"variables[{idx}]"
            if not isinstance(var, dict):
                violations.append({"field": path, "error": "must_be_object"})
                continue

            key = str(var.get("key", "")).strip()
            source_field = var.get("source_field")
            required = bool(var.get("required", False))
            var_format = str(var.get("format", "")).strip()
            missing_behavior = str(var.get("missing_behavior", "")).strip()

            if not key:
                violations.append({"field": f"{path}.key", "error": "required"})
            elif key in seen_keys:
                violations.append({"field": f"{path}.key", "error": f"duplicate:{key}"})
            else:
                seen_keys.add(key)

            if not source_field:
                violations.append({"field": f"{path}.source_field", "error": "required"})
            else:
                self._validate_source_field(source_field, f"{path}.source_field", violations)

            if not var_format:
                violations.append({"field": f"{path}.format", "error": "required"})
            elif var_format not in ALLOWED_VARIABLE_FORMATS:
                violations.append({"field": f"{path}.format", "error": f"invalid:{var_format}"})

            if not missing_behavior:
                violations.append({"field": f"{path}.missing_behavior", "error": "required"})
            elif missing_behavior not in ALLOWED_MISSING_BEHAVIORS:
                violations.append(
                    {"field": f"{path}.missing_behavior", "error": f"invalid:{missing_behavior}"}
                )

            if audience == "client" and required and missing_behavior and missing_behavior != "block_rendering":
                violations.append(
                    {
                        "field": f"{path}.missing_behavior",
                        "error": "client_required_variables_must_use_block_rendering",
                    }
                )

    def _validate_conditions(self, conditions: Any, violations: List[Dict[str, str]]) -> None:
        if conditions is None:
            return
        if not isinstance(conditions, (dict, list)):
            violations.append({"field": "conditions", "error": "must_be_object_or_array"})
            return
        self._validate_condition_node(conditions, "conditions", violations)

    def _validate_condition_node(self, node: Any, path: str, violations: List[Dict[str, str]]) -> None:
        if isinstance(node, list):
            for idx, item in enumerate(node):
                self._validate_condition_node(item, f"{path}[{idx}]", violations)
            return

        if isinstance(node, dict):
            for key, value in node.items():
                if key in FORBIDDEN_CONDITION_KEYS:
                    violations.append({"field": f"{path}.{key}", "error": "forbidden_condition_feature"})

                if key == "operator":
                    if not isinstance(value, str):
                        violations.append({"field": f"{path}.operator", "error": "must_be_string"})
                    elif value not in ALLOWED_CONDITION_OPERATORS:
                        violations.append({"field": f"{path}.operator", "error": f"invalid:{value}"})

                if key == "field":
                    self._validate_source_field(value, f"{path}.field", violations)

                self._validate_condition_node(value, f"{path}.{key}", violations)

    def _validate_source_field(self, source_field: Any, path: str, violations: List[Dict[str, str]]) -> None:
        if not isinstance(source_field, str) or not source_field.strip():
            violations.append({"field": path, "error": "must_be_non_empty_string"})
            return

        field = source_field.strip()

        if field in FORBIDDEN_SOURCE_FIELDS:
            violations.append({"field": path, "error": f"forbidden_source:{field}"})
            return

        for forbidden_prefix in FORBIDDEN_SOURCE_PREFIXES:
            if field.startswith(forbidden_prefix):
                violations.append({"field": path, "error": f"forbidden_source:{field}"})
                return

        if field.startswith("inventory."):
            violations.append({"field": path, "error": f"forbidden_source:{field}"})
            return

        if not any(field.startswith(prefix) for prefix in ALLOWED_SOURCE_PREFIXES):
            violations.append({"field": path, "error": f"source_prefix_not_allowed:{field}"})

    def _parse_json_field(self, value: Optional[str], fallback: Union[Dict[str, Any], List[Any]]) -> Any:
        if value is None:
            return fallback
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return fallback

    def _serialize(self, row: OutputBlock) -> Dict[str, Any]:
        return {
            "id": row.id,
            "block_id": row.block_id,
            "block_type": row.block_type,
            "title": row.title,
            "purpose": row.purpose,
            "audience": row.audience,
            "document_type": row.document_type,
            "source_fields": self._parse_json_field(row.source_fields, []),
            "variables": self._parse_json_field(row.variables, []),
            "template_text": row.template_text,
            "conditions": self._parse_json_field(row.conditions, {}),
            "approval_status": row.approval_status,
            "version": row.version,
            "owner_role": row.owner_role,
            "reviewer_role": row.reviewer_role,
            "snapshot_policy": self._parse_json_field(row.snapshot_policy, {}),
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }