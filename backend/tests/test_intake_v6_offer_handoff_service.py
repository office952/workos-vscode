from __future__ import annotations

from types import SimpleNamespace

import pytest

from services import intake_v6_offer_handoff_service as handoff_service


@pytest.mark.asyncio
async def test_handoff_creates_quote_then_writes_backend_priced_totals(monkeypatch) -> None:
    async def fake_create_or_reuse(_db, workspace_id, request, current_user):
        assert workspace_id == "workspace-v6"
        assert request.client_analysis_hash == "a" * 64
        assert request.confirm_internal_draft_quote is True
        assert current_user.email == "ops@example.com"
        return SimpleNamespace(
            quote_created=True,
            quote_id=6,
            quote_code="Q-V6-IV6-TEST-1",
            quote_status="draft",
        )

    async def fake_write(
        _db,
        workspace_id,
        *,
        quote_id,
        expected_total_gross,
        expected_pricing_hash,
        operator_confirmation,
        operator_identifier,
    ):
        assert workspace_id == "workspace-v6"
        assert quote_id == 6
        assert expected_total_gross == 1190.0
        assert expected_pricing_hash == "hash-123"
        assert operator_confirmation is True
        assert operator_identifier == "ops@example.com"
        return {
            "status": "V6_PRICED_QUOTE_WRITTEN",
            "commercial_totals": {"total_gross": 1190.0, "currency": "RON"},
            "line_items": [{"description": "Debitare fata"}],
            "pricing_trace": {"pricing_hash": "hash-123"},
            "blockers": [],
            "warnings": [],
            "can_create_quote_snapshot": True,
        }

    monkeypatch.setattr(
        handoff_service,
        "create_or_reuse_guarded_draft_quote_from_intake_v6_workspace",
        fake_create_or_reuse,
    )
    monkeypatch.setattr(
        handoff_service,
        "write_intake_v6_priced_quote_totals",
        fake_write,
    )

    current_user = SimpleNamespace(id="u1", email="ops@example.com", name="Ops")

    result = await handoff_service.handoff_intake_v6_workspace_to_offer(
        None,
        "workspace-v6",
        client_analysis_hash="a" * 64,
        expected_total_gross=1190.0,
        expected_pricing_hash="hash-123",
        operator_confirmation=True,
        current_user=current_user,
    )

    assert result["status"] == "V6_PRICED_QUOTE_WRITTEN"
    assert result["quote_created"] is True
    assert result["quote_id"] == 6
    assert result["quote_code"] == "Q-V6-IV6-TEST-1"
    assert result["quote_status"] == "priced"
    assert result["next_route"] == "/quotes/Q-V6-IV6-TEST-1"
    assert result["can_create_quote_snapshot"] is True


@pytest.mark.asyncio
async def test_handoff_reuses_existing_quote_when_present(monkeypatch) -> None:
    async def fake_create_or_reuse(_db, _workspace_id, _request, _current_user):
        return SimpleNamespace(
            quote_created=False,
            quote_id=42,
            quote_code="Q-V6-IV6-EXISTING",
            quote_status="draft",
        )

    async def fake_write(_db, _workspace_id, **_kwargs):
        return {
            "status": "V6_PRICED_QUOTE_WRITTEN",
            "commercial_totals": {"total_gross": 2200.0, "currency": "RON"},
            "line_items": [],
            "pricing_trace": {},
            "blockers": [],
            "warnings": [],
            "can_create_quote_snapshot": True,
        }

    monkeypatch.setattr(
        handoff_service,
        "create_or_reuse_guarded_draft_quote_from_intake_v6_workspace",
        fake_create_or_reuse,
    )
    monkeypatch.setattr(
        handoff_service,
        "write_intake_v6_priced_quote_totals",
        fake_write,
    )

    current_user = SimpleNamespace(id="u1", email="ops@example.com", name="Ops")
    result = await handoff_service.handoff_intake_v6_workspace_to_offer(
        None,
        "workspace-v6",
        client_analysis_hash="b" * 64,
        expected_total_gross=2200.0,
        expected_pricing_hash=None,
        operator_confirmation=True,
        current_user=current_user,
    )

    assert result["quote_created"] is False
    assert result["quote_id"] == 42
    assert result["next_route"] == "/quotes/Q-V6-IV6-EXISTING"