"""Canonical semantic comparison for preview vs freeze ActiveScopeResult.

Local helper only — not a new architectural subsystem.
"""

from __future__ import annotations

from typing import Any

from schemas.active_scope import ActiveScopeResult
from schemas.active_scope_snapshot import QuoteSnapshotActiveScope


class ActiveScopePreviewFreezeMismatch(ValueError):
    """Preview and freeze compiled scopes differ semantically."""

    def __init__(self, diffs: list[str]) -> None:
        self.diffs = list(diffs)
        super().__init__(
            "ACTIVE_SCOPE_PREVIEW_FREEZE_MISMATCH: " + "; ".join(self.diffs)
        )


def _sorted_list(values: list[str] | None) -> list[str]:
    return sorted(str(v) for v in (values or []) if str(v).strip())


def _norm_null_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    return _sorted_list(values)


def canonical_active_scope_projection(result: ActiveScopeResult) -> dict[str, Any]:
    """Projection used for semantic equality (excludes freeze-only metadata)."""
    deps = sorted(
        (
            {
                "code": d.code,
                "dependency_class": d.dependency_class,
                "reason": d.reason,
                "required_by": _sorted_list(list(d.required_by or [])),
            }
            for d in (result.dependencies or [])
        ),
        key=lambda row: (row["code"], row["dependency_class"]),
    )
    return {
        "contract_version": result.contract_version,
        "resolver_version": result.resolver_version,
        "template_code": result.template_code,
        "mode": result.mode,
        "use_legacy_full_product": bool(result.use_legacy_full_product),
        "sold_module_codes": _norm_null_list(result.sold_module_codes),
        "active_runtime_modules": _norm_null_list(result.active_runtime_modules),
        "inactive_runtime_modules": _norm_null_list(result.inactive_runtime_modules),
        "calculation_prerequisites": _norm_null_list(result.calculation_prerequisites),
        "commercial_scope_modules": _norm_null_list(result.commercial_scope_modules),
        "execution_scope_modules": _norm_null_list(result.execution_scope_modules),
        "composition_excluded_operations": _norm_null_list(
            result.composition_excluded_operations
        ),
        "dependencies": deps,
        "warnings": _norm_null_list(result.warnings),
        "errors": _norm_null_list(result.errors),
    }


def compare_active_scope_semantics(
    left: ActiveScopeResult,
    right: ActiveScopeResult,
) -> list[str]:
    """Return exact semantic field paths that differ (empty = equal)."""
    a = canonical_active_scope_projection(left)
    b = canonical_active_scope_projection(right)
    diffs: list[str] = []
    for key in a:
        if a[key] != b[key]:
            diffs.append(f"{key}: {a[key]!r} != {b[key]!r}")
    return diffs


def assert_preview_freeze_semantic_match(
    preview: ActiveScopeResult,
    frozen: ActiveScopeResult,
) -> None:
    diffs = compare_active_scope_semantics(preview, frozen)
    if diffs:
        raise ActiveScopePreviewFreezeMismatch(diffs)


def freeze_identity_fields(snapshot: QuoteSnapshotActiveScope) -> dict[str, Any]:
    """Identity preserved across preview/freeze (not compared as compiled body)."""
    return {
        "active_scope_snapshot_version": snapshot.active_scope_snapshot_version,
        "source_template_code": snapshot.source_template_code,
        "source_offer_scope_version": snapshot.source_offer_scope_version,
        "resolver_version": snapshot.resolver_version,
        "active_scope_contract_version": snapshot.active_scope_contract_version,
    }
