from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from services import intake_v6_priced_quote_dry_run_service as dry_run


class FakeDb:
    def __init__(self) -> None:
        self.add_called = False
        self.commit_called = False

    def add(self, _obj) -> None:
        self.add_called = True

    async def commit(self) -> None:
        self.commit_called = True


class FakeCommercialPriceProposalService:
    preview = None

    def __init__(self, db) -> None:
        self.db = db

    async def build_preview(self, template_code, *, workspace_id=None, quote_input=None, currency="RON"):
        assert template_code == "TPL-VOLUMETRIC-LETTERS_v2"
        assert workspace_id == "workspace-v6"
        assert currency == "RON"
        assert quote_input is not None
        return self.preview


class FakeEstimatedInternalCostService:
    preview = None

    def __init__(self, db) -> None:
        self.db = db

    async def build_preview(self, template_code, *, workspace_id=None, quote_input=None, currency="RON"):
        return self.preview


def _record() -> SimpleNamespace:
    return SimpleNamespace(
        id="workspace-v6",
        workspace_code="IV6-TEST",
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        payload_json=(
            '{"product_binding":{"template_code":"TPL-VOLUMETRIC-LETTERS_v2"},'
            '"intake_request_code":"IR-TEST"}'
        ),
    )


def _pricing_preview(*, ready: bool = True, blockers: list[str] | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        workspace_id="workspace-v6",
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        is_ready_for_quote=ready,
        adapter_status="ready" if ready else "blocked",
        adapter_blockers=blockers or [],
        adapter_warnings=[],
        quote_input_payload={
            "intake_source": "intake_v6",
            "letter_count": 19,
            "letter_face_area_m2": 1.2638,
            "letter_perimeter_m": 20.9727,
            "preview_total_gross": 999999.0,
        },
        operation_flags={},
        production_counts={"letter_count": 19},
        finish_summary={"face_finish_type": "oracal_651"},
    )


def _material_breakdown() -> SimpleNamespace:
    return SimpleNamespace(
        workspace_id="workspace-v6",
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        totals=SimpleNamespace(
            estimated_cost_total=782.38,
            material_cost_total=782.38,
            currency="EUR",
            contains_estimates=True,
            contains_missing_prices=False,
        ),
    )


def _commercial_preview(*, subtotal: float | None = 1000.0, status: str = "ready") -> SimpleNamespace:
    return SimpleNamespace(
        source="commercial_price_proposal",
        status=status,
        subtotal_commercial=subtotal,
        commercial_total=subtotal,
        quote_ready_for_commercial_review=status == "ready",
        warnings=[],
        commercial_blockers=[],
        unknown_owner_decisions=[],
        forbidden_hourly_usage_detected=[],
        commercial_price_lines=[
            SimpleNamespace(
                code="debitare_fata",
                label="Debitare fata",
                module_code="fata",
                component_code="face",
                basis_type="m2",
                quantity=1.25,
                unit="m2",
                commercial_unit_price=800.0,
                subtotal=subtotal,
                pricing_rule_code="CPP-FACE",
                source="commercial_rules_volumetric_v2",
                owner_decision_required=False,
                warnings=[],
            )
        ],
        provenance=[SimpleNamespace(model_dump=lambda mode="json": {"key": "commercial_rules"})],
    )


@pytest.fixture(autouse=True)
def patch_dry_run_dependencies(monkeypatch):
    async def fake_get_record(_db, workspace_id):
        assert workspace_id == "workspace-v6"
        return _record()

    def fake_parse_payload(raw):
        return SimpleNamespace(
            intake_request_code=raw.get("intake_request_code"),
            product_binding=SimpleNamespace(template_code="TPL-VOLUMETRIC-LETTERS_v2"),
        )

    async def fake_material_breakdown(_db, workspace_id):
        assert workspace_id == "workspace-v6"
        return _material_breakdown()

    async def fake_vat(_db):
        return 19.0

    async def fake_eur(_db):
        return 5.0

    monkeypatch.setattr(dry_run, "_get_record_or_404", fake_get_record)
    monkeypatch.setattr(dry_run, "_parse_payload", fake_parse_payload)
    monkeypatch.setattr(dry_run, "build_v6_pricing_input_preview", lambda **_kwargs: _pricing_preview())
    monkeypatch.setattr(dry_run, "get_material_breakdown_for_workspace", fake_material_breakdown)
    monkeypatch.setattr(dry_run, "get_default_vat_pct", fake_vat)
    monkeypatch.setattr(dry_run, "get_eur_to_ron_rate", fake_eur)
    monkeypatch.setattr(dry_run, "CommercialPriceProposalService", FakeCommercialPriceProposalService)
    monkeypatch.setattr(dry_run, "EstimatedInternalCostService", FakeEstimatedInternalCostService)
    FakeCommercialPriceProposalService.preview = _commercial_preview()
    FakeEstimatedInternalCostService.preview = SimpleNamespace(
        source="estimated_internal_cost",
        status="partial",
        estimated_total_internal_cost=782.38,
        estimated_material_cost=600.0,
        estimated_operation_cost=182.38,
        currency="RON",
        internal_blockers=[],
        provenance=[],
    )


@pytest.mark.asyncio
async def test_dry_run_returns_non_zero_totals_when_backend_pricing_available() -> None:
    db = FakeDb()

    result = await dry_run.build_intake_v6_priced_quote_dry_run(db, "workspace-v6")

    assert result["pricing_status"] == dry_run.V6_PRICED_DRY_RUN_READY
    assert result["pricing_source"] == dry_run.V6_PRICED_DRY_RUN_SOURCE
    assert result["commercial_totals"]["subtotal_net"] == 1000.0
    assert result["commercial_totals"]["vat_rate"] == 19.0
    assert result["commercial_totals"]["vat_amount"] == 190.0
    assert result["commercial_totals"]["total_gross"] == 1190.0
    assert result["commercial_totals"]["currency"] == "RON"
    assert result["commercial_line_items"]
    assert result["internal_cost_trace"]["estimated_cost_total"] == 782.38
    assert result["pricing_authority"] == dry_run.V6_OFFICIAL_COMMERCIAL_AUTHORITY
    assert result["estimated_internal_cost_trace"]["available"] is True
    assert result["diagnostic_cost_plus_trace"] is not None
    assert result["diagnostic_cost_plus_trace"]["diagnostic_only"] is True
    assert "official_v6_pricing_uses_cost_plus" not in " ".join(result.get("warnings") or [])
    assert result["dry_run_only"] is True


@pytest.mark.asyncio
async def test_dry_run_does_not_create_or_update_quote() -> None:
    db = FakeDb()

    result = await dry_run.build_intake_v6_priced_quote_dry_run(db, "workspace-v6")

    assert db.add_called is False
    assert db.commit_called is False
    assert result["persistence"] == {
        "creates_quote": False,
        "updates_quote": False,
        "writes_quote_totals": False,
        "creates_quote_snapshot": False,
        "creates_order": False,
    }


@pytest.mark.asyncio
async def test_dry_run_has_write_and_snapshot_flags_false() -> None:
    result = await dry_run.build_intake_v6_priced_quote_dry_run(FakeDb(), "workspace-v6")

    assert result["can_write_quote_totals"] is False
    assert result["can_create_quote_snapshot"] is False


@pytest.mark.asyncio
async def test_dry_run_blocks_zero_totals_instead_of_ready_zero() -> None:
    FakeCommercialPriceProposalService.preview = _commercial_preview(subtotal=0.0)

    result = await dry_run.build_intake_v6_priced_quote_dry_run(FakeDb(), "workspace-v6")

    assert result["pricing_status"] == dry_run.V6_PRICED_DRY_RUN_BLOCKED
    assert result["commercial_totals"]["subtotal_net"] is None
    assert any(blocker["code"] == dry_run.V6_PRICED_DRY_RUN_ZERO_TOTAL for blocker in result["blockers"])


@pytest.mark.asyncio
async def test_missing_pricing_source_returns_blocked(monkeypatch) -> None:
    monkeypatch.setattr(
        dry_run,
        "build_v6_pricing_input_preview",
        lambda **_kwargs: _pricing_preview(ready=False, blockers=["pricing_input_missing"]),
    )
    FakeCommercialPriceProposalService.preview = None

    result = await dry_run.build_intake_v6_priced_quote_dry_run(FakeDb(), "workspace-v6")

    assert result["pricing_status"] == dry_run.V6_PRICED_DRY_RUN_BLOCKED
    codes = {blocker["code"] for blocker in result["blockers"]}
    assert "pricing_input_missing" in codes
    assert dry_run.V6_PRICED_DRY_RUN_SOURCE_MISSING in codes


@pytest.mark.asyncio
async def test_dry_run_does_not_copy_frontend_preview_totals() -> None:
    result = await dry_run.build_intake_v6_priced_quote_dry_run(FakeDb(), "workspace-v6")

    assert result["pricing_input_trace"]["is_ready_for_quote"] is True
    assert result["commercial_totals"]["total_gross"] == 1190.0
    assert result["commercial_totals"]["total_gross"] != 999999.0


@pytest.mark.asyncio
async def test_dry_run_does_not_use_cost_plus_when_7g_blocked() -> None:
    FakeCommercialPriceProposalService.preview = _commercial_preview(subtotal=None, status="partial")

    result = await dry_run.build_intake_v6_priced_quote_dry_run(FakeDb(), "workspace-v6")

    assert result["pricing_status"] == dry_run.V6_PRICED_DRY_RUN_BLOCKED
    assert result["pricing_authority"] is None
    assert result["commercial_totals"]["total_gross"] is None
    assert result["diagnostic_cost_plus_trace"] is not None
    assert result["diagnostic_cost_plus_trace"]["total_gross"] is not None
    assert "official_v6_pricing_uses_cost_plus" not in " ".join(result.get("warnings") or [])


@pytest.mark.asyncio
async def test_dry_run_7g_official_total_differs_from_diagnostic_cost_plus() -> None:
    result = await dry_run.build_intake_v6_priced_quote_dry_run(FakeDb(), "workspace-v6")

    assert result["pricing_status"] == dry_run.V6_PRICED_DRY_RUN_READY
    assert result["commercial_totals"]["total_gross"] == 1190.0
    assert result["diagnostic_cost_plus_trace"]["total_gross"] != 1190.0


def test_dry_run_service_does_not_call_v4_draft_builder() -> None:
    path = Path(dry_run.__file__)
    source = path.read_text(encoding="utf-8")

    assert "build_v4_quote_draft_payload" not in source
    assert "intake_v4_commercial_quote_service" not in source


def test_dry_run_service_has_no_quote_snapshot_order_or_execution_imports() -> None:
    path = Path(dry_run.__file__)
    source = path.read_text(encoding="utf-8")

    forbidden = (
        "QuotesService",
        "quote_output_snapshots",
        "Order",
        "ProductAggregate",
        "ExecutionPlan",
        "offerModel",
    )
    for token in forbidden:
        assert token not in source
