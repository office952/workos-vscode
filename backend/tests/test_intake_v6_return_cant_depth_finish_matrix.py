"""RETURN-CANT commercial depth × finish matrix integrity.

Slice: WORKOS_INTAKE_V6_RETURN_CANT_COMMERCIAL_DEPTH_FINISH_MATRIX_INTEGRITY_V1
Authority: existing CPP F7F/F7H rules + owner RAL depth tiers — no new rates.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select

from models.workcenter_rates import Workcenter_rates
from schemas.intake_v4 import (
    IntakeV4ClientRequest,
    IntakeV4FinishSetup,
    IntakeV4LetterGroupFinish,
    IntakeV4ProductBinding,
    IntakeV4WorkspacePayload,
)
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.intake_v4_pricing_input_service import build_v4_pricing_input_preview
from services.intake_v6_priced_quote_dry_run_service import (
    _enrich_quote_input_linked_logo_geometry,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
PERIMETER = 12.5


@pytest_asyncio.fixture
async def cpp_service(volumetric_v2_db):
    yield CommercialPriceProposalService(volumetric_v2_db)


async def _ensure_ral_labor_rate(db) -> None:
    existing = (
        await db.execute(
            select(Workcenter_rates).where(Workcenter_rates.code == "RETURN_CANT_RAL_PAINT_LABOR").limit(1)
        )
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            Workcenter_rates(
                code="RETURN_CANT_RAL_PAINT_LABOR",
                label="RETURN_CANT_RAL_PAINT_LABOR",
                rate_basis="per_linear_meter",
                rate_per_linear_meter=1.0,
                currency="EUR",
                status="active",
                is_active=True,
                notes="RETURN-CANT matrix fixture — owner-confirmed 1 EUR/ml.",
            )
        )
    else:
        existing.rate_per_linear_meter = 1.0
        existing.currency = "EUR"
        existing.status = "active"
        existing.is_active = True
    await db.commit()


def _payload(finish: str, depth: int, *, groups: list[dict] | None = None) -> dict:
    return {
        "analysis_ready": True,
        "svg_source": {"file_name": "test.svg"},
        "client": {"width_mm": 1200, "height_mm": 400},
        "quote_geometry": {
            "letter_count": 5,
            "letter_perimeter_m": PERIMETER,
            "letter_face_area_m2": 1.2,
        },
        "letter_perimeter_m": PERIMETER,
        "return_finish_type": finish,
        "return_depth_mm": depth,
        "finish_setup": {
            "face_finish_type": "none",
            "return_depth_mm": depth,
            "return_finish_type": finish,
            "backing_mode": "closed_back",
            "mounting_system": "direct_wall",
            "lighting_system_type": "front_lit",
            "illuminated": True,
            "led_module_count": 24,
            "selected_psu_watts": 100,
            "required_psu_watts": 140.4,
            "mounting_template_enabled": True,
            "mounting_template_area_m2": 2.5,
            "mounting_template_material_type": "paper",
            "letter_group_finishes": groups
            or [{"group_key": "default", "confirmed": True, "return_finish_type": finish, "return_depth_mm": depth}],
        },
    }


def _line(preview, code: str):
    return next(line for line in preview.commercial_price_lines if line.code == code)


def _has_prefix(preview, prefix: str) -> bool:
    return any(str(line.code or "").startswith(prefix) for line in preview.commercial_price_lines)


@pytest.mark.asyncio
@pytest.mark.parametrize("depth", [30, 60, 80, 100])
async def test_stock_finish_zero_cant_surcharge_all_depths(
    cpp_service: CommercialPriceProposalService, depth: int
):
    preview = await cpp_service.build_preview(
        TEMPLATE, quote_input=_payload("white_aluminum", depth)
    )
    assert preview is not None
    assert not _has_prefix(preview, "finisaje_cant_")
    forming = _line(preview, "modelare_cant_aluminiu")
    # Existing CPP forming authority is flat EUR/ml — depth does not change unit rate.
    assert forming.commercial_unit_price == 5.0
    assert forming.quantity == pytest.approx(PERIMETER)


@pytest.mark.asyncio
async def test_oracal_material_monotone_with_depth(cpp_service: CommercialPriceProposalService):
    rows = []
    for depth in (30, 60, 80, 100):
        preview = await cpp_service.build_preview(
            TEMPLATE, quote_input=_payload("oracal_wrapped", depth)
        )
        material = _line(preview, "finisaje_cant_oracal_material")
        labor = _line(preview, "finisaje_cant_oracal_labor")
        expected_qty = round(PERIMETER * (depth / 1000.0), 6)
        assert material.quantity == pytest.approx(expected_qty)
        assert material.commercial_unit_price == 5.0  # 651 series
        assert material.subtotal == pytest.approx(5.0 * expected_qty)
        # F7F authority: Oracal cant labor = 3 EUR/m2 on developed wrap area (same qty).
        assert labor.basis_type == "m2"
        assert labor.quantity == pytest.approx(expected_qty)
        assert labor.commercial_unit_price == pytest.approx(3.0)
        rows.append((depth, material.subtotal, labor.subtotal))
    mats = [r[1] for r in rows]
    assert mats == sorted(mats)
    assert mats[0] < mats[1] < mats[2] < mats[3]


@pytest.mark.asyncio
async def test_ral_material_tiers_and_constant_labor(
    cpp_service: CommercialPriceProposalService, volumetric_v2_db
):
    await _ensure_ral_labor_rate(volumetric_v2_db)
    expected_rates = {30: 2.0, 60: 2.5, 80: 3.0, 100: 4.0}
    mat_subs = []
    labor_subs = []
    for depth, rate in expected_rates.items():
        preview = await cpp_service.build_preview(
            TEMPLATE, quote_input=_payload("ral_paint", depth)
        )
        material = _line(preview, "finisaje_cant_ral_material")
        labor = _line(preview, "finisaje_cant_ral_labor")
        assert material.commercial_unit_price == pytest.approx(rate)
        assert material.quantity == pytest.approx(PERIMETER)
        assert material.subtotal == pytest.approx(rate * PERIMETER)
        assert labor.commercial_unit_price == pytest.approx(1.0)
        assert labor.quantity == pytest.approx(PERIMETER)
        assert labor.subtotal == pytest.approx(PERIMETER)
        mat_subs.append(material.subtotal)
        labor_subs.append(labor.subtotal)
    assert mat_subs == sorted(mat_subs)
    assert mat_subs[0] < mat_subs[1] < mat_subs[2] < mat_subs[3]
    assert len(set(round(x, 6) for x in labor_subs)) == 1


@pytest.mark.asyncio
async def test_enrich_bridges_return_depth_mm_over_missing_quote_depth():
    quote_input = {
        "face_finish_type": "none",
        "return_finish_type": "oracal_wrapped",
        # depth omitted / wrong — workspace is authority
        "letter_perimeter_m": PERIMETER,
    }
    payload_raw = {
        "finish_setup": {
            "return_finish_type": "oracal_wrapped",
            "return_depth_mm": 100,
            "letter_group_finishes": [
                {
                    "group_key": "g1",
                    "return_finish_type": "oracal_wrapped",
                    "return_depth_mm": 100,
                    "confirmed": True,
                }
            ],
        }
    }
    enriched = _enrich_quote_input_linked_logo_geometry(payload_raw, quote_input)
    assert enriched["finish_setup"]["return_depth_mm"] == 100
    assert enriched.get("return_depth_mm") == 100 or enriched["finish_setup"]["return_depth_mm"] == 100


@pytest.mark.asyncio
async def test_pricing_input_preserves_return_depth_and_finish():
    finish = IntakeV4FinishSetup(
        face_finish_type="none",
        return_finish_type="ral_paint",
        return_depth_mm=80,
        letter_group_finishes=[
            IntakeV4LetterGroupFinish(
                group_key="g1",
                layer_name="L",
                face_finish_type="none",
                return_finish_type="ral_paint",
                return_depth_mm=80,
                confirmed=True,
            )
        ],
        confirmed=True,
        illuminated=True,
    )
    preview = build_v4_pricing_input_preview(
        workspace_id="ws-cant",
        payload=IntakeV4WorkspacePayload(
            client=IntakeV4ClientRequest(),
            product_binding=IntakeV4ProductBinding(template_code="TPL-VOLUMETRIC-LETTERS"),
            finish_setup=finish,
            svg_analysis_json={"layers": []},
            quote_geometry={"letter_count": 5, "letter_perimeter_m": PERIMETER},
        ),
    )
    qi = preview.quote_input_payload
    assert qi.get("return_depth_mm") == 80
    matrix = qi.get("letter_group_finish_matrix") or []
    assert matrix[0]["return_depth_mm"] == 80
    assert matrix[0]["return_finish_type"] == "ral_paint"


@pytest.mark.asyncio
async def test_mixed_group_depths_preserve_matrix_identity():
    finish = IntakeV4FinishSetup(
        face_finish_type="none",
        return_finish_type="oracal_wrapped",
        return_depth_mm=30,
        letter_group_finishes=[
            IntakeV4LetterGroupFinish(
                group_key="g30",
                layer_name="A",
                face_finish_type="none",
                return_finish_type="oracal_wrapped",
                return_depth_mm=30,
                perimeter_m=5.0,
                confirmed=True,
            ),
            IntakeV4LetterGroupFinish(
                group_key="g100",
                layer_name="B",
                face_finish_type="none",
                return_finish_type="oracal_wrapped",
                return_depth_mm=100,
                perimeter_m=7.5,
                confirmed=True,
            ),
        ],
        confirmed=True,
        illuminated=True,
    )
    preview = build_v4_pricing_input_preview(
        workspace_id="ws-mixed-cant",
        payload=IntakeV4WorkspacePayload(
            client=IntakeV4ClientRequest(),
            product_binding=IntakeV4ProductBinding(template_code="TPL-VOLUMETRIC-LETTERS"),
            finish_setup=finish,
            svg_analysis_json={"layers": []},
            quote_geometry={"letter_count": 5, "letter_perimeter_m": PERIMETER},
        ),
    )
    matrix = preview.quote_input_payload.get("letter_group_finish_matrix") or []
    by_id = {row["group_id"]: row for row in matrix}
    assert by_id["g30"]["return_depth_mm"] == 30
    assert by_id["g100"]["return_depth_mm"] == 100


@pytest.mark.asyncio
async def test_cpp_mixed_oracal_depths_aggregate_developed_area(
    cpp_service: CommercialPriceProposalService,
):
    """When groups carry distinct cant depths, CPP must not collapse to a single job depth."""
    groups = [
        {
            "group_key": "g30",
            "return_finish_type": "oracal_wrapped",
            "return_depth_mm": 30,
            "perimeter_m": 5.0,
            "confirmed": True,
        },
        {
            "group_key": "g100",
            "return_finish_type": "oracal_wrapped",
            "return_depth_mm": 100,
            "perimeter_m": 7.5,
            "confirmed": True,
        },
    ]
    # Job-level depth deliberately wrong/dominant — groups are truth.
    payload = _payload("oracal_wrapped", 30, groups=groups)
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=payload)
    assert preview is not None
    material = _line(preview, "finisaje_cant_oracal_material")
    # 5.0*0.03 + 7.5*0.10 = 0.15 + 0.75 = 0.90 m2
    assert material.quantity == pytest.approx(0.90)
    assert material.subtotal == pytest.approx(4.5)


@pytest.mark.asyncio
async def test_cpp_mixed_ral_depths_use_per_group_tiers(
    cpp_service: CommercialPriceProposalService, volumetric_v2_db
):
    await _ensure_ral_labor_rate(volumetric_v2_db)
    groups = [
        {
            "group_key": "g30",
            "return_finish_type": "ral_paint",
            "return_depth_mm": 30,
            "perimeter_m": 5.0,
            "confirmed": True,
        },
        {
            "group_key": "g100",
            "return_finish_type": "ral_paint",
            "return_depth_mm": 100,
            "perimeter_m": 7.5,
            "confirmed": True,
        },
    ]
    payload = _payload("ral_paint", 30, groups=groups)
    preview = await cpp_service.build_preview(TEMPLATE, quote_input=payload)
    assert preview is not None
    material = _line(preview, "finisaje_cant_ral_material")
    # 5*2.0 + 7.5*4.0 = 10 + 30 = 40
    assert material.subtotal == pytest.approx(40.0)
    labor = _line(preview, "finisaje_cant_ral_labor")
    assert labor.subtotal == pytest.approx(12.5)  # 5+7.5 ml @ 1 EUR/ml
