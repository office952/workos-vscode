"""Tests for preparation domain, template material costing, and blueprint ownership."""

from __future__ import annotations

import json
import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.auth import User
from models.execution_plan import ExecutionPlan
from models.inventory_materials import Inventory_materials
from seeds.material_canonical_naming import CANONICAL_MATERIAL_NAMING
from seeds.seed_volumetric_owner_confirmed_prices import OWNER_CONFIRMED_VOLUMETRIC_PRICES
from services.preparation_domain_service import derive_preparation_domain
from services.quote_input_line_gate import should_skip_quote_input_gated_line
from services.volumetric_quote_input_policy import (
    MAT_MOUNTING_TEMPLATE_FOREX,
    MAT_MOUNTING_TEMPLATE_PAPER,
    normalize_mounting_template_material_type,
    resolve_mounting_template_material_code,
)
from tests.test_employee_mobile_tasks import (
    _cleanup_overrides,
    _client_for,
    _seed_employee,
    _user,
)


def _owner_price(code: str) -> dict | None:
    for row in OWNER_CONFIRMED_VOLUMETRIC_PRICES:
        if row.get("code") == code:
            return row
    return None


class TestPreparationDomain:
    def test_cnc_task_maps_to_cnc(self) -> None:
        domain = derive_preparation_domain(
            {
                "process_id": "face_cnc_cut",
                "process_type": "cnc_routing",
                "machine_type": "CNC_ROUTER",
            }
        )
        assert domain == "cnc"

    def test_print_task_maps_to_print(self) -> None:
        domain = derive_preparation_domain(
            {
                "process_id": "face_vinyl_print",
                "process_type": "print",
                "machine_type": "PRINTER",
            }
        )
        assert domain == "print"

    def test_document_task_maps_to_instrumentation(self) -> None:
        domain = derive_preparation_domain(
            {
                "process_id": "document_handoff",
                "process_type": "document",
                "machine_type": "DESKTOP",
                "documents": [{"id": "doc-1"}],
            }
        )
        assert domain == "instrumentation"


class TestMountingTemplateMaterialType:
    def test_legacy_enabled_without_type_defaults_forex(self) -> None:
        qi = {"mounting_template_enabled": True}
        assert normalize_mounting_template_material_type(qi) == "forex"
        assert resolve_mounting_template_material_code(qi) == MAT_MOUNTING_TEMPLATE_FOREX

    def test_disabled_template_is_none(self) -> None:
        qi = {"mounting_template_enabled": False}
        assert normalize_mounting_template_material_type(qi) == "none"
        assert resolve_mounting_template_material_code(qi) is None

    def test_paper_uses_hartie_material(self) -> None:
        qi = {
            "mounting_template_enabled": True,
            "mounting_template_material_type": "paper",
            "mounting_template_area_m2": 2.5,
        }
        assert normalize_mounting_template_material_type(qi) == "paper"
        assert resolve_mounting_template_material_code(qi) == MAT_MOUNTING_TEMPLATE_PAPER

    def test_forex_gate_skips_paper_material(self) -> None:
        entry = {
            "formula_params": {
                "gate": {"mounting_template_material_type": "forex"},
            }
        }
        skip = should_skip_quote_input_gated_line(
            entry,
            {"mounting_template_material_type": "paper", "mounting_template_enabled": True},
        )
        assert skip == "gate:mounting_template_material_type"

    def test_paper_gate_skips_forex_material(self) -> None:
        entry = {
            "formula_params": {
                "gate": {"mounting_template_material_type": "paper"},
            }
        }
        skip = should_skip_quote_input_gated_line(
            entry,
            {"mounting_template_enabled": True},
        )
        assert skip == "gate:mounting_template_material_type"


class TestPaperTemplateRegistry:
    def test_hartie_owner_confirmed_price(self) -> None:
        row = _owner_price("MAT-SABLON-HARTIE")
        assert row is not None
        assert row["unit_cost"] == 5.0
        assert row["currency"] == "EUR"

    def test_hartie_canonical_naming(self) -> None:
        meta = CANONICAL_MATERIAL_NAMING["MAT-SABLON-HARTIE"]
        assert meta["canonical_name"] == "Șablon hârtie"

    def test_forex_not_duplicated(self) -> None:
        codes = [row["code"] for row in OWNER_CONFIRMED_VOLUMETRIC_PRICES]
        assert codes.count("MAT-SABLON-MONTAJ") == 1
        montaj = _owner_price("MAT-SABLON-MONTAJ")
        assert montaj is not None
        assert montaj["unit_cost"] == 6.0


@pytest.fixture
def blueprint_prepared_by_fixture(db_fixture, db_session):
    order_id = 7100 + int(uuid.uuid4().hex[:4], 16) % 1000
    preparer_id = f"prep-{uuid.uuid4().hex[:8]}"

    async def _setup():
        worker = await _seed_employee(db_session, user_id=None, name="CNC Worker")
        db_session.add(
            User(
                id=preparer_id,
                email=f"{preparer_id}@workos.test",
                name="Responsabil Instrumentare",
                role="operator",
            )
        )
        db_session.add(
            ExecutionPlan(
                order_id=order_id,
                order_code=f"ORD-PREP-{order_id}",
                snapshot_version=1,
                prepared_by_user_id=preparer_id,
                tasks_json=json.dumps(
                    [
                        {
                            "task_id": "T-CNC",
                            "name": "CNC față",
                            "process_id": "face_cnc_cut",
                            "process_type": "cnc_routing",
                            "machine_type": "CNC_ROUTER",
                            "estimated_time_minutes": 30,
                            "assigned_employee_id": worker.id,
                        },
                        {
                            "task_id": "T-DOC",
                            "name": "Documente atelier",
                            "process_id": "document_handoff",
                            "process_type": "document",
                            "machine_type": "DESKTOP",
                            "estimated_time_minutes": 10,
                            "documents": [{"id": "doc-1", "name": "Schiță.svg"}],
                        },
                        {
                            "task_id": "T-PRINT",
                            "name": "Print vinyl",
                            "process_id": "face_vinyl_print",
                            "process_type": "print",
                            "machine_type": "PRINTER",
                            "estimated_time_minutes": 20,
                        },
                    ]
                ),
                total_estimated_time_minutes=60,
            )
        )
        db_session.add(
            Inventory_materials(
                code="MAT-SABLON-HARTIE",
                name="Șablon hârtie",
                unit="mp",
                category="consumabile",
                unit_cost=5.0,
                currency="EUR",
                status="active",
            )
        )
        db_session.add(
            Inventory_materials(
                code="MAT-SABLON-MONTAJ",
                name="Șablon montaj Forex 3 mm",
                unit="mp",
                category="forex",
                unit_cost=6.0,
                currency="EUR",
                status="active",
            )
        )
        await db_session.commit()

    db_fixture.run(_setup())
    yield {"order_id": order_id, "preparer_id": preparer_id, "db_fixture": db_fixture}
    _cleanup_overrides()


def test_blueprint_exposes_prepared_by_and_preparation_domains(blueprint_prepared_by_fixture):
    order_id = blueprint_prepared_by_fixture["order_id"]
    preparer_id = blueprint_prepared_by_fixture["preparer_id"]
    client = _client_for(
        blueprint_prepared_by_fixture["db_fixture"],
        _user(f"admin-prep-{uuid.uuid4().hex[:6]}", "admin"),
    )
    response = client.get(f"/api/v1/operator/orders/{order_id}/production-blueprint")
    assert response.status_code == 200
    body = response.json()
    assert body["prepared_by_user_id"] == preparer_id
    assert body["prepared_by_user_name"] == "Responsabil Instrumentare"
    assert body["preparation_ownership"]["instrumentation"]["source_field"] == (
        "execution_plan.prepared_by_user_id"
    )

    tasks = {task["task_id"]: task for task in body["tasks"]}
    assert tasks["T-CNC"]["preparation_domain"] == "cnc"
    assert tasks["T-DOC"]["preparation_domain"] == "instrumentation"
    assert tasks["T-PRINT"]["preparation_domain"] == "print"

    groups = body["preparation_groups"]
    assert len(groups["cnc"]) == 1
    assert len(groups["instrumentation"]) == 1
    assert len(groups["print"]) == 1
