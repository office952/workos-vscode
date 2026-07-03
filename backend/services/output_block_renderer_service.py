"""BUILD 27.07 - OutputBlock renderer for quote preview contract.

Preview-only renderer for OutputBlock entity records from `output_blocks`.
This service is backend-only, read-only, and does not persist or mutate
quotes/orders/inventory/execution.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.output_blocks import OutputBlock
from services.output_blocks_service import (
    FORBIDDEN_CONDITION_KEYS,
    FORBIDDEN_SOURCE_FIELDS,
    FORBIDDEN_SOURCE_PREFIXES,
)


_PLACEHOLDER_RE = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
_SUPPORTED_CONTEXTS = frozenset({"quote_preview"})
_SUPPORTED_CONDITION_OPERATORS = frozenset({"equals"})


class OutputBlockPreviewValidationError(Exception):
    def __init__(self, violations: List[Dict[str, str]]):
        super().__init__("output_block_preview_validation_error")
        self.violations = violations


class OutputBlockRendererService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def render_output_blocks_preview(
        self,
        *,
        block_ids: Optional[List[str]],
        block_types: Optional[List[str]],
        context: str,
        source_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        violations: List[Dict[str, str]] = []
        normalized_block_ids = [str(item).strip() for item in (block_ids or []) if str(item).strip()]
        normalized_block_types = [str(item).strip() for item in (block_types or []) if str(item).strip()]

        if context not in _SUPPORTED_CONTEXTS:
            violations.append({"field": "context", "error": f"invalid:{context}"})
        if not normalized_block_ids and not normalized_block_types:
            violations.append(
                {
                    "field": "block_ids|block_types",
                    "error": "at_least_one_selector_required",
                }
            )
        if not isinstance(source_payload, dict):
            violations.append({"field": "source_payload", "error": "must_be_object"})

        if violations:
            raise OutputBlockPreviewValidationError(violations)

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

        rendered_blocks: List[Dict[str, Any]] = []
        top_level_warnings: List[Dict[str, Any]] = []

        for row in rows:
            block_payload = self._serialize_row(row)
            rendered = self._render_single_block(block_payload=block_payload, source_payload=source_payload)
            rendered_blocks.append(rendered)
            top_level_warnings.extend(rendered["warnings"])
            top_level_blockers.extend(rendered["blockers"])

        return {
            "preview_only": True,
            "context": context,
            "rendered_blocks": rendered_blocks,
            "warnings": top_level_warnings,
            "blockers": top_level_blockers,
        }

    def _serialize_row(self, row: OutputBlock) -> Dict[str, Any]:
        return {
            "block_id": row.block_id,
            "block_type": row.block_type,
            "title": row.title,
            "approval_status": row.approval_status,
            "template_text": row.template_text or "",
            "variables": self._parse_json(row.variables, []),
            "conditions": self._parse_json(row.conditions, {}),
        }

    def _render_single_block(self, *, block_payload: Dict[str, Any], source_payload: Dict[str, Any]) -> Dict[str, Any]:
        block_id = block_payload.get("block_id", "")
        block_type = block_payload.get("block_type", "")
        title = block_payload.get("title")
        approval_status = str(block_payload.get("approval_status", "")).strip()
        template_text = str(block_payload.get("template_text", ""))
        variables_raw = block_payload.get("variables", [])
        conditions_raw = block_payload.get("conditions", {})

        block_warnings: List[Dict[str, Any]] = []
        block_blockers: List[Dict[str, Any]] = []

        result: Dict[str, Any] = {
            "block_id": block_id,
            "block_type": block_type,
            "title": title,
            "approval_status": approval_status,
            "rendered_text": None,
            "variables_used": {},
            "source_fields_used": [],
            "skipped": False,
            "skip_reason": None,
            "warnings": block_warnings,
            "blockers": block_blockers,
        }

        approval_decision = self._apply_preview_approval_policy(approval_status)
        block_warnings.extend(approval_decision["warnings"])
        block_blockers.extend(approval_decision["blockers"])
        if approval_decision["skipped"]:
            result["skipped"] = True
            result["skip_reason"] = approval_decision["skip_reason"]
            return result

        conditions_eval = self._evaluate_conditions(conditions_raw, source_payload)
        block_warnings.extend(conditions_eval["warnings"])
        block_blockers.extend(conditions_eval["blockers"])
        result["source_fields_used"].extend(conditions_eval["source_fields_used"])
        if conditions_eval["skip"]:
            result["skipped"] = True
            result["skip_reason"] = conditions_eval["skip_reason"]
            return result

        variables = self._normalize_variables(variables_raw)
        placeholder_keys = self._extract_placeholders(template_text)
        known_variable_keys = {item["key"] for item in variables}

        unknown_placeholders = sorted(key for key in placeholder_keys if key not in known_variable_keys)
        if unknown_placeholders:
            for key in unknown_placeholders:
                block_blockers.append(
                    {
                        "code": "unknown_placeholder",
                        "placeholder": key,
                        "message": "Placeholder not declared in variables",
                    }
                )
            return result

        variables_by_key = {item["key"]: item for item in variables}
        resolved_values: Dict[str, Any] = {}

        for key in placeholder_keys:
            definition = variables_by_key.get(key)
            if not definition:
                continue

            source_field = definition["source_field"]
            if self._is_forbidden_source_path(source_field):
                block_blockers.append(
                    {
                        "code": "forbidden_source_path",
                        "variable": key,
                        "source_field": source_field,
                        "message": "Source path forbidden by renderer fail-safe policy",
                    }
                )
                continue

            result["source_fields_used"].append(source_field)
            value, exists = self._get_dot_path(source_payload, source_field)

            if exists and not self._is_missing_value(value):
                resolved_values[key] = value
                result["variables_used"][key] = value
                continue

            required = bool(definition.get("required", False))
            missing_behavior = str(definition.get("missing_behavior", "")).strip()

            if required:
                block_blockers.append(
                    {
                        "code": "required_variable_missing",
                        "variable": key,
                        "source_field": source_field,
                        "message": "Required variable missing for preview render",
                    }
                )
                continue

            if missing_behavior == "hide_block":
                result["skipped"] = True
                result["skip_reason"] = "optional_variable_missing_hide_block"
                return result

            if missing_behavior == "render_with_warning":
                block_warnings.append(
                    {
                        "code": "optional_variable_missing_render_with_warning",
                        "variable": key,
                        "source_field": source_field,
                        "message": "Optional variable missing; rendered with blank fallback",
                    }
                )
                resolved_values[key] = ""
                result["variables_used"][key] = ""
                continue

            if missing_behavior == "use_approved_fallback":
                block_warnings.append(
                    {
                        "code": "optional_variable_missing_use_approved_fallback",
                        "variable": key,
                        "source_field": source_field,
                        "message": "No approved fallback available; rendered with blank fallback",
                    }
                )
                resolved_values[key] = ""
                result["variables_used"][key] = ""
                continue

            if missing_behavior in {"block_rendering", "require_manual_review"}:
                block_blockers.append(
                    {
                        "code": "optional_variable_missing_blocked",
                        "variable": key,
                        "source_field": source_field,
                        "message": "Missing variable behavior blocks rendering",
                    }
                )
                continue

            block_blockers.append(
                {
                    "code": "unknown_missing_behavior",
                    "variable": key,
                    "source_field": source_field,
                    "missing_behavior": missing_behavior,
                }
            )

        if block_blockers or result["skipped"]:
            return result

        result["rendered_text"] = self._render_template(template_text, resolved_values)
        result["source_fields_used"] = sorted(set(result["source_fields_used"]))
        return result

    def _apply_preview_approval_policy(self, approval_status: str) -> Dict[str, Any]:
        warnings: List[Dict[str, Any]] = []
        blockers: List[Dict[str, Any]] = []

        if approval_status == "approved":
            return {"warnings": warnings, "blockers": blockers, "skipped": False, "skip_reason": None}

        if approval_status == "draft":
            warnings.append(
                {
                    "code": "non_canonical_preview_draft_block",
                    "message": "Draft block rendered in preview-only mode",
                }
            )
            return {"warnings": warnings, "blockers": blockers, "skipped": False, "skip_reason": None}

        if approval_status == "needs_review":
            warnings.append(
                {
                    "code": "non_canonical_preview_needs_review_block",
                    "message": "Needs-review block rendered in preview-only mode",
                }
            )
            return {"warnings": warnings, "blockers": blockers, "skipped": False, "skip_reason": None}

        if approval_status in {"deprecated", "blocked", "rejected", "archived"}:
            blockers.append(
                {
                    "code": "approval_status_blocked_for_preview",
                    "approval_status": approval_status,
                    "message": "Block status is not eligible for quote_preview rendering",
                }
            )
            return {
                "warnings": warnings,
                "blockers": blockers,
                "skipped": True,
                "skip_reason": f"approval_status_{approval_status}",
            }

        blockers.append(
            {
                "code": "unknown_approval_status",
                "approval_status": approval_status,
                "message": "Unknown approval status is blocked by default",
            }
        )
        return {
            "warnings": warnings,
            "blockers": blockers,
            "skipped": True,
            "skip_reason": "unknown_approval_status",
        }

    def _evaluate_conditions(self, conditions: Any, source_payload: Dict[str, Any]) -> Dict[str, Any]:
        warnings: List[Dict[str, Any]] = []
        blockers: List[Dict[str, Any]] = []
        source_fields_used: List[str] = []

        if conditions in (None, {}, []):
            return {
                "warnings": warnings,
                "blockers": blockers,
                "source_fields_used": source_fields_used,
                "skip": False,
                "skip_reason": None,
            }

        if self._contains_forbidden_condition_feature(conditions):
            blockers.append(
                {
                    "code": "forbidden_condition_feature",
                    "message": "Condition contains forbidden regex/script/expression feature",
                }
            )
            return {
                "warnings": warnings,
                "blockers": blockers,
                "source_fields_used": source_fields_used,
                "skip": True,
                "skip_reason": "forbidden_condition_feature",
            }

        condition_nodes: List[Dict[str, Any]] = []
        self._collect_condition_nodes(conditions, condition_nodes)
        if not condition_nodes:
            return {
                "warnings": warnings,
                "blockers": blockers,
                "source_fields_used": source_fields_used,
                "skip": False,
                "skip_reason": None,
            }

        for node in condition_nodes:
            field = str(node.get("field", "")).strip()
            operator = str(node.get("operator", "")).strip()
            expected = node.get("value")

            if not field:
                blockers.append({"code": "condition_field_missing", "message": "Condition field is required"})
                continue

            if self._is_forbidden_source_path(field):
                blockers.append(
                    {
                        "code": "condition_forbidden_source_path",
                        "field": field,
                        "message": "Condition field is forbidden",
                    }
                )
                continue

            source_fields_used.append(field)

            if operator not in _SUPPORTED_CONDITION_OPERATORS:
                blockers.append(
                    {
                        "code": "unsupported_condition_operator",
                        "operator": operator,
                        "message": "Condition operator is not supported for preview",
                    }
                )
                continue

            actual_value, exists = self._get_dot_path(source_payload, field)
            if not self._evaluate_condition_operator(operator, actual_value, exists, expected):
                return {
                    "warnings": warnings,
                    "blockers": blockers,
                    "source_fields_used": source_fields_used,
                    "skip": True,
                    "skip_reason": "conditions_not_matched",
                }

        if blockers:
            return {
                "warnings": warnings,
                "blockers": blockers,
                "source_fields_used": source_fields_used,
                "skip": True,
                "skip_reason": "condition_blocked",
            }

        return {
            "warnings": warnings,
            "blockers": blockers,
            "source_fields_used": source_fields_used,
            "skip": False,
            "skip_reason": None,
        }

    def _collect_condition_nodes(self, node: Any, collector: List[Dict[str, Any]]) -> None:
        if isinstance(node, list):
            for item in node:
                self._collect_condition_nodes(item, collector)
            return

        if isinstance(node, dict):
            if "field" in node and "operator" in node:
                collector.append(node)
            for value in node.values():
                self._collect_condition_nodes(value, collector)

    def _contains_forbidden_condition_feature(self, node: Any) -> bool:
        if isinstance(node, list):
            return any(self._contains_forbidden_condition_feature(item) for item in node)
        if isinstance(node, dict):
            for key, value in node.items():
                if str(key).strip().lower() in FORBIDDEN_CONDITION_KEYS:
                    return True
                if self._contains_forbidden_condition_feature(value):
                    return True
        return False

    def _evaluate_condition_operator(self, operator: str, actual: Any, exists: bool, expected: Any) -> bool:
        if operator == "equals":
            return actual == expected
        if operator == "not_equals":
            return actual != expected
        if operator == "in":
            if isinstance(expected, list):
                return actual in expected
            return actual == expected
        if operator == "exists":
            return exists and not self._is_missing_value(actual)
        if operator == "not_exists":
            return (not exists) or self._is_missing_value(actual)
        return False

    def _normalize_variables(self, raw_variables: Any) -> List[Dict[str, Any]]:
        if not isinstance(raw_variables, list):
            return []

        normalized: List[Dict[str, Any]] = []
        for item in raw_variables:
            if not isinstance(item, dict):
                continue

            key = str(item.get("key", "")).strip() or str(item.get("name", "")).strip()
            source_field = str(item.get("source_field", "")).strip()
            if not key or not source_field:
                continue

            normalized.append(
                {
                    "key": key,
                    "source_field": source_field,
                    "required": bool(item.get("required", False)),
                    "missing_behavior": str(item.get("missing_behavior", "")).strip(),
                }
            )
        return normalized

    def _extract_placeholders(self, template_text: str) -> List[str]:
        seen = []
        for match in _PLACEHOLDER_RE.findall(template_text or ""):
            key = str(match).strip()
            if key and key not in seen:
                seen.append(key)
        return seen

    def _render_template(self, template_text: str, values: Dict[str, Any]) -> str:
        def _replacement(match: re.Match[str]) -> str:
            key = match.group(1).strip()
            value = values.get(key, "")
            if value is None:
                return ""
            if isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=True, sort_keys=True)
            return str(value)

        return _PLACEHOLDER_RE.sub(_replacement, template_text or "")

    def _get_dot_path(self, payload: Dict[str, Any], path: str) -> Tuple[Any, bool]:
        current: Any = payload
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return None, False
            current = current[part]
        return current, True

    def _is_forbidden_source_path(self, path: str) -> bool:
        normalized = str(path).strip()
        if not normalized:
            return True
        if normalized in FORBIDDEN_SOURCE_FIELDS:
            return True
        if normalized.startswith("inventory."):
            return True
        for prefix in FORBIDDEN_SOURCE_PREFIXES:
            if normalized.startswith(prefix):
                return True
        return False

    def _is_missing_value(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        return False

    def _parse_json(self, raw: Optional[str], fallback: Any) -> Any:
        if raw is None:
            return fallback
        try:
            return json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return fallback
