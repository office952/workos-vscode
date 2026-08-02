"""C2 — Operator may read closure readiness; close remains management-only."""

from __future__ import annotations

from dependencies.permissions import PERMISSION_MATRIX


def test_closure_readiness_allows_operator_close_does_not():
    assert "operator" in PERMISSION_MATRIX["execution.closure_readiness"]
    assert "admin" in PERMISSION_MATRIX["execution.closure_readiness"]
    assert "manager" in PERMISSION_MATRIX["execution.closure_readiness"]
    assert "operator" not in PERMISSION_MATRIX["execution.job_close"]
    assert set(PERMISSION_MATRIX["execution.job_close"]) == {"admin", "manager"}
