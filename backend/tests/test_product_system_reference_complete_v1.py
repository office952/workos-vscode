"""PRODUCT_SYSTEM_REFERENCE_COMPLETE — closure contract tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from data.product_system_reference_complete_v1 import (
    DOCUMENTATION_HANDOFF_DOCS,
    FREEZE_GOVERNANCE_CONTRACT,
    JUST_IN_TIME_CATALOG_RULE,
    OPERATIONAL_PROCESS_CONTRACT,
    REFERENCE_COMPLETE_NAME,
)
from models.inventory_materials import Inventory_materials
from services.material_variant_selector_policy import TEMPLATE_PSU_CODE
from services.product_system_reference_complete_service import (
    ProductSystemReferenceCompleteService,
)
from services.volumetric_material_rate_resolver import PSU_WATTS_TO_VARIANT_CODE

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


def test_governance_contracts_frozen():
    assert FREEZE_GOVERNANCE_CONTRACT["status"] == "CONTRACT_FROZEN"
    assert "FREEZE ON" in FREEZE_GOVERNANCE_CONTRACT["rule"]
    assert JUST_IN_TIME_CATALOG_RULE["rule_id"] == "just_in_time_catalog_growth_v1"
    assert OPERATIONAL_PROCESS_CONTRACT["status"] == "CONTRACT_FROZEN"
    assert "CNC_mechanical" in OPERATIONAL_PROCESS_CONTRACT["required_categories"]
    assert len(DOCUMENTATION_HANDOFF_DOCS) == 25
    assert "FREEZE_AND_VERSION_GOVERNANCE" in DOCUMENTATION_HANDOFF_DOCS
    assert REFERENCE_COMPLETE_NAME == "PRODUCT_SYSTEM_REFERENCE_COMPLETE"


def test_reference_complete_endpoint_shape(auth_client):
    r = auth_client.get("/api/v1/product-system/reference-complete")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "PRODUCT_SYSTEM_REFERENCE_COMPLETE"
    assert len(body["completion_matrix"]) >= 20
    assert len(body["documentation_handoff"]) == 25
    assert body["freeze_governance_contract"]["status"] == "CONTRACT_FROZEN"
    assert body["ui_mode_distinction"]["status"] == "CONTRACT_FROZEN"
    assert body["production_cost_authority"] == "EIC_production_cost"


@pytest.mark.asyncio
async def test_reference_complete_structural_pass(volumetric_v2_db):
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
        volumetric_v2_db.add(
            Inventory_materials(
                code=PSU_WATTS_TO_VARIANT_CODE[watts],
                name=PSU_WATTS_TO_VARIANT_CODE[watts],
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

    body = await ProductSystemReferenceCompleteService(volumetric_v2_db).build()
    assert body.overall_verdict == "PASS", body.live_proof
    assert body.freeze_readiness == "READY_FOR_DOCUMENTATION_HANDOFF"
    assert body.live_proof["field_count"] == 26
    assert body.live_proof["active_template_critical_codes"] == []
    assert body.live_proof["psu_selector_ok"] is True
    assert body.live_proof["psu_raw_price"] is None
    assert TEMPLATE_PSU_CODE not in (body.live_proof.get("registry_critical_missing") or [])
    axes = {row.axis: row for row in body.completion_matrix}
    assert axes["Critical material coverage"].complete == "yes"
    assert axes["Form contract"].complete in {"yes", "accepted_limitation"}
    assert axes["Freeze governance"].actual_verdict == "CONTRACT_FROZEN"
    assert axes["Operational-process boundary"].actual_verdict == "CONTRACT_FROZEN"
