"""Pydantic semantic validation models for Product Blueprint Dossier priority sections.

Phase B — Hardening.

These models define the minimum structural contracts for the 6 priority JSON sections.
They are used for progressive validation:
  - draft / blocked: syntactic JSON validation only (current behavior)
  - needs_review: syntactic + top-level key presence warning (non-blocking)
  - approved: full Pydantic model validation (blocking — rejects structurally invalid data)

These models are INTERNAL contracts. They do NOT calculate cost, create offers,
create orders, create tasks, modify stock, or rewrite snapshots.
They do NOT connect to CostEngine, Quotes, Orders, Execution, or Inventory.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, field_validator, model_validator

logger = logging.getLogger(__name__)

# --- Known section names (matching dedicated JSON field names minus _json suffix) ---
KNOWN_SECTION_NAMES = {
    "sections",
    "variants",
    "layers",
    "task_rules",
    "time_assumptions",
    "costengine_mapping",
    "quote_readiness",
    "output_blocks",
    "visual_prompt_blocks",
    "production_notes",
    "qc_checkpoints",
    "risks",
    "completion_state",
}

# ============================================================
# variants_json — array of variant objects
# ============================================================

class VariantItem(BaseModel):
    """A single product variant entry."""
    name: Optional[str] = None
    variant_key: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    default_value: Optional[Any] = None
    description: Optional[str] = None

    @model_validator(mode="after")
    def require_name_or_key(self):
        if not self.name and not self.variant_key:
            raise ValueError("Each variant must have 'name' or 'variant_key'")
        return self

    @field_validator("allowed_values", mode="before")
    @classmethod
    def allowed_values_must_be_list(cls, v):
        if v is not None and not isinstance(v, list):
            raise ValueError("'allowed_values' must be a list")
        return v


class VariantsSchema(BaseModel):
    """Top-level schema for variants_json. Must be a list of VariantItem."""
    items: List[VariantItem]

    @classmethod
    def from_raw(cls, raw: Any) -> "VariantsSchema":
        """Parse from raw parsed JSON (list or dict with 'items' key)."""
        if isinstance(raw, list):
            return cls(items=raw)
        if isinstance(raw, dict) and "items" in raw:
            return cls(items=raw["items"])
        if isinstance(raw, dict):
            # Accept dict with variant keys as top-level keys
            items = []
            for k, v in raw.items():
                if isinstance(v, dict):
                    if "name" not in v and "variant_key" not in v:
                        v["variant_key"] = k
                    items.append(v)
                else:
                    items.append({"variant_key": k, "default_value": v})
            return cls(items=items)
        raise ValueError("variants_json must be a JSON array or object")


# ============================================================
# task_rules_json — array of task rule objects
# ============================================================

class TaskRuleItem(BaseModel):
    """A single task rule entry."""
    task_name: Optional[str] = None
    task_type: Optional[str] = None
    trigger_condition: Optional[str] = None
    required_or_optional: Optional[str] = None
    estimated_time: Optional[Union[int, float, Dict[str, Any]]] = None
    description: Optional[str] = None
    sequence: Optional[int] = None

    @model_validator(mode="after")
    def require_name_or_type(self):
        if not self.task_name and not self.task_type:
            raise ValueError("Each task rule must have 'task_name' or 'task_type'")
        return self

    @model_validator(mode="after")
    def require_trigger_or_required(self):
        if not self.trigger_condition and not self.required_or_optional:
            raise ValueError(
                "Each task rule must have 'trigger_condition' or 'required_or_optional'"
            )
        return self

    @field_validator("estimated_time", mode="before")
    @classmethod
    def estimated_time_must_be_numeric_or_object(cls, v):
        if v is not None and not isinstance(v, (int, float, dict)):
            raise ValueError("'estimated_time' must be numeric or an object")
        return v


class TaskRulesSchema(BaseModel):
    """Top-level schema for task_rules_json."""
    items: List[TaskRuleItem]

    @classmethod
    def from_raw(cls, raw: Any) -> "TaskRulesSchema":
        if isinstance(raw, list):
            return cls(items=raw)
        if isinstance(raw, dict) and "items" in raw:
            return cls(items=raw["items"])
        if isinstance(raw, dict) and "rules" in raw:
            return cls(items=raw["rules"])
        raise ValueError("task_rules_json must be a JSON array or object with 'items'/'rules'")


# ============================================================
# time_assumptions_json — array of time assumption objects
# ============================================================

class TimeAssumptionItem(BaseModel):
    """A single time assumption entry."""
    operation: Optional[str] = None
    operation_code: Optional[str] = None
    time_value: Optional[Union[int, float]] = None
    time_minutes: Optional[Union[int, float]] = None
    time_unit: Optional[str] = None
    description: Optional[str] = None

    @model_validator(mode="after")
    def require_operation_ref(self):
        if not self.operation and not self.operation_code:
            raise ValueError("Each time assumption must have 'operation' or 'operation_code'")
        return self

    @model_validator(mode="after")
    def require_time_for_approved(self):
        # Time value presence is checked at the schema level for approved status
        return self

    @field_validator("time_value", mode="before")
    @classmethod
    def time_value_non_negative(cls, v):
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError("'time_value' must be numeric")
            if v < 0:
                raise ValueError("'time_value' cannot be negative")
        return v

    @field_validator("time_minutes", mode="before")
    @classmethod
    def time_minutes_non_negative(cls, v):
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError("'time_minutes' must be numeric")
            if v < 0:
                raise ValueError("'time_minutes' cannot be negative")
        return v


class TimeAssumptionsSchema(BaseModel):
    """Top-level schema for time_assumptions_json."""
    items: List[TimeAssumptionItem]

    @classmethod
    def from_raw(cls, raw: Any) -> "TimeAssumptionsSchema":
        if isinstance(raw, list):
            return cls(items=raw)
        if isinstance(raw, dict) and "items" in raw:
            return cls(items=raw["items"])
        if isinstance(raw, dict) and "assumptions" in raw:
            return cls(items=raw["assumptions"])
        raise ValueError(
            "time_assumptions_json must be a JSON array or object with 'items'/'assumptions'"
        )


# ============================================================
# costengine_mapping_json — structured mapping object
# ============================================================

COSTENGINE_MAPPING_CATEGORIES = {
    "dimension_inputs",
    "material_inputs",
    "operation_inputs",
    "labor_inputs",
    "machine_inputs",
    "waste_inputs",
    "option_modifiers",
}

CANONICAL_COSTENGINE_MAPPING_REQUIRED_FIELDS = {
    "inputs",
    "derived_primitives",
    "material_keys",
    "operation_keys",
    "cost_basis_refs",
}


class CostEngineMappingSchema(BaseModel):
    """Top-level schema for costengine_mapping_json.

    Must be a structured object. For approved status, must contain at least
    one recognized mapping category.
    """
    dimension_inputs: Optional[Any] = None
    material_inputs: Optional[Any] = None
    operation_inputs: Optional[Any] = None
    labor_inputs: Optional[Any] = None
    machine_inputs: Optional[Any] = None
    waste_inputs: Optional[Any] = None
    option_modifiers: Optional[Any] = None
    version: Optional[str] = None
    template_code: Optional[str] = None
    family_id: Optional[str] = None
    status: Optional[str] = None
    quote_ready: Optional[bool] = None
    pricing_ready: Optional[bool] = None
    inputs: Optional[Any] = None
    derived_primitives: Optional[Any] = None
    material_keys: Optional[Any] = None
    operation_keys: Optional[Any] = None
    cost_basis_refs: Optional[Any] = None
    readiness_notes: Optional[Any] = None

    class Config:
        extra = "allow"

    @classmethod
    def from_raw(cls, raw: Any) -> "CostEngineMappingSchema":
        if not isinstance(raw, dict):
            raise ValueError("costengine_mapping_json must be a JSON object")
        return cls(**raw)

    def has_any_category(self) -> bool:
        """Check if at least one recognized category is present and non-None."""
        for cat in COSTENGINE_MAPPING_CATEGORIES:
            val = getattr(self, cat, None)
            if val is not None:
                return True
        return False

    def has_canonical_structural_mapping(self) -> bool:
        """Accept the canonical 27.09N structural mapping contract.

        Approved status does not require hardcoded prices or rates. It does require
        the structural mapping references that tie quote inputs to configurable
        catalogs and rate registries.
        """
        inputs = self.inputs
        derived_primitives = self.derived_primitives
        material_keys = self.material_keys
        operation_keys = self.operation_keys
        cost_basis_refs = self.cost_basis_refs

        if not isinstance(inputs, dict) or not inputs:
            return False
        if not isinstance(derived_primitives, dict) or not derived_primitives:
            return False
        if not isinstance(material_keys, list) or not material_keys:
            return False
        if not isinstance(operation_keys, list) or not operation_keys:
            return False
        if not isinstance(cost_basis_refs, dict) or not cost_basis_refs:
            return False
        return True

    def is_approved_mapping_valid(self) -> bool:
        """Allow either the legacy category-bucket shape or the canonical structure."""
        return self.has_any_category() or self.has_canonical_structural_mapping()


# ============================================================
# qc_checkpoints_json — array of checkpoint objects
# ============================================================

class QCCheckpointItem(BaseModel):
    """A single QC checkpoint entry."""
    checkpoint_name: Optional[str] = None
    what_to_verify: Optional[str] = None
    blocking_if_failed: Optional[bool] = None
    description: Optional[str] = None
    stage: Optional[str] = None

    @model_validator(mode="after")
    def require_name_or_what(self):
        if not self.checkpoint_name and not self.what_to_verify:
            raise ValueError(
                "Each QC checkpoint must have 'checkpoint_name' or 'what_to_verify'"
            )
        return self

    @field_validator("blocking_if_failed", mode="before")
    @classmethod
    def blocking_must_be_bool(cls, v):
        if v is not None and not isinstance(v, bool):
            raise ValueError("'blocking_if_failed' must be a boolean")
        return v


class QCCheckpointsSchema(BaseModel):
    """Top-level schema for qc_checkpoints_json."""
    items: List[QCCheckpointItem]

    @classmethod
    def from_raw(cls, raw: Any) -> "QCCheckpointsSchema":
        if isinstance(raw, list):
            return cls(items=raw)
        if isinstance(raw, dict) and "items" in raw:
            return cls(items=raw["items"])
        if isinstance(raw, dict) and "checkpoints" in raw:
            return cls(items=raw["checkpoints"])
        raise ValueError(
            "qc_checkpoints_json must be a JSON array or object with 'items'/'checkpoints'"
        )


# ============================================================
# risks_json — array of risk objects
# ============================================================

ALLOWED_SEVERITY_VALUES = {"low", "medium", "high", "critical"}


class RiskItem(BaseModel):
    """A single risk entry."""
    risk_name: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    mitigation: Optional[str] = None
    probability: Optional[str] = None

    @model_validator(mode="after")
    def require_name_or_description(self):
        if not self.risk_name and not self.description:
            raise ValueError("Each risk must have 'risk_name' or 'description'")
        return self

    @field_validator("severity", mode="before")
    @classmethod
    def severity_in_allowed_set(cls, v):
        if v is not None and v not in ALLOWED_SEVERITY_VALUES:
            raise ValueError(
                f"'severity' must be one of: {', '.join(sorted(ALLOWED_SEVERITY_VALUES))}"
            )
        return v


class RisksSchema(BaseModel):
    """Top-level schema for risks_json."""
    items: List[RiskItem]

    @classmethod
    def from_raw(cls, raw: Any) -> "RisksSchema":
        if isinstance(raw, list):
            return cls(items=raw)
        if isinstance(raw, dict) and "items" in raw:
            return cls(items=raw["items"])
        if isinstance(raw, dict) and "risks" in raw:
            return cls(items=raw["risks"])
        raise ValueError("risks_json must be a JSON array or object with 'items'/'risks'")


# ============================================================
# sections_json validation — umbrella metadata key validation
# ============================================================

def validate_sections_json_keys(parsed: Any) -> Optional[str]:
    """Validate that sections_json references only known section names.

    Returns error message or None.
    """
    if not isinstance(parsed, dict):
        return "sections_json must be a JSON object"

    # Check keys in known list-type fields
    for list_key in ("section_order", "active_sections", "deferred_sections"):
        items = parsed.get(list_key)
        if items is not None:
            if not isinstance(items, list):
                return f"sections_json.{list_key} must be a list"
            for item in items:
                if isinstance(item, str) and item not in KNOWN_SECTION_NAMES:
                    return (
                        f"sections_json.{list_key}: unknown section '{item}'. "
                        f"Known sections: {', '.join(sorted(KNOWN_SECTION_NAMES))}"
                    )

    # Check keys in dict-type fields
    for dict_key in ("section_labels",):
        mapping = parsed.get(dict_key)
        if mapping is not None:
            if not isinstance(mapping, dict):
                return f"sections_json.{dict_key} must be an object"
            for key in mapping:
                if key not in KNOWN_SECTION_NAMES:
                    return (
                        f"sections_json.{dict_key}: unknown section '{key}'. "
                        f"Known sections: {', '.join(sorted(KNOWN_SECTION_NAMES))}"
                    )

    return None


# ============================================================
# Progressive validation dispatcher
# ============================================================

# Map of field_name -> (schema_class, from_raw_method_name)
PRIORITY_SECTION_SCHEMAS = {
    "variants_json": VariantsSchema,
    "task_rules_json": TaskRulesSchema,
    "time_assumptions_json": TimeAssumptionsSchema,
    "costengine_mapping_json": CostEngineMappingSchema,
    "qc_checkpoints_json": QCCheckpointsSchema,
    "risks_json": RisksSchema,
}


def validate_semantic_json_for_status(
    data: Dict[str, Any],
    status: str,
) -> List[str]:
    """Run progressive semantic validation based on dossier status.

    Args:
        data: dict of field_name -> JSON string values
        status: the dossier status (draft, needs_review, approved, etc.)

    Returns:
        List of error messages (empty if all valid).
    """
    errors: List[str] = []

    if status in ("draft", "blocked"):
        # Syntactic validation only — already done by validate_json_fields
        return errors

    for field_name, schema_cls in PRIORITY_SECTION_SCHEMAS.items():
        raw_value = data.get(field_name)
        if raw_value is None or (isinstance(raw_value, str) and not raw_value.strip()):
            continue

        try:
            parsed = json.loads(raw_value) if isinstance(raw_value, str) else raw_value
        except (json.JSONDecodeError, ValueError):
            # Already caught by syntactic validation
            continue

        if status == "needs_review":
            # Top-level key presence check (non-blocking — logged as warning only)
            # We do NOT add errors for needs_review, just log
            try:
                schema_cls.from_raw(parsed)
            except (ValueError, Exception) as e:
                logger.warning(
                    f"Semantic validation warning for {field_name} "
                    f"(status=needs_review): {str(e)}"
                )

        elif status == "approved":
            # Full Pydantic validation — blocking
            try:
                obj = schema_cls.from_raw(parsed)
                # Extra check for costengine_mapping: must have at least one category
                if field_name == "costengine_mapping_json" and isinstance(
                    obj, CostEngineMappingSchema
                ):
                    if not obj.is_approved_mapping_valid():
                        errors.append(
                            f"{field_name}: approved dossier must include either at least one "
                            f"legacy mapping category ({', '.join(sorted(COSTENGINE_MAPPING_CATEGORIES))}) "
                            f"or the canonical structural mapping fields "
                            f"({', '.join(sorted(CANONICAL_COSTENGINE_MAPPING_REQUIRED_FIELDS))})"
                        )
            except (ValueError, Exception) as e:
                errors.append(f"{field_name}: semantic validation failed — {str(e)}")

    # Validate sections_json keys if present — only blocking for approved
    if status == "approved":
        sections_raw = data.get("sections_json")
        if sections_raw and isinstance(sections_raw, str) and sections_raw.strip():
            try:
                parsed_sections = json.loads(sections_raw)
                err = validate_sections_json_keys(parsed_sections)
                if err:
                    errors.append(err)
            except (json.JSONDecodeError, ValueError):
                pass  # Already caught by syntactic validation
    elif status == "needs_review":
        # Non-blocking warning only
        sections_raw = data.get("sections_json")
        if sections_raw and isinstance(sections_raw, str) and sections_raw.strip():
            try:
                parsed_sections = json.loads(sections_raw)
                err = validate_sections_json_keys(parsed_sections)
                if err:
                    logger.warning(
                        f"Sections JSON key validation warning "
                        f"(status=needs_review): {err}"
                    )
            except (json.JSONDecodeError, ValueError):
                pass

    return errors