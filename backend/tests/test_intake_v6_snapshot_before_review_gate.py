from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from services import intake_v6_quote_to_order_service as spine_service


class FakeQuotesService:
    quote = None

    def __init__(self, _db) -> None:
        pass

    async def get_by_id(self, quote_id: int):
        if self.quote is not None:
            assert self.quote.id == quote_id
        return self.quote


def _quote() -> SimpleNamespace:
    linkage = {
        "source_module": "intake_v6",
        "source_workspace_id": "workspace-v6",
        "requires_pricing_review": True,
    }
    return SimpleNamespace(
        id=6,
        code="Q-V6-IV6-TEST",
        intake_code="IV6-workspace-v6",
        status="priced",
        notes=json.dumps({"intake_v6_linkage_v1": linkage}),
        subtotal=1000.0,
        total_before_vat=1000.0,
        vat=190.0,
        grand_total=1190.0,
    )


def _body() -> dict:
    return {
        "expected_quote_id": 6,
        "expected_intake_code": "IV6-workspace-v6",
        "reviewer_confirmation": True,
        "confirm_quote_stays_draft": True,
        "confirm_no_order": True,
        "confirm_no_execution": True,
        "confirm_no_inventory": True,
        "pricing_review_reason": "Review after frozen snapshot.",
    }


@pytest.mark.asyncio
async def test_pricing_review_requires_persisted_snapshot_v2(monkeypatch) -> None:
    FakeQuotesService.quote = _quote()

    async def no_snapshot(_db, _quote, _linkage):
        return None

    monkeypatch.setattr(spine_service, "QuotesService", FakeQuotesService)
    monkeypatch.setattr(spine_service, "_resolve_snapshot_for_v6_pricing_review", no_snapshot)

    with pytest.raises(HTTPException) as exc:
        await spine_service.complete_v6_pricing_review(
            SimpleNamespace(),
            6,
            _body(),
            SimpleNamespace(id="user-1", name="User", email="user@test.local"),
        )

    assert exc.value.detail["error"] == "MISSING_SNAPSHOT_V2"
    assert exc.value.detail["message"] == "Creeaza Snapshot V2 inainte de Review si Accept."
    assert exc.value.detail["blockers"] == ["missing_active_snapshot"]
