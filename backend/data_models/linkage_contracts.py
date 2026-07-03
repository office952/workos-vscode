"""
Phase 4 — Registry Linkage Validation contracts.

Canonical data shapes for the LinkageValidationResult returned by
ProductSystemLinkageValidator.validate_template_linkage().

These are pure data containers (Pydantic models for serialization).
No business logic lives here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class LinkageIssue(BaseModel):
    """A single linkage validation issue (blocker or warning)."""

    model_config = ConfigDict(extra="forbid")

    severity: str  # "blocker" | "warning"
    task_template_id: str
    path: str  # e.g. "task_templates[0].required_skill_ids[1]"
    code: str  # e.g. "PS-BLK-09"
    message: str
    details: Dict[str, Any] = {}


class LinkageValidationResult(BaseModel):
    """Full validation result for a product template's linkage."""

    model_config = ConfigDict(extra="forbid")

    template_id: int
    template_code: str
    valid: bool  # true iff len(blockers) == 0
    blockers: List[LinkageIssue] = []
    warnings: List[LinkageIssue] = []
    missing_links: List[LinkageIssue] = []  # union of blockers + warnings
    registries_consulted: List[str] = []
    registries_unavailable: List[str] = []
    task_template_count: int = 0
    timestamp: str = ""

    @classmethod
    def build(
        cls,
        *,
        template_id: int,
        template_code: str,
        blockers: List[LinkageIssue],
        warnings: List[LinkageIssue],
        registries_consulted: List[str],
        registries_unavailable: List[str],
        task_template_count: int,
    ) -> "LinkageValidationResult":
        missing_links = blockers + warnings
        return cls(
            template_id=template_id,
            template_code=template_code,
            valid=len(blockers) == 0,
            blockers=blockers,
            warnings=warnings,
            missing_links=missing_links,
            registries_consulted=registries_consulted,
            registries_unavailable=registries_unavailable,
            task_template_count=task_template_count,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )