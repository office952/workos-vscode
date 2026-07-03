"""
BUILD 7 — Output Blocks Contract Validator.

Pure validation helper for output_blocks_json canonical schema.
NOT wired into existing CRUD — prepared validation only.

Rules:
  - Does not modify any entity.
  - Does not enforce on existing data unless explicitly called.
  - Does not break existing CRUD.
  - Validates structure against canonical schema.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Canonical allowed values
# ---------------------------------------------------------------------------

ALLOWED_BLOCK_TYPES = frozenset([
    "offer_short_description",
    "offer_technical_description",
    "contract_scope_included",
    "contract_scope_excluded",
    "technical_memo_description",
    "technical_memo_materials",
    "technical_memo_execution_method",
    "production_instruction",
    "installation_note",
    "warranty_note",
    "maintenance_note",
    "exclusion_assumption",
    "qc_note",
    "risk_note",
    "visual_prompt_block",
])

ALLOWED_AUDIENCES = frozenset([
    "client",
    "internal",
    "production",
    "technical",
    "legal_commercial",
    "installation",
    "sales",
    "estimator",
    "ai_visual_generation",
])

ALLOWED_DOCUMENT_TYPES = frozenset([
    "offer",
    "contract",
    "technical_memo",
    "production_sheet",
    "installation_sheet",
    "warranty_document",
    "maintenance_document",
    "internal_note",
    "visual_prompt",
])

ALLOWED_MISSING_BEHAVIORS = frozenset([
    "block_rendering",
    "render_with_warning",
    "use_approved_fallback",
    "hide_block",
    "require_manual_review",
])

ALLOWED_APPROVAL_STATUSES = frozenset([
    "draft",
    "needs_review",
    "approved",
    "approved_for_client",
    "deprecated",
    "blocked",
])

# Client-facing document types that require snapshot_policy
CLIENT_FACING_DOCUMENT_TYPES = frozenset([
    "offer",
    "contract",
])


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------

@dataclass
class BlockValidationError:
    block_index: int
    block_id: str
    field: str
    error: str
    severity: str = "error"  # "error" | "warning"


@dataclass
class OutputBlocksValidationResult:
    is_valid: bool = True
    errors: List[BlockValidationError] = field(default_factory=list)
    warnings: List[BlockValidationError] = field(default_factory=list)
    blocks_validated: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": [
                {
                    "block_index": e.block_index,
                    "block_id": e.block_id,
                    "field": e.field,
                    "error": e.error,
                    "severity": e.severity,
                }
                for e in self.errors
            ],
            "warnings": [
                {
                    "block_index": w.block_index,
                    "block_id": w.block_id,
                    "field": w.field,
                    "error": w.error,
                    "severity": w.severity,
                }
                for w in self.warnings
            ],
            "blocks_validated": self.blocks_validated,
        }


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

def validate_output_blocks(raw: Any) -> OutputBlocksValidationResult:
    """Validate output_blocks_json against canonical schema.

    Args:
        raw: Either a parsed dict/list or a JSON string.

    Returns:
        OutputBlocksValidationResult with errors and warnings.
    """
    result = OutputBlocksValidationResult()

    # Parse if string
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            result.is_valid = False
            result.errors.append(BlockValidationError(
                block_index=-1,
                block_id="",
                field="root",
                error="invalid_json",
            ))
            return result
    elif raw is None:
        # Null is valid (empty output blocks)
        return result
    else:
        data = raw

    # Expect { "blocks": [...] } or just [...]
    blocks: List[Dict[str, Any]] = []
    if isinstance(data, dict):
        blocks = data.get("blocks", [])
        if not isinstance(blocks, list):
            result.is_valid = False
            result.errors.append(BlockValidationError(
                block_index=-1,
                block_id="",
                field="blocks",
                error="blocks_must_be_array",
            ))
            return result
    elif isinstance(data, list):
        blocks = data
    else:
        result.is_valid = False
        result.errors.append(BlockValidationError(
            block_index=-1,
            block_id="",
            field="root",
            error="expected_object_or_array",
        ))
        return result

    result.blocks_validated = len(blocks)

    for idx, block in enumerate(blocks):
        if not isinstance(block, dict):
            result.is_valid = False
            result.errors.append(BlockValidationError(
                block_index=idx,
                block_id="",
                field="block",
                error="block_must_be_object",
            ))
            continue

        block_id = str(block.get("block_id", ""))

        # Required fields
        _validate_required_field(result, idx, block_id, block, "block_id")
        _validate_required_field(result, idx, block_id, block, "block_type")
        _validate_required_field(result, idx, block_id, block, "audience")
        _validate_required_field(result, idx, block_id, block, "document_type")

        # Allowed values
        block_type = block.get("block_type", "")
        if block_type and block_type not in ALLOWED_BLOCK_TYPES:
            result.is_valid = False
            result.errors.append(BlockValidationError(
                block_index=idx,
                block_id=block_id,
                field="block_type",
                error=f"invalid_block_type:{block_type}",
            ))

        audience = block.get("audience", "")
        if audience and audience not in ALLOWED_AUDIENCES:
            result.is_valid = False
            result.errors.append(BlockValidationError(
                block_index=idx,
                block_id=block_id,
                field="audience",
                error=f"invalid_audience:{audience}",
            ))

        document_type = block.get("document_type", "")
        if document_type and document_type not in ALLOWED_DOCUMENT_TYPES:
            result.is_valid = False
            result.errors.append(BlockValidationError(
                block_index=idx,
                block_id=block_id,
                field="document_type",
                error=f"invalid_document_type:{document_type}",
            ))

        # template_text validation (required for rendering)
        template_text = block.get("template_text")
        if template_text is not None and not isinstance(template_text, str):
            result.is_valid = False
            result.errors.append(BlockValidationError(
                block_index=idx,
                block_id=block_id,
                field="template_text",
                error="template_text_must_be_string",
            ))

        # Variables validation
        variables = block.get("variables", [])
        if isinstance(variables, list):
            for var_idx, var in enumerate(variables):
                if isinstance(var, dict):
                    if not var.get("name") and not var.get("source_field"):
                        result.is_valid = False
                        result.errors.append(BlockValidationError(
                            block_index=idx,
                            block_id=block_id,
                            field=f"variables[{var_idx}]",
                            error="variable_missing_name_and_source_field",
                        ))
                    elif not var.get("source_field"):
                        result.is_valid = False
                        result.errors.append(BlockValidationError(
                            block_index=idx,
                            block_id=block_id,
                            field=f"variables[{var_idx}].source_field",
                            error="missing_source_field",
                        ))
                    missing_behavior = var.get("missing_behavior", "")
                    if missing_behavior and missing_behavior not in ALLOWED_MISSING_BEHAVIORS:
                        result.is_valid = False
                        result.errors.append(BlockValidationError(
                            block_index=idx,
                            block_id=block_id,
                            field=f"variables[{var_idx}].missing_behavior",
                            error=f"invalid_missing_behavior:{missing_behavior}",
                        ))

        # Approval status
        approval_status = block.get("approval_status", "")
        if approval_status and approval_status not in ALLOWED_APPROVAL_STATUSES:
            result.is_valid = False
            result.errors.append(BlockValidationError(
                block_index=idx,
                block_id=block_id,
                field="approval_status",
                error=f"invalid_approval_status:{approval_status}",
            ))

        # Client-facing blocks must have snapshot_policy
        if (
            audience == "client"
            and document_type in CLIENT_FACING_DOCUMENT_TYPES
        ):
            snapshot_policy = block.get("snapshot_policy")
            if not snapshot_policy or not isinstance(snapshot_policy, dict):
                result.warnings.append(BlockValidationError(
                    block_index=idx,
                    block_id=block_id,
                    field="snapshot_policy",
                    error="client_facing_block_missing_snapshot_policy",
                    severity="warning",
                ))

    return result


def _validate_required_field(
    result: OutputBlocksValidationResult,
    idx: int,
    block_id: str,
    block: Dict[str, Any],
    field_name: str,
) -> None:
    """Check that a required field exists and is non-empty."""
    value = block.get(field_name)
    if not value:
        result.is_valid = False
        result.errors.append(BlockValidationError(
            block_index=idx,
            block_id=block_id,
            field=field_name,
            error=f"required_field_missing:{field_name}",
        ))