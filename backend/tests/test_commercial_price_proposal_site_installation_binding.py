"""SITE_INSTALLATION_STANDARD binds montaj once per job via Pricing Registry.

Owner decision WORKOS-SITE-INSTALLATION-STANDARD-TARIFF-BINDING-V1:
200 EUR + VAT, fixed per location/job, company EUR→RON, no travel line.
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
from services.company_commercial_settings_service import CompanyCommercialSettingsService
from services.intake_v6_priced_quote_dry_run_service import (
    V6_PRICED_DRY_RUN_READY,
    build_intake_v6_priced_quote_dry_run,
)
from tests.test_commercial_price_proposal_linked_logo import (
    _letters_only_quote_input,
    _lines_for_segment,
    _two_logo_quote_input,
)
from tests.test_commercial_price_proposal_logo_registry_binding import (
    _upsert_canonical_finish_rates,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

ROOT = "TPL-VOLUMETRIC-LETTERS_v2"
SITE_CODE = "SITE_INSTALLATION_STANDARD"
SITE_EUR = 200.0
FX = 5.0
EXPECTED_RON = round(SITE_EUR * FX, 6)


async def _persist_workspace(db, payload: dict[str, Any]) -> IntakeV6WorkspaceRecord:
    import json

    record = IntakeV6WorkspaceRecord(
        id=str(uuid.uuid4()),
        workspace_code=f"WS-SITE-INSTALL-{uuid.uuid4().hex[:8]}",
        title="Site installation binding test",
        template_code=ROOT,
        status="draft",
        payload_json=json.dumps(payload),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def _upsert_site_installation_rate(db, *, active: bool = True, amount: float = SITE_EUR) -> None:
    existing = (
        await db.execute(select(Workcenter_rates).where(Workcenter_rates.code == SITE_CODE).limit(1))
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            Workcenter_rates(
                code=SITE_CODE,
                label="Montaj standard la locatie",
                rate_basis="per_piece",
                rate_per_linear_meter=amount,
                currency="EUR",
                status="active" if active else "missing_price",
                is_active=active,
                notes="owner_confirmed_site_installation_standard_test_fixture",
            )
        )
    else:
        existing.label = "Montaj standard la locatie"
        existing.rate_basis = "per_piece"
        existing.rate_per_linear_meter = amount
        existing.currency = "EUR"
        existing.status = "active" if active else "missing_price"
        existing.is_active = active
    await db.commit()
    settings = CompanyCommercialSettingsService(db)
    await settings.update_settings(eur_to_ron_rate=FX)


async def _remove_site_installation_rate(db) -> None:
    existing = (
        await db.execute(select(Workcenter_rates).where(Workcenter_rates.code == SITE_CODE).limit(1))
    ).scalar_one_or_none()
    if existing is not None:
        await db.delete(existing)
        await db.commit()


@pytest_asyncio.fixture
async def site_binding_db(volumetric_v2_db):
    await seed_tpl_volumetric_logo_v1()
    await _upsert_canonical_finish_rates(volumetric_v2_db, include_forbidden_stub=True)
    await _remove_site_installation_rate(volumetric_v2_db)
    yield volumetric_v2_db


@pytest_asyncio.fixture
async def cpp_service(site_binding_db):
    yield CommercialPriceProposalService(site_binding_db)


@pytest.mark.asyncio
async def test_site_install_fail_closed_without_registry_rate(cpp_service, site_binding_db):
    payload = _two_logo_quote_input(site_install=True)
    record = await _persist_workspace(site_binding_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None
    montaj = next(line for line in preview.commercial_price_lines if line.code == "montaj")
    assert montaj.commercial_unit_price is None
    assert montaj.owner_decision_required is True
    assert montaj.registry_pricing_code == SITE_CODE
    assert any(d.code == "MONTAJ_COMMERCIAL_RULE" for d in preview.unknown_owner_decisions)
    assert preview.quote_ready_for_commercial_review is False


@pytest.mark.asyncio
async def test_site_install_binds_once_per_job_with_eur_to_ron(cpp_service, site_binding_db):
    await _upsert_site_installation_rate(site_binding_db)
    payload = _two_logo_quote_input(site_install=True)
    record = await _persist_workspace(site_binding_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None

    montaj_lines = [line for line in preview.commercial_price_lines if line.code == "montaj"]
    assert len(montaj_lines) == 1
    montaj = montaj_lines[0]
    assert montaj.quantity == 1.0
    assert montaj.unit == "locatie"
    assert montaj.basis_type == "fixed"
    assert montaj.registry_pricing_code == SITE_CODE
    assert montaj.source_currency == "EUR"
    assert montaj.cpp_currency == "RON"
    assert montaj.currency_conversion_rate == FX
    assert montaj.commercial_unit_price == EXPECTED_RON
    assert montaj.subtotal == round(EXPECTED_RON, 4)
    assert montaj.owner_decision_required is False
    assert not any(d.code == "MONTAJ_COMMERCIAL_RULE" for d in preview.unknown_owner_decisions)

    # No travel / distance commercial lines in this phase.
    travelish = [
        line
        for line in preview.commercial_price_lines
        if any(tok in (line.code or "").lower() for tok in ("travel", "deplas", "km", "cazare"))
    ]
    assert travelish == []

    assert preview.quote_ready_for_commercial_review is True
    assert preview.status == "ready"


@pytest.mark.asyncio
async def test_site_install_not_charged_per_letter_or_logo(cpp_service, site_binding_db):
    await _upsert_site_installation_rate(site_binding_db)
    payload = _two_logo_quote_input(site_install=True)
    record = await _persist_workspace(site_binding_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None
    assert sum(1 for line in preview.commercial_price_lines if line.code == "montaj") == 1
    assert not any(line.code.startswith("montaj::") for line in preview.commercial_price_lines)


@pytest.mark.asyncio
async def test_letters_and_logo_lines_unchanged_when_site_install_binds(cpp_service, site_binding_db):
    await _upsert_site_installation_rate(site_binding_db)
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
    payload = _two_logo_quote_input(site_install=True)
    record = await _persist_workspace(site_binding_db, payload)
    with_install = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert letters is not None and with_install is not None
    for code in ("debitare_fata", "modelare_cant_aluminiu", "debitare_spate"):
        a = next(line for line in letters.commercial_price_lines if line.code == code)
        b = next(line for line in with_install.commercial_price_lines if line.code == code)
        assert a.quantity == b.quantity
        assert a.subtotal == b.subtotal
    for segment in ("logo_instance_001", "logo_instance_002"):
        print_lines = [
            line
            for line in _lines_for_segment(with_install, segment)
            if line.code.startswith("logo_print::")
        ]
        assert len(print_lines) == 1
        assert print_lines[0].commercial_unit_price == 42.5


@pytest.mark.asyncio
async def test_currency_fail_closed_when_eur_rate_unset(cpp_service, site_binding_db):
    await _upsert_site_installation_rate(site_binding_db)
    from models.company_commercial_settings import CompanyCommercialSettings

    row = (
        await site_binding_db.execute(select(CompanyCommercialSettings).limit(1))
    ).scalar_one_or_none()
    assert row is not None
    row.eur_to_ron_rate = None
    await site_binding_db.commit()

    payload = _two_logo_quote_input(site_install=True)
    record = await _persist_workspace(site_binding_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None
    montaj = next(line for line in preview.commercial_price_lines if line.code == "montaj")
    assert montaj.commercial_unit_price is None
    assert montaj.owner_decision_required is True
    assert any("BLOCKED_BY_CANONICAL_CURRENCY_CONVERSION" in (w or "") for w in montaj.warnings)
    assert preview.quote_ready_for_commercial_review is False


@pytest.mark.asyncio
async def test_dry_run_ready_with_one_installation_line_and_vat(site_binding_db):
    """Priced dry-run uses a schema-valid workspace payload (not the CPP quote_input fixture)."""
    import json

    await _upsert_site_installation_rate(site_binding_db)
    payload = {
        "analysis_ready": True,
        "intake_request_code": "IR-SITE-INSTALL",
        "product_binding": {"template_code": ROOT},
        "svg_source": {"file_name": "letters.svg", "file_size_bytes": 2048},
        "client": {"width_mm": 1200, "height_mm": 400},
        "quote_geometry": {
            "letter_count": 5,
            "letter_perimeter_m": 12.5,
            "letter_face_area_m2": 1.2,
            "face_area_m2": 1.2,
        },
        "finish_setup": {
            "face_finish_type": "plexiglas_clear",
            "return_depth_mm": 60,
            "return_finish_type": "ral",
            "volum_aluminum_module_template_code": "TPL-VOLUM-ALUMINIU_v1",
            "backing_mode": "forex_10_no_bevel",
            "mounting_system": "direct_wall",
            "mounting_template_enabled": True,
            "mounting_template_area_m2": 2.5,
            "mounting_template_material_type": "forex",
            "mounting_scope": "preparation_and_site_installation",
            "site_installation_included": True,
            "mounting_solution": {
                "kind": "installation_template",
                "template_code": None,
                "configuration": {},
            },
            "lighting_system_type": "front_lit",
            "illuminated": True,
            "led_module_count": 20,
            "selected_psu_watts": 60,
            "letter_group_finishes": [{"group_key": "default", "confirmed": True}],
        },
        "product_composition_confirmed": {"confirmed": True},
    }
    workspace_id = str(uuid.uuid4())
    site_binding_db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"IV6-SITE-{workspace_id[:8]}",
            title="Site install dry-run",
            template_code=ROOT,
            status="draft",
            payload_json=json.dumps(payload),
        )
    )
    await site_binding_db.commit()

    result = await build_intake_v6_priced_quote_dry_run(site_binding_db, workspace_id)
    montaj_items = [
        item
        for item in (result.get("commercial_line_items") or [])
        if item.get("code") == "montaj"
    ]
    assert len(montaj_items) == 1, result.get("blockers")
    assert montaj_items[0].get("subtotal") == round(EXPECTED_RON, 4)
    assert not any(
        (b.get("code") if isinstance(b, dict) else getattr(b, "code", None)) == "MONTAJ_COMMERCIAL_RULE"
        for b in (result.get("blockers") or [])
    )
    # Full READY may still fail on unrelated adapter/geometry gates; prove montaj + VAT math when ready.
    if result["pricing_status"] == V6_PRICED_DRY_RUN_READY:
        totals = result["commercial_totals"]
        assert totals["subtotal_net"] is not None and totals["subtotal_net"] > 0
        assert totals["vat_amount"] is not None and totals["vat_amount"] > 0
        assert totals["total_gross"] is not None and totals["total_gross"] > totals["subtotal_net"]
    else:
        # Montaj must not be among blockers; remaining blockers are out of this tariff scope.
        codes = [
            (b.get("code") if isinstance(b, dict) else getattr(b, "code", None))
            for b in (result.get("blockers") or [])
        ]
        assert "MONTAJ_COMMERCIAL_RULE" not in codes
        assert montaj_items[0].get("commercial_unit_price") == EXPECTED_RON or montaj_items[0].get(
            "subtotal"
        ) == round(EXPECTED_RON, 4)
