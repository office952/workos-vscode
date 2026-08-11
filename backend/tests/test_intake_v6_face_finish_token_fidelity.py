"""Intake V6 face-finish token fidelity — series must reach CPP unchanged.

Slice: WORKOS_INTAKE_V6_FACE_FINISH_TOKEN_FIDELITY_V1
Boundary: mapping fidelity only — no Pricing Registry / Product Truth / schema changes.
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from schemas.intake_v4 import (
    IntakeV4ClientRequest,
    IntakeV4FinishSetup,
    IntakeV4LetterGroupFinish,
    IntakeV4ProductBinding,
    IntakeV4WorkspacePayload,
)
from services.commercial_price_proposal_service import (
    CommercialPriceProposalService,
    _coalesce_quote_input,
    _face_finish_token,
)
from services.intake_v4_pricing_input_service import (
    _template_face_finish_type,
    build_v4_pricing_input_preview,
)
from services.intake_v6_priced_quote_dry_run_service import (
    _enrich_quote_input_linked_logo_geometry,
)

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


@pytest_asyncio.fixture
async def cpp_service(volumetric_v2_db):
    yield CommercialPriceProposalService(volumetric_v2_db)


def _payload(finish: IntakeV4FinishSetup) -> IntakeV4WorkspacePayload:
    return IntakeV4WorkspacePayload(
        client=IntakeV4ClientRequest(),
        product_binding=IntakeV4ProductBinding(template_code="TPL-VOLUMETRIC-LETTERS"),
        finish_setup=finish,
        svg_analysis_json={"layers": []},
        quote_geometry={
            "letter_count": 5,
            "letter_perimeter_m": 12.5,
            "letter_face_area_m2": 1.2,
        },
    )


def _group(
    key: str,
    face: str,
    *,
    roll_mm: float | None = 1000,
    confirmed: bool = True,
) -> IntakeV4LetterGroupFinish:
    return IntakeV4LetterGroupFinish(
        group_key=key,
        layer_name=key,
        face_finish_type=face,
        face_vinyl_roll_width_mm=roll_mm,
        confirmed=confirmed,
    )


def _preview_for(face: str, *, groups: list[IntakeV4LetterGroupFinish] | None = None):
    letter_groups = groups or [_group("g1", face, roll_mm=1260 if face == "oracal_8500" else 1000)]
    finish = IntakeV4FinishSetup(
        face_finish_type=face,
        face_vinyl_roll_width_mm=1260 if face == "oracal_8500" else 1000,
        letter_group_finishes=letter_groups,
        confirmed=True,
        illuminated=True,
    )
    return build_v4_pricing_input_preview(workspace_id="ws-face-fidelity", payload=_payload(finish))


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("none", "none"),
        ("oracal_641", "oracal_641"),
        ("oracal_651", "oracal_651"),
        ("oracal_8500", "oracal_8500"),
        ("print_laminate", "printed_laminated_vinyl"),
        ("vinyl", "oracal_651"),
        ("printed_vinyl", "printed_vinyl"),
    ],
)
def test_template_face_finish_preserves_series(raw: str, expected: str):
    assert _template_face_finish_type(raw) == expected


@pytest.mark.parametrize(
    "face,expected_qi",
    [
        ("none", "none"),
        ("oracal_641", "oracal_641"),
        ("oracal_651", "oracal_651"),
        ("oracal_8500", "oracal_8500"),
        ("print_laminate", "print_laminate"),
    ],
)
def test_quote_input_preserves_operator_face_token(face: str, expected_qi: str):
    preview = _preview_for(face)
    qi = preview.quote_input_payload
    assert qi.get("face_finish_type") == expected_qi
    assert preview.finish_summary.get("face_finish_type") == expected_qi
    handoff = (qi.get("letter_group_face_vinyl_handoff") or {}).get("groups") or []
    if face == "none":
        assert handoff == []
        return
    assert handoff[0]["face_finish_raw"] == face
    if face == "print_laminate":
        assert handoff[0]["face_finish_type"] == "printed_laminated_vinyl"
        assert handoff[0].get("face_oracal_series") is None
    else:
        assert handoff[0]["face_finish_type"] == face
        expected_series = {"oracal_641": "641", "oracal_651": "651", "oracal_8500": "8500"}[face]
        assert handoff[0].get("face_oracal_series") == expected_series


def test_mixed_groups_preserve_per_group_identity():
    preview = _preview_for(
        "oracal_641",
        groups=[
            _group("g641", "oracal_641"),
            _group("g651", "oracal_651"),
        ],
    )
    groups = (preview.quote_input_payload.get("letter_group_face_vinyl_handoff") or {}).get("groups") or []
    by_id = {g["group_id"]: g for g in groups}
    assert by_id["g641"]["face_finish_type"] == "oracal_641"
    assert by_id["g641"]["face_oracal_series"] == "641"
    assert by_id["g651"]["face_finish_type"] == "oracal_651"
    assert by_id["g651"]["face_oracal_series"] == "651"
    matrix = preview.quote_input_payload.get("letter_group_finish_matrix") or []
    assert {row["face_finish_type"] for row in matrix} == {"oracal_641", "oracal_651"}
    assert {row["face_finish_template_type"] for row in matrix} == {"oracal_641", "oracal_651"}


def test_mixed_651_8500_preserve_per_group_identity():
    preview = _preview_for(
        "oracal_651",
        groups=[
            _group("g651", "oracal_651"),
            _group("g8500", "oracal_8500", roll_mm=1260),
        ],
    )
    groups = (preview.quote_input_payload.get("letter_group_face_vinyl_handoff") or {}).get("groups") or []
    by_id = {g["group_id"]: g for g in groups}
    assert by_id["g651"]["face_finish_type"] == "oracal_651"
    assert by_id["g8500"]["face_finish_type"] == "oracal_8500"


def test_none_plus_641_preserves_both_matrix_rows():
    preview = _preview_for(
        "oracal_641",
        groups=[
            _group("g_none", "none", roll_mm=None),
            _group("g641", "oracal_641"),
        ],
    )
    matrix = preview.quote_input_payload.get("letter_group_finish_matrix") or []
    by_id = {row["group_id"]: row for row in matrix}
    assert by_id["g_none"]["face_finish_type"] == "none"
    assert by_id["g_none"]["face_finish_template_type"] == "none"
    assert by_id["g641"]["face_finish_type"] == "oracal_641"
    handoff = (preview.quote_input_payload.get("letter_group_face_vinyl_handoff") or {}).get("groups") or []
    assert [g["group_id"] for g in handoff] == ["g641"]


def test_enrich_bridges_workspace_face_over_vinyl_collapse():
    quote_input = {"face_finish_type": "vinyl", "letter_face_area_m2": 1.2}
    payload_raw = {
        "finish_setup": {
            "face_finish_type": "oracal_641",
            "letter_group_finishes": [
                {"group_key": "g1", "face_finish_type": "oracal_641", "confirmed": True}
            ],
        }
    }
    enriched = _enrich_quote_input_linked_logo_geometry(payload_raw, quote_input)
    assert enriched["face_finish_type"] == "oracal_641"
    assert enriched["finish_setup"]["face_finish_type"] == "oracal_641"
    assert enriched["finish_setup"]["letter_group_finishes"][0]["face_finish_type"] == "oracal_641"
    coalesced = _coalesce_quote_input(enriched)
    assert _face_finish_token(coalesced) == "oracal_641"


def test_enrich_bridges_print_laminate_over_printed_vinyl():
    quote_input = {"face_finish_type": "printed_vinyl"}
    payload_raw = {"finish_setup": {"face_finish_type": "print_laminate"}}
    enriched = _enrich_quote_input_linked_logo_geometry(payload_raw, quote_input)
    assert enriched["face_finish_type"] == "print_laminate"
    assert _face_finish_token(_coalesce_quote_input(enriched)) == "print_laminate"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "face,material_code,unit_price",
    [
        ("oracal_641", "finisaje_oracal_641_material", 6.5),
        ("oracal_651", "finisaje_oracal_651_material", 5.0),
    ],
)
async def test_cpp_emits_series_face_lines_from_adapter_quote_input(
    cpp_service: CommercialPriceProposalService,
    face: str,
    material_code: str,
    unit_price: float,
):
    preview_adapter = _preview_for(face)
    qi = dict(preview_adapter.quote_input_payload)
    qi["letter_face_area_m2"] = 1.2
    qi["quote_geometry"] = {
        "letter_count": 5,
        "letter_perimeter_m": 12.5,
        "letter_face_area_m2": 1.2,
    }
    # Simulate dry-run enrich from workspace (same token).
    qi = _enrich_quote_input_linked_logo_geometry(
        {
            "finish_setup": {
                "face_finish_type": face,
                "face_vinyl_roll_width_mm": 1000,
                "letter_group_finishes": [
                    {"group_key": "g1", "face_finish_type": face, "confirmed": True}
                ],
                "confirmed": True,
            }
        },
        qi,
    )
    commercial = await cpp_service.build_preview(TEMPLATE, quote_input=qi)
    assert commercial is not None
    codes = {line.code for line in commercial.commercial_price_lines}
    assert material_code in codes
    assert "finisaje_aplicare_autocolant_fata" in codes
    material = next(line for line in commercial.commercial_price_lines if line.code == material_code)
    assert material.commercial_unit_price == unit_price
    assert material.subtotal == pytest.approx(unit_price * 1.2)


@pytest.mark.asyncio
async def test_cpp_8500_line_from_adapter_quote_input(cpp_service: CommercialPriceProposalService):
    preview_adapter = _preview_for("oracal_8500")
    qi = dict(preview_adapter.quote_input_payload)
    qi["letter_face_area_m2"] = 1.2
    qi["quote_geometry"] = {"letter_face_area_m2": 1.2, "letter_perimeter_m": 12.5, "letter_count": 5}
    qi = _enrich_quote_input_linked_logo_geometry(
        {
            "finish_setup": {
                "face_finish_type": "oracal_8500",
                "face_vinyl_roll_width_mm": 1260,
                "letter_group_finishes": [
                    {
                        "group_key": "g1",
                        "face_finish_type": "oracal_8500",
                        "face_vinyl_roll_width_mm": 1260,
                        "confirmed": True,
                    }
                ],
                "confirmed": True,
            }
        },
        qi,
    )
    commercial = await cpp_service.build_preview(TEMPLATE, quote_input=qi)
    assert commercial is not None
    material = next(
        line for line in commercial.commercial_price_lines if line.code == "finisaje_oracal_8500_material"
    )
    assert material.commercial_unit_price == 13.5
    assert "finisaje_aplicare_autocolant_fata" in {line.code for line in commercial.commercial_price_lines}


@pytest.mark.asyncio
async def test_cpp_none_has_no_face_oracal_or_aplicare(cpp_service: CommercialPriceProposalService):
    preview_adapter = _preview_for("none")
    qi = dict(preview_adapter.quote_input_payload)
    qi["letter_face_area_m2"] = 1.2
    qi["quote_geometry"] = {"letter_face_area_m2": 1.2}
    qi = _enrich_quote_input_linked_logo_geometry(
        {"finish_setup": {"face_finish_type": "none", "confirmed": True}},
        qi,
    )
    commercial = await cpp_service.build_preview(TEMPLATE, quote_input=qi)
    assert commercial is not None
    codes = {line.code for line in commercial.commercial_price_lines}
    assert "finisaje_oracal_641_material" not in codes
    assert "finisaje_oracal_651_material" not in codes
    assert "finisaje_oracal_8500_material" not in codes
    assert "finisaje_print_laminate_material" not in codes
    assert "finisaje_aplicare_autocolant_fata" not in codes


@pytest.mark.asyncio
async def test_cpp_print_laminate_distinct(cpp_service: CommercialPriceProposalService):
    preview_adapter = _preview_for("print_laminate")
    qi = dict(preview_adapter.quote_input_payload)
    qi["letter_face_area_m2"] = 1.2
    qi["quote_geometry"] = {"letter_face_area_m2": 1.2}
    qi = _enrich_quote_input_linked_logo_geometry(
        {"finish_setup": {"face_finish_type": "print_laminate", "confirmed": True}},
        qi,
    )
    commercial = await cpp_service.build_preview(TEMPLATE, quote_input=qi)
    assert commercial is not None
    codes = {line.code for line in commercial.commercial_price_lines}
    assert "finisaje_print_laminate_material" in codes
    assert "finisaje_oracal_641_material" not in codes
    assert "finisaje_oracal_651_material" not in codes
    assert "finisaje_aplicare_autocolant_fata" in codes
    material = next(
        line for line in commercial.commercial_price_lines if line.code == "finisaje_print_laminate_material"
    )
    assert material.commercial_unit_price == 10.0
