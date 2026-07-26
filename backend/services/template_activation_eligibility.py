"""TEMPLATE_ACTIVATION_V1 — shared eligibility map (activation vs publication).

Configured AI defaults are valid operational truth. Structural blockers remain.
Optional capabilities (ACM logo / treatments) do not suspend base shell readiness.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from data.ai_operational_defaults_v1 import SOURCE_PRECEDENCE

OperationalReadiness = Literal[
    "ACTIVE_WITH_CONFIRMED_TRUTH",
    "ACTIVE_WITH_AI_DEFAULTS",
    "ACTIVE_WITH_WARNINGS",
    "BLOCKED",
]

# known_conflicts that remain hard publish blockers
STRUCTURAL_KNOWN_CONFLICTS = frozenset(
    {
        "required_inactive_child",
    }
)

OPTIONAL_CAPABILITY_CHECK_IDS = frozenset(
    {
        "components.acm_logo_branch_honesty",
        "components.acm_face_treatment_commercial_path",
        "acm_face_treatment.commercial_path",
    }
)


def is_structural_known_conflict(code: str) -> bool:
    return str(code or "").strip() in STRUCTURAL_KNOWN_CONFLICTS


def classify_finding_scope(finding: dict[str, Any] | Any) -> str:
    """Return structural | optional_capability | warning."""
    if isinstance(finding, dict):
        check_id = str(finding.get("check_id") or finding.get("code") or "")
        blocking = bool(finding.get("blocking"))
        status = str(finding.get("status") or "")
        evidence = finding.get("evidence") if isinstance(finding.get("evidence"), dict) else {}
    else:
        check_id = str(getattr(finding, "check_id", None) or "")
        blocking = bool(getattr(finding, "blocking", False))
        status = str(getattr(finding, "status", None) or "")
        evidence = getattr(finding, "evidence", None)
        evidence = evidence if isinstance(evidence, dict) else {}

    if check_id in OPTIONAL_CAPABILITY_CHECK_IDS or evidence.get("optional_absent_ok") is True:
        return "optional_capability"
    if evidence.get("publication") == "KEEP_DRAFT" and not blocking:
        return "optional_capability"
    if blocking or status in {"FAIL", "BLOCKED"}:
        # BLOCKED status without blocking flag on optional honesty → already handled above
        if status == "BLOCKED" and not blocking:
            return "warning"
        return "structural"
    return "warning"


def build_activation_eligibility(
    *,
    template_code: str,
    publication_status: Optional[str],
    effective_status: str,
    db_active: bool,
    e2e_verdict: Optional[str],
    e2e_ready: bool,
    known_conflicts: list[str],
    findings: list[Any],
    pricing_activation: Optional[str],
    ai_decisions: list[dict[str, Any]],
    acm_treatment_allowed: Optional[bool] = None,
) -> dict[str, Any]:
    """Single shared map for agents / API / UI."""
    structural: list[str] = []
    optional: list[str] = []
    warnings: list[str] = []

    for conflict in known_conflicts:
        if is_structural_known_conflict(conflict):
            structural.append(f"known_conflict:{conflict}")
        else:
            warnings.append(f"known_conflict:{conflict}")

    for f in findings:
        scope = classify_finding_scope(f)
        if isinstance(f, dict):
            label = str(f.get("check_id") or f.get("code") or f.get("message") or "finding")
            blocking = bool(f.get("blocking"))
            status = str(f.get("status") or "")
        else:
            label = str(getattr(f, "check_id", None) or getattr(f, "message", None) or "finding")
            blocking = bool(getattr(f, "blocking", False))
            status = str(getattr(f, "status", None) or "")
        if scope == "structural" and (blocking or status in {"FAIL", "BLOCKED"}):
            structural.append(label)
        elif scope == "optional_capability":
            optional.append(label)
        else:
            warnings.append(label)

    if not db_active:
        structural.append("template_inactive")

    publishable_verdicts = {
        "STATIC_READY",
        "STATIC_READY_WITH_WARNINGS",
        "RUNTIME_READY",
    }
    verdict_ok = str(e2e_verdict or "") in publishable_verdicts
    # e2e_ready may be false for STATIC_READY_WITH_WARNINGS — still publishable
    activation_eligible = db_active and (
        (pricing_activation or "").startswith("ACTIVE")
        or verdict_ok
    )
    publication_eligible = (
        db_active
        and verdict_ok
        and not structural
    )

    ai_ids = [str(d.get("decision_id")) for d in ai_decisions if d.get("decision_id")]
    uses_ai = bool(ai_ids) or (pricing_activation == "ACTIVE_WITH_AI_DEFAULTS")

    target = "KEEP_LEGACY_UNSPECIFIED"
    if publication_eligible:
        target = "PUBLISHED"
    elif activation_eligible and structural:
        target = "ACTIVE_BLOCKED_PUBLISH"
    elif activation_eligible:
        target = "ACTIVE_UNPUBLISHED"
    elif not db_active:
        target = "INACTIVE"

    return {
        "template_code": template_code,
        "current_lifecycle": publication_status or effective_status,
        "active": db_active,
        "published": publication_status == "PUBLISHED",
        "technical_readiness": verdict_ok,
        "commercial_readiness": (pricing_activation or "").startswith("ACTIVE"),
        "operational_readiness": pricing_activation,
        "ai_defaults": {
            "uses_ai_defaults": uses_ai,
            "ai_decision_ids": ai_ids,
            "precedence": list(SOURCE_PRECEDENCE),
        },
        "warnings": sorted(set(warnings))[:40],
        "structural_blockers": sorted(set(structural)),
        "optional_capability_blockers": sorted(set(optional)),
        "e2e_verdict": e2e_verdict,
        "e2e_ready": e2e_ready,
        "acm_treatment_commercial_lines_allowed": acm_treatment_allowed,
        "publication_eligible": publication_eligible,
        "activation_eligible": activation_eligible,
        "target_state": target,
        "confidence": "high" if publication_eligible or structural else "medium",
        "contract_version": "template_activation_eligibility_v1",
    }
