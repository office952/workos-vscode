"""Logo commercial lines must bind to existing Pricing Registry operation rates.

Characterization + contract for WORKOS-GRADI-CURAT-LOGO-EXISTING-TARIFF-BINDING-CORRECTION-V1.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import select

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.workcenter_rates import Workcenter_rates
from seeds.seed_tpl_volumetric_logo_v1 import seed_tpl_volumetric_logo_v1
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.company_commercial_settings_service import (
    CompanyCommercialSettingsService,
    get_eur_to_ron_rate,
)
from services.linked_logo_commercial_price_service import FORBIDDEN_LAMINATION_STUB_CODE
from tests.test_commercial_price_proposal_linked_logo import (
    _letters_only_quote_input,
    _lines_for_segment,
    _two_logo_quote_input,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

ROOT = "TPL-VOLUMETRIC-LETTERS_v2"

CANONICAL = {
    "logo_print": "LARGE_FORMAT_PRINT",
    "logo_laminate": "LAMINATION",
    "logo_application": "FACE_VINYL_APPLICATION_LABOR",
}


async def _persist_workspace(db, payload: dict[str, Any]) -> IntakeV6WorkspaceRecord:
    import json

    record = IntakeV6WorkspaceRecord(
        id=str(uuid.uuid4()),
        workspace_code=f"WS-LOGO-BIND-{uuid.uuid4().hex[:8]}",
        title="Logo registry binding test",
        template_code=ROOT,
        status="draft",
        payload_json=json.dumps(payload),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def _upsert_canonical_finish_rates(db, *, include_forbidden_stub: bool = False) -> None:
    """Seed only the three owner-confirmed finish rates (no duplicate tariffs)."""
    specs = [
        ("LARGE_FORMAT_PRINT", "Serviciu print autocolant", 8.5),
        ("LAMINATION", "Serviciu laminare print", 5.0),
        ("FACE_VINYL_APPLICATION_LABOR", "Manoperă aplicare folie fețe litere", 5.0),
    ]
    for code, label, rate in specs:
        existing = (
            await db.execute(select(Workcenter_rates).where(Workcenter_rates.code == code).limit(1))
        ).scalar_one_or_none()
        if existing is None:
            db.add(
                Workcenter_rates(
                    code=code,
                    label=label,
                    rate_basis="per_square_meter",
                    rate_per_linear_meter=rate,
                    currency="EUR",
                    status="active",
                    is_active=True,
                    notes="owner_confirmed_test_fixture",
                )
            )
        else:
            existing.label = label
            existing.rate_basis = "per_square_meter"
            existing.rate_per_linear_meter = rate
            existing.currency = "EUR"
            existing.status = "active"
            existing.is_active = True
    if include_forbidden_stub:
        stub = (
            await db.execute(
                select(Workcenter_rates).where(Workcenter_rates.code == FORBIDDEN_LAMINATION_STUB_CODE).limit(1)
            )
        ).scalar_one_or_none()
        if stub is None:
            db.add(
                Workcenter_rates(
                    code=FORBIDDEN_LAMINATION_STUB_CODE,
                    label="Forbidden lamination stub",
                    rate_basis="per_piece",
                    rate_per_linear_meter=99.0,
                    currency="EUR",
                    status="missing_price",
                    is_active=False,
                )
            )
    await db.commit()
    settings = CompanyCommercialSettingsService(db)
    await settings.update_settings(eur_to_ron_rate=5.0)


@pytest_asyncio.fixture
async def logo_binding_db(volumetric_v2_db):
    await seed_tpl_volumetric_logo_v1()
    await _upsert_canonical_finish_rates(volumetric_v2_db, include_forbidden_stub=True)
    yield volumetric_v2_db


@pytest_asyncio.fixture
async def cpp_service(logo_binding_db):
    yield CommercialPriceProposalService(logo_binding_db)


def _finish_lines(preview, segment: str, family: str):
    return [
        line
        for line in _lines_for_segment(preview, segment)
        if line.code.startswith(f"{family}::")
    ]


@pytest.mark.asyncio
async def test_logo_print_resolves_large_format_print(cpp_service, logo_binding_db):
    payload = _two_logo_quote_input()
    record = await _persist_workspace(logo_binding_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None
    for segment in ("logo_instance_001", "logo_instance_002"):
        lines = _finish_lines(preview, segment, "logo_print")
        assert len(lines) == 1
        line = lines[0]
        assert line.registry_pricing_code == "LARGE_FORMAT_PRINT"
        assert line.commercial_unit_price is not None
        assert line.subtotal is not None
        assert line.owner_decision_required is False
        assert "SVC-LAMINATION" not in (line.source or "")
        assert line.source_currency == "EUR"
        assert (line.cpp_currency or preview.currency) == "RON"


@pytest.mark.asyncio
async def test_logo_lamination_resolves_lamination_not_stub(cpp_service, logo_binding_db):
    payload = _two_logo_quote_input()
    record = await _persist_workspace(logo_binding_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None
    for segment in ("logo_instance_001", "logo_instance_002"):
        lines = _finish_lines(preview, segment, "logo_laminate")
        assert len(lines) == 1
        line = lines[0]
        assert line.registry_pricing_code == "LAMINATION"
        assert line.registry_pricing_code != FORBIDDEN_LAMINATION_STUB_CODE
        assert FORBIDDEN_LAMINATION_STUB_CODE not in (line.source or "")
        assert line.commercial_unit_price is not None


@pytest.mark.asyncio
async def test_logo_application_resolves_face_vinyl_labor(cpp_service, logo_binding_db):
    payload = _two_logo_quote_input()
    record = await _persist_workspace(logo_binding_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None
    for segment in ("logo_instance_001", "logo_instance_002"):
        lines = _finish_lines(preview, segment, "logo_application")
        assert len(lines) == 1
        assert lines[0].registry_pricing_code == "FACE_VINYL_APPLICATION_LABOR"
        assert lines[0].commercial_unit_price is not None


@pytest.mark.asyncio
async def test_quantities_per_logo_square_meters_not_letter_area(cpp_service, logo_binding_db):
    payload = _two_logo_quote_input()
    # Force distinct finish areas for quantity truth.
    finishes = payload["finish_setup"]["artwork_finishes"]
    finishes[0]["estimated_area_m2"] = 0.4002
    finishes[1]["estimated_area_m2"] = 0.4002
    record = await _persist_workspace(logo_binding_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None
    letter_face = 1.2638
    for family in ("logo_print", "logo_laminate", "logo_application"):
        for segment in ("logo_instance_001", "logo_instance_002"):
            line = _finish_lines(preview, segment, family)[0]
            assert line.unit in {"m2", "mp"}
            assert line.quantity == pytest.approx(0.4002, rel=1e-4)
            assert line.quantity != pytest.approx(letter_face, rel=1e-3)


@pytest.mark.asyncio
async def test_no_hardcoded_tariff_values_or_eic_or_hourly(cpp_service, logo_binding_db):
    payload = _two_logo_quote_input()
    record = await _persist_workspace(logo_binding_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None
    blob = preview.model_dump_json().lower()
    assert "rate_per_hour" not in blob
    assert "estimated_internal_cost" not in blob or "diagnostic" in blob
    for family in ("logo_print", "logo_laminate", "logo_application"):
        for segment in ("logo_instance_001", "logo_instance_002"):
            line = _finish_lines(preview, segment, family)[0]
            # Must come from registry mapping, not invented VOL_V2 documented constants.
            assert line.registry_pricing_code in CANONICAL.values()
            assert "owner_pending" not in (line.source or "")
            assert line.currency_conversion_source == "company_commercial_settings.eur_to_ron_rate"
        assert "pricing_registry:operation:" in (line.source or "")


@pytest.mark.asyncio
async def test_currency_conversion_uses_company_settings_rate(cpp_service, logo_binding_db):
    rate = await get_eur_to_ron_rate(logo_binding_db)
    assert rate == pytest.approx(5.0)
    payload = _two_logo_quote_input()
    payload["finish_setup"]["artwork_finishes"][0]["estimated_area_m2"] = 1.0
    payload["finish_setup"]["artwork_finishes"][1]["estimated_area_m2"] = 1.0
    # Keep only logo 1 print-like path by still having both; check unit prices.
    record = await _persist_workspace(logo_binding_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None
    print_line = _finish_lines(preview, "logo_instance_001", "logo_print")[0]
    assert print_line.commercial_unit_price == pytest.approx(8.5 * rate, rel=1e-6)
    assert print_line.currency_conversion_rate == pytest.approx(rate)
    lam = _finish_lines(preview, "logo_instance_001", "logo_laminate")[0]
    assert lam.commercial_unit_price == pytest.approx(5.0 * rate, rel=1e-6)
    app = _finish_lines(preview, "logo_instance_001", "logo_application")[0]
    assert app.commercial_unit_price == pytest.approx(5.0 * rate, rel=1e-6)


@pytest.mark.asyncio
async def test_currency_gate_fails_closed_without_canonical_rate(logo_binding_db):
    from models.company_commercial_settings import CompanyCommercialSettings
    from sqlalchemy import select

    row = (
        await logo_binding_db.execute(
            select(CompanyCommercialSettings).order_by(CompanyCommercialSettings.id.asc()).limit(1)
        )
    ).scalar_one_or_none()
    assert row is not None
    row.eur_to_ron_rate = None
    await logo_binding_db.commit()

    payload = _two_logo_quote_input()
    record = await _persist_workspace(logo_binding_db, payload)
    preview = await CommercialPriceProposalService(logo_binding_db).build_preview(
        ROOT, workspace_id=record.id, quote_input=payload
    )
    assert preview is not None
    print_line = _finish_lines(preview, "logo_instance_001", "logo_print")[0]
    assert print_line.commercial_unit_price is None
    assert print_line.subtotal is None
    assert print_line.owner_decision_required is True
    assert any("BLOCKED_BY_CANONICAL_CURRENCY_CONVERSION" in (w or "") for w in print_line.warnings)


@pytest.mark.asyncio
async def test_site_install_remains_exact_blocker(cpp_service, logo_binding_db):
    payload = _two_logo_quote_input(site_install=True)
    record = await _persist_workspace(logo_binding_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None
    montaj = next(line for line in preview.commercial_price_lines if line.code == "montaj")
    assert montaj.commercial_unit_price is None
    assert montaj.owner_decision_required is True
    assert any(d.code == "MONTAJ_COMMERCIAL_RULE" for d in preview.unknown_owner_decisions)
    assert preview.quote_ready_for_commercial_review is False
    assert preview.status in {"partial", "blocked"}
    # Print/lam/app no longer owner-pending when registry resolves
    assert not any(d.code == "LOGO_PRINT_COMMERCIAL_RULE" for d in preview.unknown_owner_decisions)
    assert not any(d.code == "LOGO_LAMINATE_COMMERCIAL_RULE" for d in preview.unknown_owner_decisions)
    assert not any(d.code == "LOGO_APPLICATION_COMMERCIAL_RULE" for d in preview.unknown_owner_decisions)


@pytest.mark.asyncio
async def test_packaging_deferred_and_sablon_not_doubled(cpp_service, logo_binding_db):
    payload = _two_logo_quote_input(site_install=True)
    record = await _persist_workspace(logo_binding_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None
    sablon = [line for line in preview.commercial_price_lines if line.code.startswith("sablon_montaj")]
    assert len(sablon) == 1
    ambalare = next(line for line in preview.commercial_price_lines if line.code == "ambalare")
    assert ambalare.owner_decision_required is True
    assert ambalare.commercial_unit_price is None


@pytest.mark.asyncio
async def test_letter_and_logo_body_lines_unchanged(cpp_service, logo_binding_db):
    letters = await cpp_service.build_preview(
        ROOT,
        quote_input={
            **_letters_only_quote_input(),
            "quote_geometry": {
                "letter_count": 19,
                "letter_perimeter_m": 21.1675,
                "letter_face_area_m2": 1.2638,
                "artwork_boxes": [],
            },
            "finish_setup": {
                **_letters_only_quote_input()["finish_setup"],
                "letter_led_module_count": 85,
                "emblem_led_module_count": 0,
                "led_module_count": 85,
                "emblem_lighting_mode": "excluded",
            },
        },
    )
    payload = _two_logo_quote_input()
    record = await _persist_workspace(logo_binding_db, payload)
    with_logos = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert letters is not None and with_logos is not None
    for code in ("debitare_fata", "modelare_cant_aluminiu", "debitare_spate"):
        a = next(line for line in letters.commercial_price_lines if line.code == code)
        b = next(line for line in with_logos.commercial_price_lines if line.code == code)
        assert a.quantity == b.quantity
        assert a.subtotal == b.subtotal
    for segment in ("logo_instance_001", "logo_instance_002"):
        face = _finish_lines(with_logos, segment, "logo_face_cnc")[0]
        assert face.commercial_unit_price == 25.0
        led = _finish_lines(with_logos, segment, "logo_led_modules")[0]
        assert led.commercial_unit_price == 5.0


@pytest.mark.asyncio
async def test_no_duplicate_finish_lines_across_two_logos(cpp_service, logo_binding_db):
    payload = _two_logo_quote_input()
    record = await _persist_workspace(logo_binding_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None
    codes = [line.code for line in preview.commercial_price_lines]
    assert len(codes) == len(set(codes))
    for family in ("logo_print", "logo_laminate", "logo_application"):
        assert sum(1 for c in codes if c.startswith(f"{family}::")) == 2
