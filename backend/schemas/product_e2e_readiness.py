"""Product E2E Readiness Check — read-only result contract.

Statuses are evidence of the product path; NOT_TESTED is never treated as PASS.
Catalog / workspace are never written by readiness.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


ProductE2ECheckStatus = Literal[
    "PASS",
    "PASS_WITH_WARNINGS",
    "PARTIAL",
    "FAIL",
    "BLOCKED",
    "NOT_CONFIGURED",
    "NOT_TESTED",
    "LEGACY_DEPENDENCY",
    "STALE_EVIDENCE",
]

ProductE2EVerdict = Literal[
    "STATIC_READY",
    "STATIC_READY_WITH_WARNINGS",
    "RUNTIME_READY",
    "PARTIAL",
    "BLOCKED",
    "NOT_TESTED",
]

ProductE2EMode = Literal["static", "runtime_dry_run"]

ProductE2ESeverity = Literal["info", "warning", "error", "blocker"]

ProductE2ESystem = Literal[
    "catalog",
    "components",
    "intake",
    "product_truth",
    "product_definition",
    "aggregate",
    "quantity",
    "cpp",
    "eic",
    "quote_snapshot",
    "order_snapshot",
    "execution_preview",
]


class ProductE2ECheckFinding(BaseModel):
    check_id: str
    system: ProductE2ESystem
    status: ProductE2ECheckStatus
    severity: ProductE2ESeverity
    blocking: bool = False
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    evidence_type: Optional[str] = None
    source_owner: str
    template_code: Optional[str] = None
    component_template_code: Optional[str] = None
    workspace_id: Optional[str] = None
    route: Optional[str] = None
    recommended_navigation: Optional[str] = None
    technical_details: Optional[dict[str, Any]] = None


class ProductE2ESystemNode(BaseModel):
    system: ProductE2ESystem
    status: ProductE2ECheckStatus
    blocking: bool = False
    finding_count: int = 0
    summary: str = ""


class ProductE2ERuntimeDryRunRequest(BaseModel):
    workspace_id: str
    dry_run: bool = True


class ProductE2EReadinessResult(BaseModel):
    template_code: str
    mode: ProductE2EMode
    verdict: ProductE2EVerdict
    e2e_ready: bool = False
    write_performed: bool = False
    no_write: bool = True
    dry_run: bool = True
    workspace_id: Optional[str] = None
    checked_at: str
    findings: list[ProductE2ECheckFinding] = Field(default_factory=list)
    systems: list[ProductE2ESystemNode] = Field(default_factory=list)
    known_conflicts: list[str] = Field(default_factory=list)
    contract_version: str = "product_e2e_readiness_v1"
