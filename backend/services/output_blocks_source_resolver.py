"""
BUILD 8 — Output Blocks Source Resolver.

Controlled variable resolution for Output Blocks rendering.
Reads ONLY from permitted sources:
  - ProductTemplate fields
  - ProductFamily fields
  - BlueprintDossier fields
  - quote_context from request
  - readiness DTO (read-only)

Forbidden sources:
  - AI output
  - Free random text
  - Frontend-only values
  - Inventory mutation
  - ExecutionTask
  - ExecutionReality
  - Order mutation

Rules:
  - Unknown source field -> warning or blocker (never crash)
  - Missing required field -> blocker
  - Missing optional field -> warning
  - All resolved values reported in variables_used
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class ResolvedVariable:
    name: str
    source_field: str
    value: Any = None
    resolved: bool = False
    missing: bool = False


@dataclass
class SourceResolverResult:
    variables_used: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variables_used": self.variables_used,
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
        }


# ---------------------------------------------------------------------------
# Source Resolver
# ---------------------------------------------------------------------------

class OutputBlocksSourceResolver:
    """Resolves variables from permitted sources only."""

    def __init__(
        self,
        *,
        template_data: Optional[Dict[str, Any]] = None,
        family_data: Optional[Dict[str, Any]] = None,
        dossier_data: Optional[Dict[str, Any]] = None,
        quote_context: Optional[Dict[str, Any]] = None,
        readiness_data: Optional[Dict[str, Any]] = None,
    ):
        self._template = template_data or {}
        self._family = family_data or {}
        self._dossier = dossier_data or {}
        self._quote_context = quote_context or {}
        self._readiness = readiness_data or {}

    def resolve_variables(
        self,
        variables: List[Dict[str, Any]],
    ) -> SourceResolverResult:
        """Resolve a list of variable definitions against permitted sources.

        Each variable dict should have:
          - name: str
          - source_field: str (e.g. "identity.product_name")
          - required: bool (default True)
          - missing_behavior: str (default "block_rendering")
        """
        result = SourceResolverResult()

        for var_def in variables:
            if not isinstance(var_def, dict):
                continue

            name = var_def.get("name", "")
            source_field = var_def.get("source_field", "")
            required = var_def.get("required", True)
            missing_behavior = var_def.get("missing_behavior", "block_rendering")

            if not source_field:
                result.blockers.append(f"variable '{name}' has no source_field")
                result.variables_used.append({
                    "name": name,
                    "source_field": "",
                    "value": None,
                    "resolved": False,
                })
                continue

            value = self._resolve_single(source_field)

            if value is None:
                # Field not found or empty
                entry = {
                    "name": name,
                    "source_field": source_field,
                    "value": None,
                    "resolved": False,
                }
                result.variables_used.append(entry)

                if required:
                    if missing_behavior == "block_rendering":
                        result.blockers.append(
                            f"required variable '{name}' missing from source '{source_field}'"
                        )
                    elif missing_behavior == "render_with_warning":
                        result.warnings.append(
                            f"required variable '{name}' missing from source '{source_field}' (render_with_warning)"
                        )
                    elif missing_behavior == "hide_block":
                        result.blockers.append(
                            f"variable '{name}' missing -> hide_block"
                        )
                    elif missing_behavior == "use_approved_fallback":
                        result.warnings.append(
                            f"variable '{name}' missing, using approved fallback"
                        )
                    elif missing_behavior == "require_manual_review":
                        result.blockers.append(
                            f"variable '{name}' missing -> requires manual review"
                        )
                    else:
                        result.blockers.append(
                            f"required variable '{name}' missing from source '{source_field}'"
                        )
                else:
                    result.warnings.append(
                        f"optional variable '{name}' not found at '{source_field}'"
                    )
            else:
                result.variables_used.append({
                    "name": name,
                    "source_field": source_field,
                    "value": value,
                    "resolved": True,
                })

        return result

    def _resolve_single(self, source_field: str) -> Any:
        """Resolve a single source_field path.

        Supported prefixes:
          - identity.* -> template identity fields
          - template.* -> template data fields
          - family.* -> family data fields
          - dossier.* -> dossier data fields
          - quote_context.* -> quote context from request
          - readiness.* -> readiness DTO fields
        """
        parts = source_field.split(".", 1)
        if len(parts) < 2:
            return self._try_flat_lookup(source_field)

        prefix = parts[0]
        remainder = parts[1]

        if prefix == "identity":
            return self._resolve_from_dict(self._template, remainder, identity_mode=True)
        elif prefix == "template":
            return self._resolve_from_dict(self._template, remainder)
        elif prefix == "family":
            return self._resolve_from_dict(self._family, remainder)
        elif prefix == "dossier":
            return self._resolve_from_dict(self._dossier, remainder)
        elif prefix == "quote_context":
            return self._resolve_from_dict(self._quote_context, remainder)
        elif prefix == "readiness":
            return self._resolve_from_dict(self._readiness, remainder)
        else:
            # Unknown prefix — not a crash, just unresolved
            return None

    def _resolve_from_dict(
        self, data: Dict[str, Any], path: str, identity_mode: bool = False
    ) -> Any:
        """Navigate nested dict by dot-separated path."""
        if not data:
            return None

        # Identity mode maps common names to template fields
        if identity_mode:
            identity_map = {
                "product_name": "description",
                "template_code": "template_code",
                "family_name": "family_name",
                "family_id": "family_id",
            }
            mapped_key = identity_map.get(path, path)
            val = data.get(mapped_key)
            if val is not None:
                return val
            # Also try direct path
            return data.get(path)

        # Standard nested resolution
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            if current is None:
                return None
        return current

    def _try_flat_lookup(self, key: str) -> Any:
        """Try to find a key in all sources (flat lookup)."""
        for source in [self._template, self._family, self._dossier, self._quote_context]:
            if key in source:
                return source[key]
        return None