"""Tests for read-only CommercialPriceProposal preview (Step 7G)."""

from __future__ import annotations

import ast
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy import select

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.workcenter_rates import Workcenter_rates
from schemas.commercial_price_proposal import CommercialPriceLine
from services.commercial_price_proposal_service import (
    CommercialPriceProposalService,
    scan_forbidden_hourly_usage,
)
from services.company_commercial_settings_service import CompanyCommercialSettingsService

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


@pytest_asyncio.fixture
async def cpp_service(volumetric_v2_db):
    yield CommercialPriceProposalService(volumetric_v2_db)


@pytest.fixture
def cpp_auth_client(volumetric_auth_client):
    return volumetric_auth_client


def _full_quote_input(*, mounting_system: str = "direct_wall", illuminated: bool = True) -> dict:
    return {
        "analysis_ready": True,
        "svg_source": {"file_name": "test.svg"},
        "client": {"width_mm": 1200, "height_mm": 400},
        "quote_geometry": {
            "letter_count": 5,
            "letter_perimeter_m": 12.5,
            "letter_face_area_m2": 1.2,
        },
        "finish_setup": {
            "face_finish_type": "plexiglas_clear",
            "return_depth_mm": 60,
            "return_finish_type": "ral",
            "volum_aluminum_module_template_code": "TPL-VOLUM-ALUMINIU_v1",
            "backing_mode": "closed_back",
            "mounting_system": mounting_system,
            "lighting_system_type": "front_lit" if illuminated else "none",
            "illuminated": illuminated,
            "led_module_count": 24,
            "selected_psu_watts": 100,
            "required_psu_watts": 140.4,
            "mounting_template_enabled": True,
            "mounting_template_area_m2": 2.5,
            "mounting_template_material_type": "forex",
            "letter_group_finishes": [{"group_key": "default", "confirmed": True}],
        },
    }


@pytest.mark.asyncio
async def test_no_rate_per_hour_as_price_basis(cpp_service: CommercialPriceProposalService):
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    for line in preview.commercial_price_lines:
        assert "rate_per_hour" not in line.source.lower()
        assert "rate_per_hour" not in line.pricing_rule_code.lower()
        assert line.basis_type not in ("hours",)
    assert "rate_per_hour" not in preview.model_dump_json()


@pytest.mark.asyncio
async def test_estimated_minutes_not_commercial_price(cpp_service: CommercialPriceProposalService):
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    blob = preview.model_dump_json()
    assert "estimated_minutes" not in blob
    for line in preview.commercial_price_lines:
        assert "estimated_minutes" not in line.source
        assert line.unit not in ("min", "minute", "minutes", "ore")


@pytest.mark.asyncio
async def test_missing_workcenter_rates_does_not_block(cpp_service: CommercialPriceProposalService):
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    blocker_codes = {b.code for b in preview.commercial_blockers}
    assert "MISSING_WORKCENTER_RATES" not in blocker_codes
    assert "WORKCENTER_RATES_MISSING" not in blocker_codes
    blob = preview.model_dump_json().lower()
    assert "workcenter_rates" not in blob or "workcenter_rates missing" not in blob


@pytest.mark.asyncio
async def test_missing_execution_actuals_does_not_block(cpp_service: CommercialPriceProposalService):
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    blob = preview.model_dump_json().lower()
    assert "executionactuals" not in blob
    assert "EXECUTION_ACTUALS" not in {b.code for b in preview.commercial_blockers}


@pytest.mark.asyncio
async def test_volumetric_lines_use_product_bases_not_hourly(cpp_service: CommercialPriceProposalService):
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    allowed = {"m2", "ml", "piece", "letter", "set", "fixed", "minimum", "complexity", "unknown"}
    for line in preview.commercial_price_lines:
        assert line.basis_type in allowed
        assert line.basis_type not in ("hours", "hour", "minute")
    codes = {line.code for line in preview.commercial_price_lines}
    assert "debitare_fata" in codes
    assert "modelare_cant_aluminiu" in codes
    assert "sistem_led_module" in codes


@pytest.mark.asyncio
async def test_missing_commercial_rule_produces_commercial_rule_missing(cpp_service: CommercialPriceProposalService):
    from data.commercial_rules_volumetric_v2 import RULES_BY_TEMPLATE

    original = RULES_BY_TEMPLATE[TEMPLATE]
    RULES_BY_TEMPLATE[TEMPLATE] = tuple(r for r in original if r.module_code != "debitare_fata")
    try:
        preview = await cpp_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
        assert preview is not None
        assert any(b.code == "COMMERCIAL_RULE_MISSING" for b in preview.commercial_blockers)
    finally:
        RULES_BY_TEMPLATE[TEMPLATE] = original


@pytest.mark.asyncio
async def test_missing_critical_geometry_blocks(cpp_service: CommercialPriceProposalService):
    bad_input = _full_quote_input()
    bad_input["quote_geometry"] = {"letter_count": 5}
    bad_input.pop("client", None)
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=bad_input)
    assert preview is not None
    assert preview.status == "blocked"
    assert any(b.code == "CRITICAL_GEOMETRY_MISSING" for b in preview.commercial_blockers)
    assert preview.quote_ready_for_commercial_review is False


@pytest.mark.asyncio
async def test_provenance_present(cpp_service: CommercialPriceProposalService):
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    keys = {p.key for p in preview.provenance}
    assert "product_definition" in keys
    assert "commercial_rules" in keys
    assert "active_modules" in keys


@pytest.mark.asyncio
async def test_direct_wall_structura_suport_inactive(cpp_service: CommercialPriceProposalService):
    preview = await cpp_service.build_preview(
        TEMPLATE,
        quote_input=_full_quote_input(mounting_system="direct_wall"),
    )
    assert preview is not None
    active = set(preview.input_summary.get("active_modules", []))
    assert "structura_suport" not in active
    assert any("structura_suport correctly inactive" in w for w in preview.warnings)


@pytest.mark.asyncio
async def test_sablon_hartie_documented_price(cpp_service: CommercialPriceProposalService):
    payload = _full_quote_input()
    payload["finish_setup"]["mounting_template_material_type"] = "paper"
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=payload)
    assert preview is not None
    hartie = next((line for line in preview.commercial_price_lines if line.code == "sablon_montaj_hartie"), None)
    assert hartie is not None
    assert hartie.commercial_unit_price == 5.0
    assert hartie.basis_type == "m2"
    assert hartie.subtotal == pytest.approx(12.5)


@pytest.mark.asyncio
async def test_debitare_spate_dev_bridge_m2_price(cpp_service: CommercialPriceProposalService):
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    back = next(line for line in preview.commercial_price_lines if line.code == "debitare_spate")
    assert back.basis_type == "m2"
    assert back.owner_decision_required is False
    assert back.commercial_unit_price == 20.0
    assert back.subtotal == pytest.approx(24.0)


@pytest.mark.asyncio
async def test_volumetric_v2_dev_bridge_reaches_ready_status(cpp_service: CommercialPriceProposalService):
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    assert preview.status == "ready"
    assert preview.quote_ready_for_commercial_review is True
    assert preview.subtotal_commercial is not None
    assert preview.subtotal_commercial > 0
    assert not any(
        d.code in {"DEBITARE_SPATE_BASIS_ML_VS_M2", "SABLON_FOREX_COMMERCIAL_PRICE"}
        for d in preview.unknown_owner_decisions
    )


@pytest.mark.asyncio
async def test_no_db_writes(cpp_service: CommercialPriceProposalService, volumetric_v2_db):
    session = volumetric_v2_db
    add_mock = MagicMock(wraps=session.add)
    commit_mock = AsyncMock(wraps=session.commit)
    session.add = add_mock
    session.commit = commit_mock

    preview = await cpp_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    add_mock.assert_not_called()
    commit_mock.assert_not_called()


def _forbidden_service_imports() -> set[str]:
    path = Path(__file__).resolve().parents[1] / "services" / "commercial_price_proposal_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
    return modules


def test_service_does_not_import_cost_engine():
    modules = _forbidden_service_imports()
    assert not any("cost_engine" in mod for mod in modules)


def test_service_does_not_import_quote_orchestrator():
    modules = _forbidden_service_imports()
    assert not any("quote_orchestrator" in mod for mod in modules)


def test_forbidden_hourly_usage_produces_blocked():
    lines = [
        CommercialPriceLine(
            code="bad_line",
            label="Bad",
            basis_type="fixed",
            quantity=1,
            unit="set",
            pricing_rule_code="BAD",
            source="legacy workcenter_rate fallback",
            owner_decision_required=False,
        )
    ]
    hits = scan_forbidden_hourly_usage(lines)
    assert hits
    assert any("workcenter_rate" in hit for hit in hits)


@pytest.mark.asyncio
async def test_forbidden_hourly_blocks_preview_status(cpp_service: CommercialPriceProposalService, monkeypatch):
    from services import commercial_price_proposal_service as mod

    original_scan = mod.scan_forbidden_hourly_usage

    def _force_hourly(lines):
        base = original_scan(lines)
        return base + ["debitare_fata:rate_per_hour"]

    monkeypatch.setattr(mod, "scan_forbidden_hourly_usage", _force_hourly)
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    assert preview.status == "blocked"
    assert preview.quote_ready_for_commercial_review is False
    assert preview.forbidden_hourly_usage_detected


def test_post_endpoint_returns_preview(cpp_auth_client):
    response = cpp_auth_client.post(
        f"/api/v1/product-system/commercial-price-preview/{TEMPLATE}",
        json={"quote_input": _full_quote_input(), "currency": "RON"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["template_code"] == TEMPLATE
    assert body["source"] == "commercial_price_proposal"
    assert isinstance(body["commercial_price_lines"], list)


async def _upsert_operation_rate(
    db,
    *,
    code: str,
    amount: float,
    currency: str = "EUR",
    fx_rate: float | None = None,
) -> None:
    existing = (
        await db.execute(select(Workcenter_rates).where(Workcenter_rates.code == code).limit(1))
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            Workcenter_rates(
                code=code,
                label=code,
                rate_basis="per_linear_meter",
                rate_per_linear_meter=amount,
                currency=currency,
                status="active",
                is_active=True,
                notes="F7E test fixture — owner-confirmed registry rate row.",
            )
        )
    else:
        existing.rate_per_linear_meter = amount
        existing.currency = currency
        existing.status = "active"
        existing.is_active = True
    await db.commit()
    if fx_rate is not None:
        await CompanyCommercialSettingsService(db).update_settings(eur_to_ron_rate=fx_rate)


# --- F7E Agent B — commercial rule scenario matrix (Lead GO 2026-08-03) ---


@pytest.mark.asyncio
async def test_face_finish_none_does_not_charge_flat_finish_line(
    cpp_service: CommercialPriceProposalService,
):
    """AGENT-B-F001: 'Fara finisaj' must not charge the flat finisaje_colantare_vopsire line."""
    payload = _full_quote_input()
    payload["finish_setup"]["face_finish_type"] = "none"
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=payload)
    assert preview is not None
    codes = {line.code for line in preview.commercial_price_lines}
    assert "finisaje_colantare_vopsire" not in codes
    assert not any(b.code == "COMMERCIAL_RULE_MISSING" for b in preview.commercial_blockers)
    assert preview.status == "ready"
    assert preview.quote_ready_for_commercial_review is True


@pytest.mark.asyncio
async def test_face_finish_unpriced_commercial_token_fails_closed(
    cpp_service: CommercialPriceProposalService,
):
    """Selection-granularity fail-closed: print_laminate has no CPP rule -> COMMERCIAL_RULE_MISSING,
    never a silent fall-back to the flat 35 RON/m2 line (no OWNER_RULE leftover)."""
    payload = _full_quote_input()
    payload["finish_setup"]["face_finish_type"] = "print_laminate"
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=payload)
    assert preview is not None
    codes = {line.code for line in preview.commercial_price_lines}
    assert "finisaje_colantare_vopsire" not in codes
    assert any(
        b.code == "COMMERCIAL_RULE_MISSING" and "print_laminate" in b.message
        for b in preview.commercial_blockers
    )
    assert preview.status == "blocked"
    assert preview.quote_ready_for_commercial_review is False


@pytest.mark.asyncio
async def test_stock_cant_colors_zero_delta_preserved(cpp_service: CommercialPriceProposalService):
    """Stock cant colors (white/black/gold/standard aluminum) stay zero-delta by design —
    no finisaje_cant_* line should ever fire for them (regression guard)."""
    for token in ("white_aluminum", "black_aluminum", "gold_aluminum", "standard_aluminum"):
        payload = _full_quote_input()
        payload["finish_setup"]["return_finish_type"] = token
        preview = await cpp_service.build_preview(TEMPLATE, quote_input=payload)
        assert preview is not None
        codes = {line.code for line in preview.commercial_price_lines}
        assert not any(code.startswith("finisaje_cant_") for code in codes), token
        assert any(line.code == "modelare_cant_aluminiu" for line in preview.commercial_price_lines)


@pytest.mark.asyncio
async def test_cant_oracal_wrap_material_and_labor_pricing(
    cpp_service: CommercialPriceProposalService, volumetric_v2_db
):
    """Oracal cant wrap: material MAT-ORACAL-651 (9.0 EUR/m2, developed wrap area) + labor
    RETURN_CANT_VINYL_APPLICATION_LABOR (registry rate, EUR->RON)."""
    await _upsert_operation_rate(
        volumetric_v2_db,
        code="RETURN_CANT_VINYL_APPLICATION_LABOR",
        amount=1.0,
        currency="EUR",
        fx_rate=5.0,
    )
    payload = _full_quote_input()
    payload["finish_setup"]["return_finish_type"] = "oracal_wrapped"
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=payload)
    assert preview is not None

    material = next(
        line for line in preview.commercial_price_lines if line.code == "finisaje_cant_oracal_material"
    )
    assert material.owner_decision_required is False
    assert material.commercial_unit_price == 9.0
    assert material.quantity == pytest.approx(0.75)  # 12.5 ml x 60mm depth
    assert material.subtotal == pytest.approx(6.75)

    labor = next(
        line for line in preview.commercial_price_lines if line.code == "finisaje_cant_oracal_labor"
    )
    assert labor.owner_decision_required is False
    assert labor.quantity == pytest.approx(12.5)
    assert labor.commercial_unit_price == pytest.approx(5.0)  # 1 EUR/ml x FX 5.0
    assert labor.subtotal == pytest.approx(62.5)
    assert preview.status == "ready"


@pytest.mark.asyncio
async def test_cant_oracal_wrap_641_series_resolves_lower_material_rate(
    cpp_service: CommercialPriceProposalService,
):
    payload = _full_quote_input()
    payload["finish_setup"]["return_finish_type"] = "oracal_641"
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=payload)
    assert preview is not None
    material = next(
        line for line in preview.commercial_price_lines if line.code == "finisaje_cant_oracal_material"
    )
    assert material.commercial_unit_price == 6.5


@pytest.mark.asyncio
async def test_cant_ral_paint_minimum_charge_applies_below_floor(
    cpp_service: CommercialPriceProposalService,
):
    """RAL cant paint under the 100 RON/color floor (labor registry rate unresolved here) —
    combined material+labor is topped up to the owner-documented minimum."""
    payload = _full_quote_input()
    payload["finish_setup"]["return_finish_type"] = "ral_paint"
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=payload)
    assert preview is not None
    material = next(
        line for line in preview.commercial_price_lines if line.code == "finisaje_cant_ral_material"
    )
    assert material.subtotal == pytest.approx(100.0)
    assert any("minimum_charge_applied=100.0RON_per_color" in w for w in material.warnings)


@pytest.mark.asyncio
async def test_cant_ral_paint_pricing_above_minimum_floor(
    cpp_service: CommercialPriceProposalService, volumetric_v2_db
):
    """Large enough RAL cant job clears the 100 RON floor on its own — no top-up applied."""
    await _upsert_operation_rate(
        volumetric_v2_db,
        code="RETURN_CANT_RAL_PAINT_LABOR",
        amount=1.0,
        currency="EUR",
        fx_rate=5.0,
    )
    payload = _full_quote_input()
    payload["finish_setup"]["return_finish_type"] = "ral_paint"
    payload["quote_geometry"]["letter_perimeter_m"] = 80.0
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=payload)
    assert preview is not None
    material = next(
        line for line in preview.commercial_price_lines if line.code == "finisaje_cant_ral_material"
    )
    labor = next(
        line for line in preview.commercial_price_lines if line.code == "finisaje_cant_ral_labor"
    )
    assert material.commercial_unit_price == pytest.approx(2.5)  # 60mm tier
    assert material.subtotal == pytest.approx(200.0)  # 80ml x 2.5 EUR/ml, no floor top-up
    assert labor.commercial_unit_price == pytest.approx(5.0)  # 1 EUR/ml x FX 5.0
    assert labor.subtotal == pytest.approx(400.0)
    assert not any("minimum_charge_applied" in w for w in material.warnings)
    assert preview.status == "ready"


@pytest.mark.asyncio
async def test_face_oracal_641_651_8500_pricing_no_color_tier(
    cpp_service: CommercialPriceProposalService, volumetric_v2_db
):
    """Face Oracal 641/651/8500 (legacy CPP only, F7E Owner GO): material by series,
    labor via FACE_VINYL_APPLICATION_LABOR. Same series stays one line regardless of color code."""
    await _upsert_operation_rate(
        volumetric_v2_db,
        code="FACE_VINYL_APPLICATION_LABOR",
        amount=5.0,
        currency="EUR",
        fx_rate=5.0,
    )
    expected_material_eur = {"oracal_641": 6.5, "oracal_651": 9.0, "oracal_8500": 20.0}
    for face_token, expected_price in expected_material_eur.items():
        payload = _full_quote_input()
        payload["finish_setup"]["face_finish_type"] = face_token
        preview = await cpp_service.build_preview(TEMPLATE, quote_input=payload)
        assert preview is not None
        codes = {line.code for line in preview.commercial_price_lines}
        assert "finisaje_colantare_vopsire" not in codes

        material = next(
            line
            for line in preview.commercial_price_lines
            if line.code == f"finisaje_{face_token}_material"
        )
        assert material.commercial_unit_price == expected_price
        assert material.subtotal == pytest.approx(expected_price * 1.2)  # letter_face_area_m2

        labor = next(
            line for line in preview.commercial_price_lines if line.code == f"finisaje_{face_token}_labor"
        )
        assert labor.commercial_unit_price == pytest.approx(25.0)  # 5 EUR/m2 x FX 5.0
        assert labor.subtotal == pytest.approx(30.0)
        assert preview.status == "ready"

    # No color-tier differentiation is authorized: an arbitrary color code on the same series
    # must not change the resolved material rate (documented, not invented).
    payload_color_a = _full_quote_input()
    payload_color_a["finish_setup"]["face_finish_type"] = "oracal_651"
    payload_color_a["finish_setup"]["face_oracal_code"] = "021"
    payload_color_b = _full_quote_input()
    payload_color_b["finish_setup"]["face_finish_type"] = "oracal_651"
    payload_color_b["finish_setup"]["face_oracal_code"] = "032"
    preview_a = await cpp_service.build_preview(TEMPLATE, quote_input=payload_color_a)
    preview_b = await cpp_service.build_preview(TEMPLATE, quote_input=payload_color_b)
    material_a = next(
        line for line in preview_a.commercial_price_lines if line.code == "finisaje_oracal_651_material"
    )
    material_b = next(
        line for line in preview_b.commercial_price_lines if line.code == "finisaje_oracal_651_material"
    )
    assert material_a.commercial_unit_price == material_b.commercial_unit_price == 9.0


@pytest.mark.asyncio
async def test_sablon_forex_preserves_plus_10_ron_delta_vs_paper(
    cpp_service: CommercialPriceProposalService,
):
    """Regression guard for the proven paper<->Forex differential-pricing control
    (AGENT-B-F009, +10.00 RON/m2 delta) — must not shift while G1 branches are added."""
    paper_payload = _full_quote_input()
    paper_payload["finish_setup"]["mounting_template_material_type"] = "paper"
    forex_payload = _full_quote_input()
    forex_payload["finish_setup"]["mounting_template_material_type"] = "forex"

    paper_preview = await cpp_service.build_preview(TEMPLATE, quote_input=paper_payload)
    forex_preview = await cpp_service.build_preview(TEMPLATE, quote_input=forex_payload)
    assert paper_preview is not None and forex_preview is not None

    hartie = next(
        line for line in paper_preview.commercial_price_lines if line.code == "sablon_montaj_hartie"
    )
    forex = next(
        line for line in forex_preview.commercial_price_lines if line.code == "sablon_montaj_forex"
    )
    assert forex.commercial_unit_price - hartie.commercial_unit_price == pytest.approx(10.0)


@pytest.mark.asyncio
async def test_workspace_id_payload(volumetric_v2_db, cpp_service: CommercialPriceProposalService):
    import json

    workspace_id = str(uuid.uuid4())
    record = IntakeV6WorkspaceRecord(
        id=workspace_id,
        workspace_code=f"WS-CPP-{workspace_id[:8]}",
        title="CPP test workspace",
        template_code=TEMPLATE,
        payload_json=json.dumps(_full_quote_input()),
        status="draft",
    )
    volumetric_v2_db.add(record)
    await volumetric_v2_db.commit()

    preview = await cpp_service.build_preview(TEMPLATE, workspace_id=workspace_id)
    assert preview is not None
    assert preview.source == "commercial_price_proposal"
    assert preview.input_summary.get("workspace_id") == workspace_id
