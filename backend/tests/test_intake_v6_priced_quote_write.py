from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from services import intake_v6_priced_quote_write_service as write_service


class FakeScalarResult:
    def scalar(self) -> int:
        return 0


class FakeDb:
    def __init__(self) -> None:
        self.add_called = False
        self.commit_called = False

    def add(self, _obj) -> None:
        self.add_called = True

    async def commit(self) -> None:
        self.commit_called = True

    async def execute(self, _query) -> FakeScalarResult:
        return FakeScalarResult()


class FakeQuotesService:
    quote = None
    updated_data = None

    def __init__(self, db) -> None:
        self.db = db

    async def get_by_id(self, quote_id: int):
        if self.quote is not None:
            assert self.quote.id == quote_id
        return self.quote

    async def update(self, quote_id: int, update_data: dict):
        assert self.quote is not None
        assert self.quote.id == quote_id
        self.updated_data = update_data
        for key, value in update_data.items():
            setattr(self.quote, key, value)
        self.db.commit_called = True
        return self.quote


def _quote(**overrides):
    notes = json.dumps(
        {
            "human_summary": "existing note",
            "intake_v6_linkage_v1": {
                "source_module": "intake_v6",
                "source_workspace_id": "workspace-v6",
                "source_workspace_code": "IV6-TEST",
                "pricing_source": "intake_v6_pricing_input_preview",
            },
        }
    )
    data = {
        "id": 6,
        "code": "Q-V6-IV6-TEST-1",
        "intake_code": "IV6-workspace-v6",
        "status": "draft",
        "line_items": json.dumps([{"description": "old", "unit_price": 0, "total": 0}]),
        "subtotal": 0.0,
        "discount": 0.0,
        "discount_pct": 0.0,
        "total_before_vat": 0.0,
        "vat": 0.0,
        "grand_total": 0.0,
        "margin_pct": 0.0,
        "accepted_snapshot_v2_id": None,
        "notes": notes,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _dry_run(**overrides):
    data = {
        "pricing_status": "V6_PRICED_DRY_RUN_READY",
        "workspace_id": "workspace-v6",
        "workspace_code": "IV6-TEST",
        "intake_code": "IR-TEST",
        "template_code": "TPL-VOLUMETRIC-LETTERS_v2",
        "pricing_source": "intake_v6_backend_priced_dry_run",
        "commercial_totals": {
            "subtotal_net": 1000.0,
            "vat_rate": 21.0,
            "vat_amount": 210.0,
            "total_gross": 1210.0,
            "currency": "RON",
        },
        "commercial_line_items": [
            {
                "code": "debitare_fata",
                "label": "Debitare fata",
                "module_code": "fata",
                "component_code": "face",
                "basis_type": "m2",
                "quantity": 1.25,
                "unit": "m2",
                "commercial_unit_price": 800.0,
                "subtotal": 1000.0,
                "pricing_rule_code": "CPP-FACE",
                "source": "commercial_rules_volumetric_v2",
                "owner_decision_required": False,
                "warnings": [],
            }
        ],
        "internal_cost_trace": {
            "available": True,
            "estimated_cost_total": 782.38,
            "material_cost_total": 782.38,
            "currency": "EUR",
            "contains_estimates": True,
            "contains_missing_prices": False,
        },
        "pricing_input_trace": {"is_ready_for_quote": True},
        "commercial_proposal_trace": {"status": "ready"},
        "warnings": [],
        "blockers": [],
        "can_write_quote_totals": False,
        "can_create_quote_snapshot": False,
        "dry_run_only": True,
        "persistence": {
            "creates_quote": False,
            "updates_quote": False,
            "writes_quote_totals": False,
            "creates_quote_snapshot": False,
            "creates_order": False,
        },
    }
    data.update(overrides)
    return data


@pytest.fixture(autouse=True)
def patch_write_dependencies(monkeypatch):
    async def fake_dry_run(_db, workspace_id, *, pricing_mode="dry_run"):
        assert workspace_id == "workspace-v6"
        assert pricing_mode == "write_priced_quote"
        return _dry_run()

    async def no_snapshots(_db, _quote_id):
        return 0

    async def no_orders(_db, _quote_id):
        return 0

    monkeypatch.setattr(write_service, "build_intake_v6_priced_quote_dry_run", fake_dry_run)
    monkeypatch.setattr(write_service, "QuotesService", FakeQuotesService)
    monkeypatch.setattr(write_service, "_snapshot_count", no_snapshots)
    monkeypatch.setattr(write_service, "_order_count", no_orders)
    FakeQuotesService.quote = _quote()
    FakeQuotesService.updated_data = None


async def _write(**kwargs):
    return await write_service.write_intake_v6_priced_quote_totals(
        FakeDb(),
        "workspace-v6",
        quote_id=kwargs.pop("quote_id", 6),
        expected_total_gross=kwargs.pop("expected_total_gross", 1210.0),
        operator_confirmation=kwargs.pop("operator_confirmation", True),
        expected_pricing_hash=kwargs.pop("expected_pricing_hash", None),
        operator_identifier="test@example.com",
    )


def _codes(result: dict) -> set[str]:
    return {str(blocker.get("code")) for blocker in result.get("blockers", [])}


@pytest.mark.asyncio
async def test_successful_write_updates_existing_eligible_v6_unpriced_quote_with_positive_totals() -> None:
    result = await _write()

    assert result["status"] == write_service.V6_PRICED_QUOTE_WRITTEN
    assert result["commercial_totals"]["subtotal_net"] == 1000.0
    assert result["commercial_totals"]["vat"] == 210.0
    assert result["commercial_totals"]["total_gross"] == 1210.0
    assert FakeQuotesService.quote.status == "priced"
    assert FakeQuotesService.quote.subtotal == 1000.0
    assert FakeQuotesService.quote.total_before_vat == 1000.0
    assert FakeQuotesService.quote.vat == 210.0
    assert FakeQuotesService.quote.grand_total == 1210.0


@pytest.mark.asyncio
async def test_successful_write_stores_line_items_from_dry_run() -> None:
    await _write()

    line_items = json.loads(FakeQuotesService.quote.line_items)
    assert line_items[0]["description"] == "Debitare fata"
    assert line_items[0]["quantity"] == 1.25
    assert line_items[0]["unit_price"] == 800.0
    assert line_items[0]["total"] == 1000.0
    assert line_items[0]["pricing_source"] == "intake_v6_backend_priced_dry_run"


@pytest.mark.asyncio
async def test_successful_write_updates_human_summary_for_priced_quote() -> None:
    await _write()

    notes = json.loads(FakeQuotesService.quote.notes)
    assert notes["human_summary"] == (
        "Oferta pretuita din Intake V6 workspace IV6-TEST. "
        "Totalurile comerciale V6 au fost scrise pe oferta ca pret comercial final. "
        "Oferta ramane in revizie interna pana la aprobarea/trimiterea catre client. "
        "Nu a fost creata comanda, executie sau miscare de stoc."
    )
    assert "QuoteWizard" not in notes["human_summary"]
    assert "preview" not in notes["human_summary"].lower()
    assert "nu au fost inca scrise" not in notes["human_summary"].lower()
    write_trace = notes["intake_v6_linkage_v1"]["intake_v6_priced_quote_write_v1"]
    assert write_trace["workspace_id"] == "workspace-v6"
    assert write_trace["intake_code"] == "IR-TEST"
    assert write_trace["expected_total_gross"] == 1210.0
    assert write_trace["written_total_gross"] == 1210.0
    assert write_trace["no_v4_v2_commercial_truth"] is True
    assert write_trace["frontend_preview_not_used"] is True
    assert write_trace["quote_snapshot_created"] is False
    assert write_trace["order_created"] is False


@pytest.mark.asyncio
async def test_successful_write_sets_snapshot_true_but_accept_false() -> None:
    result = await _write()

    assert result["can_create_quote_snapshot"] is True
    assert result["can_accept_quote"] is False
    assert result["quote_snapshot_created"] is False
    assert result["order_created"] is False


@pytest.mark.asyncio
async def test_dry_run_blocked_prevents_write(monkeypatch) -> None:
    async def blocked_dry_run(_db, _workspace_id, *, pricing_mode="dry_run"):
        return _dry_run(
            pricing_status="V6_PRICED_DRY_RUN_BLOCKED",
            blockers=[{"code": "source_missing", "message": "missing"}],
        )

    monkeypatch.setattr(write_service, "build_intake_v6_priced_quote_dry_run", blocked_dry_run)

    result = await _write()

    assert result["status"] == write_service.V6_PRICED_QUOTE_WRITE_BLOCKED
    assert write_service.V6_PRICED_QUOTE_WRITE_DRY_RUN_BLOCKED in _codes(result)
    assert FakeQuotesService.updated_data is None


@pytest.mark.asyncio
async def test_zero_dry_run_prevents_write(monkeypatch) -> None:
    async def zero_dry_run(_db, _workspace_id, *, pricing_mode="dry_run"):
        return _dry_run(commercial_totals={"subtotal_net": 0.0, "total_gross": 0.0, "currency": "RON"})

    monkeypatch.setattr(write_service, "build_intake_v6_priced_quote_dry_run", zero_dry_run)

    result = await _write(expected_total_gross=0.0)

    assert write_service.V6_PRICED_QUOTE_WRITE_ZERO_TOTAL in _codes(result)
    assert FakeQuotesService.updated_data is None


@pytest.mark.asyncio
async def test_expected_total_mismatch_prevents_write() -> None:
    result = await _write(expected_total_gross=1.0)

    assert write_service.V6_PRICED_QUOTE_WRITE_EXPECTED_TOTAL_MISMATCH in _codes(result)
    assert FakeQuotesService.updated_data is None


@pytest.mark.asyncio
async def test_non_v6_quote_prevents_write() -> None:
    FakeQuotesService.quote = _quote(intake_code="IV4-workspace-v6", notes=json.dumps({}))

    result = await _write()

    assert write_service.V6_PRICED_QUOTE_WRITE_NOT_V6_QUOTE in _codes(result)
    assert FakeQuotesService.updated_data is None


@pytest.mark.asyncio
async def test_workspace_mismatch_prevents_write() -> None:
    notes = json.dumps(
        {"intake_v6_linkage_v1": {"source_module": "intake_v6", "source_workspace_id": "other"}}
    )
    FakeQuotesService.quote = _quote(intake_code="IV6-other", notes=notes)

    result = await _write()

    assert write_service.V6_PRICED_QUOTE_WRITE_WORKSPACE_MISMATCH in _codes(result)
    assert FakeQuotesService.updated_data is None


@pytest.mark.asyncio
async def test_already_priced_quote_prevents_write() -> None:
    FakeQuotesService.quote = _quote(grand_total=1210.0, subtotal=1000.0)

    result = await _write()

    assert write_service.V6_PRICED_QUOTE_WRITE_ALREADY_PRICED in _codes(result)
    assert FakeQuotesService.updated_data is None


@pytest.mark.asyncio
async def test_snapshot_exists_prevents_write(monkeypatch) -> None:
    async def has_snapshot(_db, _quote_id):
        return 1

    monkeypatch.setattr(write_service, "_snapshot_count", has_snapshot)

    result = await _write()

    assert write_service.V6_PRICED_QUOTE_WRITE_SNAPSHOT_EXISTS in _codes(result)
    assert FakeQuotesService.updated_data is None


@pytest.mark.asyncio
async def test_accepted_quote_prevents_write() -> None:
    FakeQuotesService.quote = _quote(status="accepted")

    result = await _write()

    assert write_service.V6_PRICED_QUOTE_WRITE_ORDER_EXISTS in _codes(result)
    assert FakeQuotesService.updated_data is None


@pytest.mark.asyncio
async def test_order_exists_prevents_write(monkeypatch) -> None:
    async def has_order(_db, _quote_id):
        return 1

    monkeypatch.setattr(write_service, "_order_count", has_order)

    result = await _write()

    assert write_service.V6_PRICED_QUOTE_WRITE_ORDER_EXISTS in _codes(result)
    assert FakeQuotesService.updated_data is None


@pytest.mark.asyncio
async def test_missing_operator_confirmation_prevents_write() -> None:
    result = await _write(operator_confirmation=False)

    assert write_service.V6_PRICED_QUOTE_WRITE_OPERATOR_CONFIRMATION_REQUIRED in _codes(result)
    assert FakeQuotesService.updated_data is None


@pytest.mark.asyncio
async def test_forbidden_v4_v2_source_prevents_write(monkeypatch) -> None:
    async def v4_source(_db, _workspace_id, *, pricing_mode="dry_run"):
        return _dry_run(pricing_source="intake_v4_pricing_input_preview")

    monkeypatch.setattr(write_service, "build_intake_v6_priced_quote_dry_run", v4_source)

    result = await _write()

    assert write_service.V6_PRICED_QUOTE_WRITE_FORBIDDEN_SOURCE in _codes(result)
    assert FakeQuotesService.updated_data is None


@pytest.mark.asyncio
async def test_missing_line_items_prevents_write(monkeypatch) -> None:
    async def no_lines(_db, _workspace_id, *, pricing_mode="dry_run"):
        return _dry_run(commercial_line_items=[])

    monkeypatch.setattr(write_service, "build_intake_v6_priced_quote_dry_run", no_lines)

    result = await _write()

    assert write_service.V6_PRICED_QUOTE_WRITE_LINE_ITEMS_MISSING in _codes(result)
    assert FakeQuotesService.updated_data is None


@pytest.mark.asyncio
async def test_invalid_notes_are_preserved_safely() -> None:
    FakeQuotesService.quote = _quote(notes="not-json")

    result = await _write()

    assert result["status"] == write_service.V6_PRICED_QUOTE_WRITTEN
    notes = json.loads(FakeQuotesService.quote.notes)
    assert notes["legacy_notes_raw"] == "not-json"
    write_trace = notes["intake_v6_linkage_v1"]["intake_v6_priced_quote_write_v1"]
    assert write_trace["notes_invalid_preserved_as_legacy_raw"] is True


def test_write_service_does_not_call_v4_draft_builder() -> None:
    source = Path(write_service.__file__).read_text(encoding="utf-8")

    assert "build_v4_quote_draft_payload" not in source
    assert "intake_v4_commercial_quote_service" not in source


def test_write_service_does_not_create_quote_snapshot_order_or_execution() -> None:
    source = Path(write_service.__file__).read_text(encoding="utf-8")

    forbidden = (
        "QuoteOrchestrator",
        "ProductAggregate",
        "ExecutionPlan",
        "offerModel",
        ".create(",
        "create_snapshot(",
        "create_order",
    )
    for token in forbidden:
        assert token not in source


@pytest.mark.asyncio
async def test_write_service_does_not_create_quote_snapshot_or_order_on_success() -> None:
    db = FakeDb()

    result = await write_service.write_intake_v6_priced_quote_totals(
        db,
        "workspace-v6",
        quote_id=6,
        expected_total_gross=1210.0,
        operator_confirmation=True,
    )

    assert result["status"] == write_service.V6_PRICED_QUOTE_WRITTEN
    assert db.add_called is False
    assert result["quote_snapshot_created"] is False
    assert result["order_created"] is False