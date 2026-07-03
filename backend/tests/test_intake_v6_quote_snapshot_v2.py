from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from services import intake_v6_quote_snapshot_v2_service as snapshot_service
from services.quote_output_composition_service import QuoteOutputCompositionService


class FakeDb:
    def __init__(self) -> None:
        self.add_called = False
        self.commit_called = False
        self.refreshed = None

    def add(self, obj) -> None:
        self.add_called = True
        self.added = obj

    async def commit(self) -> None:
        self.commit_called = True

    async def refresh(self, obj) -> None:
        self.refreshed = obj


class FakeQuotesService:
    quote = None

    def __init__(self, db) -> None:
        self.db = db

    async def get_by_id(self, quote_id: int):
        if self.quote is not None:
            assert self.quote.id == quote_id
        return self.quote


def _notes(**write_overrides):
    write_trace = {
        "workspace_id": "workspace-v6",
        "workspace_code": "IV6-TEST",
        "intake_code": "IR-TEST",
        "pricing_source": "intake_v6_backend_priced_dry_run",
        "pricing_hash": "hash-123",
        "pricing_input_trace": {"is_ready_for_quote": True},
        "commercial_proposal_trace": {"status": "ready"},
        "internal_cost_trace_summary": {"estimated_cost_total": 782.38, "currency": "EUR"},
        "no_v4_v2_commercial_truth": True,
        "frontend_preview_not_used": True,
        "quote_snapshot_created": False,
        "order_created": False,
    }
    write_trace.update(write_overrides)
    return json.dumps(
        {
            "intake_v6_linkage_v1": {
                "source_module": "intake_v6",
                "source_workspace_id": "workspace-v6",
                "source_workspace_code": "IV6-TEST",
                "source_svg": "letters.svg",
                "template_code": "TPL-VOLUMETRIC-LETTERS_v2",
                "pricing_source": "intake_v6_backend_priced_dry_run",
                "intake_v6_priced_quote_write_v1": write_trace,
            }
        }
    )


def _line_items():
    return json.dumps(
        [
            {
                "name": "Debitare fata",
                "description": "Debitare fata",
                "quantity": 1.25,
                "unit": "m2",
                "unit_price": 800.0,
                "total": 1000.0,
                "pricing_source": "intake_v6_backend_priced_dry_run",
                "client_visible": True,
            }
        ]
    )


def _quote(**overrides):
    data = {
        "id": 6,
        "code": "Q-V6-IV6-TEST-1",
        "intake_code": "IV6-workspace-v6",
        "client_id": 44,
        "client_name": "Gradinita Test",
        "status": "priced",
        "line_items": _line_items(),
        "subtotal": 1000.0,
        "discount": 0.0,
        "discount_pct": 0.0,
        "total_before_vat": 1000.0,
        "vat": 190.0,
        "grand_total": 1190.0,
        "margin_pct": 0.0,
        "valid_until": "2026-08-01",
        "created_at": None,
        "notes": _notes(),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


async def _fake_persist(
    db,
    *,
    quote_obj,
    snapshot_payload,
    commercial,
    client_output,
    created_by,
    content_hash,
    quote_snapshot_v2,
):
    db.add_called = True
    db.quote_snapshot_v2 = quote_snapshot_v2
    return SimpleNamespace(id=101, snapshot_code="QS2-2026-0001")


@pytest.fixture(autouse=True)
def patch_snapshot_dependencies(monkeypatch):
    async def no_snapshots(_db, _quote_id):
        return 0

    async def no_orders(_db, _quote_id):
        return 0

    monkeypatch.setattr(snapshot_service, "QuotesService", FakeQuotesService)
    monkeypatch.setattr(snapshot_service, "_snapshot_count", no_snapshots)
    monkeypatch.setattr(snapshot_service, "_order_count", no_orders)
    monkeypatch.setattr(snapshot_service, "_persist_snapshot", _fake_persist)
    FakeQuotesService.quote = _quote()


async def _create(**kwargs):
    return await snapshot_service.create_v6_quote_snapshot_v2(
        FakeDb(),
        quote_id=kwargs.pop("quote_id", 6),
        workspace_id=kwargs.pop("workspace_id", "workspace-v6"),
        operator_confirmation=kwargs.pop("operator_confirmation", True),
        expected_grand_total=kwargs.pop("expected_grand_total", 1190.0),
        expected_pricing_hash=kwargs.pop("expected_pricing_hash", None),
        created_by="test@example.com",
    )


def _codes(result: dict) -> set[str]:
    return {str(blocker.get("code")) for blocker in result.get("blockers", [])}


@pytest.mark.asyncio
async def test_successful_snapshot_creation_freezes_persisted_quote_totals_and_line_items() -> None:
    result = await _create(expected_pricing_hash="hash-123")

    assert result["status"] == snapshot_service.V6_QUOTE_SNAPSHOT_V2_CREATED
    assert result["snapshot_version"] == "QUOTE_SNAPSHOT_V2"
    assert result["commercial"]["grand_total"] == 1190.0
    assert result["commercial"]["total_before_vat"] == 1000.0
    assert result["line_items"][0]["total"] == 1000.0
    assert result["line_items"][0]["pricing_source"] == "intake_v6_backend_priced_dry_run"
    assert result["v6_linkage"]["template_code"] == "TPL-VOLUMETRIC-LETTERS_v2"
    assert result["v6_linkage"]["no_v4_v2_commercial_truth"] is True
    assert result["v6_linkage"]["frontend_preview_not_used"] is True


@pytest.mark.asyncio
async def test_snapshot_response_separates_client_output_from_internal_trace_and_keeps_order_locked() -> None:
    result = await _create()

    assert result["client_output"]["total_gross"] == 1190.0
    assert "internal_cost_trace_summary" not in result["client_output"]
    assert result["internal_trace"]["internal_cost_trace_summary"]["estimated_cost_total"] == 782.38
    assert result["can_accept_quote"] is True
    assert result["can_create_order"] is False
    assert result["order_snapshot_required"] is True
    assert result["order_created"] is False
    assert result["product_aggregate_created"] is False
    assert result["task_graph_created"] is False
    assert result["execution_plan_created"] is False


@pytest.mark.asyncio
async def test_zero_quote_blocks_snapshot_creation() -> None:
    FakeQuotesService.quote = _quote(grand_total=0.0)

    result = await _create(expected_grand_total=0.0)

    assert snapshot_service.V6_SNAPSHOT_INVALID_TOTALS in _codes(result)


@pytest.mark.asyncio
async def test_unpriced_quote_blocks_snapshot_creation() -> None:
    FakeQuotesService.quote = _quote(
        status="draft",
        subtotal=0.0,
        total_before_vat=0.0,
        vat=0.0,
        grand_total=0.0,
    )

    result = await _create(expected_grand_total=0.0)

    assert snapshot_service.V6_SNAPSHOT_QUOTE_NOT_PRICED in _codes(result)


@pytest.mark.asyncio
async def test_backend_priced_draft_can_create_snapshot_for_recovery_before_accept() -> None:
    FakeQuotesService.quote = _quote(status="draft")

    result = await _create()

    assert result["status"] == snapshot_service.V6_QUOTE_SNAPSHOT_V2_CREATED
    assert result["snapshot_id"] == 101


@pytest.mark.asyncio
async def test_quote_without_v6_linkage_blocks_snapshot_creation() -> None:
    FakeQuotesService.quote = _quote(intake_code="IV4-workspace-v6", notes=json.dumps({}))

    result = await _create()

    assert snapshot_service.V6_SNAPSHOT_NOT_V6_QUOTE in _codes(result)


@pytest.mark.asyncio
async def test_workspace_mismatch_blocks_snapshot_creation() -> None:
    FakeQuotesService.quote = _quote(intake_code="IV6-other", notes=_notes())

    result = await _create(workspace_id="other")

    assert snapshot_service.V6_SNAPSHOT_WORKSPACE_MISMATCH in _codes(result)


@pytest.mark.asyncio
async def test_missing_or_invalid_line_items_block_snapshot_creation() -> None:
    FakeQuotesService.quote = _quote(line_items=json.dumps([]))

    missing_result = await _create()

    assert snapshot_service.V6_SNAPSHOT_LINE_ITEMS_MISSING in _codes(missing_result)

    FakeQuotesService.quote = _quote(line_items=json.dumps([{"name": "zero", "total": 0}]))
    invalid_result = await _create()

    assert snapshot_service.V6_SNAPSHOT_LINE_ITEMS_INVALID in _codes(invalid_result)


@pytest.mark.asyncio
async def test_missing_write_provenance_blocks_snapshot_creation() -> None:
    FakeQuotesService.quote = _quote(
        notes=json.dumps(
            {
                "intake_v6_linkage_v1": {
                    "source_module": "intake_v6",
                    "source_workspace_id": "workspace-v6",
                    "pricing_source": "intake_v6_backend_priced_dry_run",
                }
            }
        )
    )

    result = await _create()

    assert snapshot_service.V6_SNAPSHOT_WRITE_PROVENANCE_MISSING in _codes(result)


@pytest.mark.asyncio
async def test_frontend_preview_and_v4_v2_provenance_block_snapshot_creation() -> None:
    FakeQuotesService.quote = _quote(notes=_notes(frontend_preview_not_used=False))

    frontend_result = await _create()

    assert snapshot_service.V6_SNAPSHOT_FRONTEND_PREVIEW_FORBIDDEN in _codes(frontend_result)

    FakeQuotesService.quote = _quote(notes=_notes(no_v4_v2_commercial_truth=False))
    v4_result = await _create()

    assert snapshot_service.V6_SNAPSHOT_V2_V4_SOURCE_FORBIDDEN in _codes(v4_result)


@pytest.mark.asyncio
async def test_existing_snapshot_or_linked_order_blocks_snapshot_creation(monkeypatch) -> None:
    async def has_snapshot(_db, _quote_id):
        return 1

    monkeypatch.setattr(snapshot_service, "_snapshot_count", has_snapshot)
    snapshot_result = await _create()
    assert snapshot_service.V6_SNAPSHOT_ALREADY_EXISTS in _codes(snapshot_result)

    async def no_snapshots(_db, _quote_id):
        return 0

    async def has_order(_db, _quote_id):
        return 1

    monkeypatch.setattr(snapshot_service, "_snapshot_count", no_snapshots)
    monkeypatch.setattr(snapshot_service, "_order_count", has_order)
    order_result = await _create()
    assert snapshot_service.V6_SNAPSHOT_ORDER_EXISTS in _codes(order_result)


@pytest.mark.asyncio
async def test_terminal_quote_missing_confirmation_expected_total_hash_and_invalid_notes_block() -> None:
    FakeQuotesService.quote = _quote(status="accepted")
    accepted_result = await _create()
    assert snapshot_service.V6_SNAPSHOT_QUOTE_TERMINAL in _codes(accepted_result)

    FakeQuotesService.quote = _quote()
    confirmation_result = await _create(operator_confirmation=False)
    assert snapshot_service.V6_SNAPSHOT_OPERATOR_CONFIRMATION_REQUIRED in _codes(confirmation_result)

    total_result = await _create(expected_grand_total=1.0)
    assert snapshot_service.V6_SNAPSHOT_EXPECTED_TOTAL_MISMATCH in _codes(total_result)

    hash_result = await _create(expected_pricing_hash="wrong")
    assert snapshot_service.V6_SNAPSHOT_EXPECTED_HASH_MISMATCH in _codes(hash_result)

    FakeQuotesService.quote = _quote(notes="not-json")
    notes_result = await _create()
    assert snapshot_service.V6_SNAPSHOT_NOTES_INVALID in _codes(notes_result)


@pytest.mark.asyncio
async def test_snapshot_creation_does_not_change_quote_totals_or_create_order() -> None:
    original = FakeQuotesService.quote

    result = await _create()

    assert result["status"] == snapshot_service.V6_QUOTE_SNAPSHOT_V2_CREATED
    assert original.subtotal == 1000.0
    assert original.total_before_vat == 1000.0
    assert original.vat == 190.0
    assert original.grand_total == 1190.0
    assert result["order_created"] is False


@pytest.mark.asyncio
async def test_output_composition_prefers_existing_quote_snapshot_v2(monkeypatch) -> None:
    snapshot_payload = {
        "client_output": {"offer_lines": [{"name": "Snapshot line", "total": 1190.0}]},
        "commercial": {"subtotal": 1000.0, "vat": 190.0, "grand_total": 1190.0, "currency": "RON"},
        "v6_linkage": {"template_code": "TPL-VOLUMETRIC-LETTERS_v2"},
    }
    snapshot = SimpleNamespace(
        id=101,
        snapshot_code="QS2-2026-0001",
        variables_used_json=json.dumps(snapshot_payload),
    )
    service = QuoteOutputCompositionService(SimpleNamespace())

    async def latest_snapshot(_quote_id):
        return snapshot

    monkeypatch.setattr(service, "_latest_quote_snapshot_v2", latest_snapshot)

    class FakeResult:
        def scalar_one_or_none(self):
            return _quote()

    async def fake_execute(_query):
        return FakeResult()

    service.db.execute = fake_execute

    result = await service.compose_preview(6)
    dto = result.to_dict()

    assert dto["composition_type"] == "quote_snapshot_v2_preview"
    assert dto["commercial_summary"]["snapshot_id"] == 101
    assert dto["sections"][0]["name"] == "Snapshot line"
    assert dto["trace"]["snapshot_v2_used"] is True


@pytest.mark.asyncio
async def test_output_composition_reports_snapshot_missing_without_snapshot(monkeypatch) -> None:
    service = QuoteOutputCompositionService(SimpleNamespace())

    async def no_snapshot(_quote_id):
        return None

    monkeypatch.setattr(service, "_latest_quote_snapshot_v2", no_snapshot)

    class FakeResult:
        def scalar_one_or_none(self):
            return _quote()

    async def fake_execute(_query):
        return FakeResult()

    service.db.execute = fake_execute

    result = await service.compose_preview(6)
    dto = result.to_dict()

    assert "snapshot_missing" in dto["warnings"]
    assert dto["commercial_summary"]["total"] == 1190.0


def test_snapshot_service_does_not_call_v4_frontend_order_or_execution_paths() -> None:
    source = Path(snapshot_service.__file__).read_text(encoding="utf-8")

    forbidden = (
        "build_v4_quote_draft_payload",
        "intake_v4_commercial_quote_service",
        "QuoteOrchestrator",
        "offerModel",
        "create_order(",
        "ProductAggregate",
        "TaskGraph",
        "ExecutionPlan",
        "Employee Mobile",
        "writes_quote_totals",
        "update_quote",
    )
    for token in forbidden:
        assert token not in source