"""ACTIVE_TEMPLATE_CRITICAL_MATERIAL_FILL_V1 — PSU selector identity, no invented price."""

from __future__ import annotations

import pytest

from models.inventory_materials import Inventory_materials
from services.material_market_price_registry_service import MaterialMarketPriceRegistryService
from services.material_variant_selector_policy import (
    MATERIAL_ROLE_VARIANT_SELECTOR,
    TEMPLATE_PSU_CODE,
    is_variant_selector,
    psu_identity_map_row,
    resolve_psu_variant_code,
    selector_variants,
)
from services.volumetric_material_rate_resolver import PSU_WATTS_TO_VARIANT_CODE

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


def test_mat_led_psu_12v_is_variant_selector_not_sku():
    assert is_variant_selector("MAT-LED-PSU-12V")
    assert TEMPLATE_PSU_CODE == "MAT-LED-PSU-12V"
    variants = selector_variants(TEMPLATE_PSU_CODE)
    assert variants == sorted(PSU_WATTS_TO_VARIANT_CODE.values())
    row = psu_identity_map_row()
    assert row["material_role"] == MATERIAL_ROLE_VARIANT_SELECTOR
    assert row["canonical_as_sku"] is False
    assert row["data_write_required"] is False


def test_psu_watt_resolution_deterministic():
    assert resolve_psu_variant_code(60) == "MAT-LED-PSU-12V-60W"
    assert resolve_psu_variant_code(100) == "MAT-LED-PSU-12V-100W"
    assert resolve_psu_variant_code(160) == "MAT-LED-PSU-12V-160W"
    assert resolve_psu_variant_code(200) == "MAT-LED-PSU-12V-200W"
    assert resolve_psu_variant_code(250) is None
    assert resolve_psu_variant_code(None) is None


@pytest.mark.asyncio
async def test_registry_excludes_psu_selector_from_critical_missing(volumetric_v2_db):
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    prices = {60: 12.0, 100: 16.0, 160: 20.0, 200: 40.0}
    volumetric_v2_db.add(
        Inventory_materials(
            code=TEMPLATE_PSU_CODE,
            name="Sursa LED 12V (selector)",
            unit="buc",
            category="iluminat_led",
            unit_cost=None,
            status="missing_price",
        )
    )
    for watts, cost in prices.items():
        code = PSU_WATTS_TO_VARIANT_CODE[watts]
        volumetric_v2_db.add(
            Inventory_materials(
                code=code,
                name=code,
                unit="buc",
                category="iluminat_led",
                unit_cost=cost,
                currency="EUR",
                vat_percent=19.0,
                valid_from=now,
                status="active",
                source_review_status="owner_confirmed",
                source_name="Owner confirmed PSU tier",
            )
        )
    await volumetric_v2_db.commit()

    out = await MaterialMarketPriceRegistryService(volumetric_v2_db).build_registry(
        include_history=False
    )
    assert TEMPLATE_PSU_CODE not in out.critical_missing

    by = {i.material_code: i for i in out.items}
    selector = by[TEMPLATE_PSU_CODE]
    assert selector.material_role == "variant_selector"
    assert selector.requires_direct_price is False
    assert selector.blocker is None
    assert selector.raw_price is None
    assert selector.canonical is True
    assert "MAT-LED-PSU-12V-100W" in selector.variant_codes
    assert selector.warning and "Selector" in selector.warning

    for watts, code in PSU_WATTS_TO_VARIANT_CODE.items():
        sku = by[code]
        assert sku.material_role == "physical_sku"
        assert sku.raw_price == prices[watts]
        assert sku.source_type == "OWNER_CONFIRMED"
        assert sku.requires_direct_price is True


def test_finish_line_critical_zero_for_psu_selector(auth_client):
    r = auth_client.get("/api/v1/product-system/reference-finish-line/critical-materials")
    assert r.status_code == 200
    body = r.json()
    assert "MAT-LED-PSU-12V" not in body["active_template_critical_codes"]
    psu = next(i for i in body["items"] if i["material_code"] == "MAT-LED-PSU-12V")
    assert psu["classification"] == "VARIANT_SELECTOR"
    assert psu["missing_price"] is False


def test_resolver_doc_forbids_generic_psu_price():
    import services.volumetric_material_rate_resolver as mod

    assert "No prices are hardcoded" in (mod.__doc__ or "")
    assert TEMPLATE_PSU_CODE in (mod.__doc__ or "")
