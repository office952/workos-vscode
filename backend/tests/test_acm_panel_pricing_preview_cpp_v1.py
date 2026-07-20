"""CPP quantities for AcmPanel — measured/proxy path quantities (no universal perimeter)."""

from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio

from seeds.seed_acm_bond_materials import seed_acm_bond_materials
from seeds.seed_acm_boxed_mounting_owner_rates import seed_acm_boxed_mounting_owner_rates
from seeds.seed_acm_owner_confirmed_prices import seed_acm_owner_confirmed_prices
from seeds.seed_tpl_acm_boxed_mounting_support_v1 import seed_tpl_acm_boxed_mounting_support_v1
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.acm_dxf_path_measurement import LENGTH_COMPARE_TOLERANCE_ML

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

LETTERS = "TPL-VOLUMETRIC-LETTERS_v2"
DOUBLE_DXF = Path(__file__).resolve().parent / "fixtures" / "acm_panel_dxf" / "2-pliuri-100x30.dxf"
TOL = LENGTH_COMPARE_TOLERANCE_ML


def _multi_panel_quote_input(*, fold_count: int = 1, l2_mm: float = 0.0, dxf: str | None = None) -> dict:
    finish = {
        "acm_panel_instance": {
            "schema": "acm_panel_component_instance_v1",
            "component_instance_id": "acm_mp",
            "association_status": "proposed",
            "technical_configuration_status": "proposed",
            "composition_status": "unconfirmed",
            "geometry": {
                "width_mm": 1000,
                "height_mm": 350,
                "panels": [
                    {
                        "panel_id": "p1",
                        "width_mm": 1000,
                        "height_mm": 350,
                        "position": {"x_mm": 0, "y_mm": 0},
                    },
                    {
                        "panel_id": "p2",
                        "width_mm": 1000,
                        "height_mm": 350,
                        "position": {"x_mm": 1000, "y_mm": 0},
                    },
                ],
                "joints": [{"joint_id": "j1"}],
            },
            "configuration": {
                "finished_depth_mm": 60,
                "fold_count": fold_count,
                "l1_mm": 60,
                "l2_mm": l2_mm,
                "field_authority": {"fold_count": "catalog_default"},
            },
        },
        "segmented_background": {
            "status": "PROPOSED",
            "panels": [
                {
                    "panel_id": "p1",
                    "width_mm": 1000,
                    "height_mm": 350,
                    "position": {"x_mm": 0, "y_mm": 0},
                },
                {
                    "panel_id": "p2",
                    "width_mm": 1000,
                    "height_mm": 350,
                    "position": {"x_mm": 1000, "y_mm": 0},
                },
            ],
            "assembly_dimensions": {"width_mm": 2000, "height_mm": 350},
        },
        "mounting_solution": {
            "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
            "configuration": {
                "panel_width_mm": 1000,
                "panel_height_mm": 350,
                "acm_thickness_mm": 3,
                "return_depth_mm": 60,
                "fold_sides": "all",
            },
        },
        "confirmed": True,
    }
    out: dict = {
        "quote_geometry": {
            "letter_count": 3,
            "letter_perimeter_m": 8.0,
            "letter_face_area_m2": 0.8,
        },
        "finish_setup": finish,
    }
    if dxf:
        out["acm_production_dxf_path"] = dxf
    return out


@pytest_asyncio.fixture
async def acm_rates_seeded_db(volumetric_v2_db):
    from seeds.seed_inventory_materials_stubs import seed_inventory_material_stubs

    await seed_inventory_material_stubs()
    await seed_acm_bond_materials()
    await seed_acm_owner_confirmed_prices()
    await seed_acm_boxed_mounting_owner_rates()
    await seed_tpl_acm_boxed_mounting_support_v1()
    return volumetric_v2_db


@pytest.mark.asyncio
async def test_cpp_single_fold_commercial_face_and_blank_perimeter_sum(acm_rates_seeded_db):
    preview = await CommercialPriceProposalService(acm_rates_seeded_db).build_preview(
        LETTERS,
        quote_input=_multi_panel_quote_input(fold_count=1, l2_mm=0),
    )
    assert preview is not None
    by_code = {line.code: line for line in preview.commercial_price_lines if line.code.startswith("acm_")}
    assert set(by_code) == {
        "acm_panel_cut",
        "acm_v_groove",
        "acm_panel_face_material",
        "acm_return_strip_material",
        "acm_boxed_assembly",
        "acm_fasteners",
    }
    assert by_code["acm_panel_face_material"].quantity == pytest.approx(0.7)
    # blank peri L1=60: 3.18 × 2
    assert by_code["acm_panel_cut"].quantity == pytest.approx(6.36)
    assert by_code["acm_v_groove"].quantity == pytest.approx(6.36)
    assert by_code["acm_boxed_assembly"].quantity == pytest.approx(0.7)
    assert by_code["acm_boxed_assembly"].subtotal == pytest.approx(20.0)
    assert by_code["acm_panel_cut"].commercial_unit_price == pytest.approx(1.5)
    assert by_code["acm_v_groove"].commercial_unit_price == pytest.approx(3.0)
    assert by_code["acm_panel_face_material"].commercial_unit_price == pytest.approx(15.0)
    assert preview.forbidden_hourly_usage_detected == []


@pytest.mark.asyncio
async def test_cpp_double_fold_without_dxf_uses_commercial_cut_v(acm_rates_seeded_db):
    preview = await CommercialPriceProposalService(acm_rates_seeded_db).build_preview(
        LETTERS,
        quote_input=_multi_panel_quote_input(fold_count=2, l2_mm=28),
    )
    assert preview is not None
    by_code = {line.code: line for line in preview.commercial_price_lines if line.code.startswith("acm_")}
    assert "acm_panel_face_material" in by_code
    assert by_code["acm_panel_face_material"].quantity == pytest.approx(0.7)
    assert "acm_panel_cut" in by_code
    assert "acm_v_groove" in by_code
    assert by_code["acm_panel_cut"].quantity == pytest.approx(6.808)
    assert by_code["acm_v_groove"].quantity == pytest.approx(11.76)
    assert preview.forbidden_hourly_usage_detected == []


@pytest.mark.asyncio
async def test_cpp_measured_dxf_double_fold_v_total(acm_rates_seeded_db):
    preview = await CommercialPriceProposalService(acm_rates_seeded_db).build_preview(
        LETTERS,
        quote_input=_multi_panel_quote_input(
            fold_count=2,
            l2_mm=30,
            dxf=str(DOUBLE_DXF),
        ),
    )
    assert preview is not None
    by_code = {line.code: line for line in preview.commercial_price_lines if line.code.startswith("acm_")}
    assert "acm_panel_cut" in by_code
    assert "acm_v_groove" in by_code
    assert by_code["acm_panel_cut"].quantity == pytest.approx(5.499412, abs=TOL)
    assert by_code["acm_v_groove"].quantity == pytest.approx(10.000004, abs=TOL)
    assert by_code["acm_v_groove"].commercial_unit_price == pytest.approx(3.0)
