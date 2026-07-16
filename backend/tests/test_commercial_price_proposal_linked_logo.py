"""Linked-logo commercial pricing — characterization + contract tests (G1–G5)."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from seeds.seed_tpl_volumetric_logo_v1 import seed_tpl_volumetric_logo_v1
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.product_aggregate_workspace_composition_service import build_workspace_composed_aggregate
from services.product_definition_builder_service import ProductDefinitionBuilderService
from services.product_template_availability_service import ProductTemplateAvailabilityService
from services.template_architecture_scope import VOLUMETRIC_LOGO_TEMPLATE_CODE
from services.template_usage_mode_policy import is_linked_child_allowed_template, is_root_offerable_template
from tests.eic_workspace_logo_fixtures import confirmed_bindings_payload, single_logo_bindings_payload

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

ROOT = "TPL-VOLUMETRIC-LETTERS_v2"
LOGO = VOLUMETRIC_LOGO_TEMPLATE_CODE


def _letters_only_quote_input() -> dict[str, Any]:
    return {
        "analysis_ready": True,
        "svg_source": {"file_name": "letters-only.svg"},
        "client": {"width_mm": 1200, "height_mm": 400},
        "quote_geometry": {
            "letter_count": 5,
            "letter_perimeter_m": 12.5,
            "letter_face_area_m2": 1.2,
            "artwork_piece_count": 0,
            "artwork_area_m2": None,
            "artwork_boxes": [],
            "artwork_return_layers": [],
            "artwork_return_perimeter_ml": None,
        },
        "finish_setup": {
            "face_finish_type": "plexiglas_clear",
            "return_depth_mm": 60,
            "return_finish_type": "ral",
            "volum_aluminum_module_template_code": "TPL-VOLUM-ALUMINIU_v1",
            "backing_mode": "closed_back",
            "mounting_system": "direct_wall",
            "lighting_system_type": "front_lit",
            "illuminated": True,
            "led_module_count": 24,
            "letter_led_module_count": 24,
            "emblem_led_module_count": 0,
            "emblem_lighting_mode": "excluded",
            "selected_psu_watts": 100,
            "required_psu_watts": 40,
            "mounting_template_enabled": True,
            "mounting_template_area_m2": 2.5,
            "mounting_template_material_type": "forex",
            "letter_group_finishes": [{"group_key": "default", "confirmed": True}],
            "artwork_finishes": [],
        },
    }


def _two_logo_quote_input(*, site_install: bool = True) -> dict[str, Any]:
    payload = confirmed_bindings_payload()
    finish = dict(payload["finish_setup"])
    finish.update(
        {
            "illuminated": True,
            "lighting_system_type": "led_modules",
            "emblem_lighting_mode": "area_lit",
            "light_color": "cool",
            "letter_led_module_count": 85,
            "emblem_led_module_count": 60,
            "led_module_count": 145,
            "total_led_module_count": 145,
            "mounting_template_enabled": True,
            "mounting_template_area_m2": 3.0523,
            "mounting_template_material_type": "forex",
            "mounting_solution": {"kind": "installation_template", "template_code": None, "configuration": {}},
            "mounting_scope": "preparation_and_site_installation" if site_install else "preparation_only",
            "site_installation_included": True if site_install else False,
            "volum_aluminum_module_template_code": "TPL-VOLUM-ALUMINIU_v1",
            "backing_mode": "closed_back",
            "letter_group_finishes": [{"group_key": "default", "confirmed": True}],
        }
    )
    payload["finish_setup"] = finish
    payload["quote_geometry"] = {
        **payload.get("quote_geometry", {}),
        "letter_count": 19,
        "letter_perimeter_m": 21.1675,
        "letter_face_area_m2": 1.2638,
        "artwork_area_m2": 0.8005,
        "artwork_piece_count": 2,
        "artwork_boxes": [
            {
                "layer_key": "logo_instance_001",
                "layer_name": "Logo 1",
                "width_mm": 667.2,
                "height_mm": 599.9,
                "area_m2": 0.4002,
            },
            {
                "layer_key": "logo_instance_002",
                "layer_name": "Logo 2",
                "width_mm": 667.2,
                "height_mm": 599.9,
                "area_m2": 0.4002,
            },
        ],
        "artwork_return_layers": [
            {
                "layer_key": "logo_instance_001",
                "layer_name": "Logo 1",
                "return_perimeter_ml": 2.4455,
                "return_depth_mm": 60.0,
                "execution_type": "print_laminate",
            },
            {
                "layer_key": "logo_instance_002",
                "layer_name": "Logo 2",
                "return_perimeter_ml": 2.4455,
                "return_depth_mm": 60.0,
                "execution_type": "print_laminate",
            },
        ],
        "artwork_return_perimeter_ml": 4.891,
    }
    payload["svg_source"] = {"file_name": "gradi-curat.svg"}
    payload["client"] = {"width_mm": 5086.99, "height_mm": 600.03}
    return payload


@pytest_asyncio.fixture
async def logo_seeded_db(volumetric_v2_db):
    await seed_tpl_volumetric_logo_v1()
    yield volumetric_v2_db


@pytest_asyncio.fixture
async def cpp_service(logo_seeded_db):
    yield CommercialPriceProposalService(logo_seeded_db)


async def _persist_workspace(db, payload: dict[str, Any]) -> IntakeV6WorkspaceRecord:
    import json

    record = IntakeV6WorkspaceRecord(
        id=str(uuid.uuid4()),
        workspace_code=f"WS-LOGO-CPP-{uuid.uuid4().hex[:8]}",
        title="Linked logo commercial pricing test",
        template_code=ROOT,
        status="draft",
        payload_json=json.dumps(payload),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


def _line_codes(preview) -> set[str]:
    return {line.code for line in preview.commercial_price_lines}


def _lines_for_segment(preview, segment_key: str) -> list:
    return [
        line
        for line in preview.commercial_price_lines
        if getattr(line, "segment_key", None) == segment_key
        or segment_key in line.code
        or segment_key in (line.label or "")
    ]


# --- 1. letters-only unchanged ---
@pytest.mark.asyncio
async def test_letters_only_composition_unchanged(cpp_service: CommercialPriceProposalService):
    preview = await cpp_service.build_preview(ROOT, quote_input=_letters_only_quote_input())
    assert preview is not None
    codes = _line_codes(preview)
    assert "debitare_fata" in codes
    assert "modelare_cant_aluminiu" in codes
    assert "debitare_spate" in codes
    assert not any("logo" in c for c in codes)
    assert preview.subtotal_commercial is not None
    # letter LED uses letter-only count (24), not inflated by emblems
    led = next(line for line in preview.commercial_price_lines if line.code == "sistem_led_module")
    assert led.quantity == 24


# --- 4–5. linked-child template policy / availability ---
@pytest.mark.asyncio
async def test_linked_logo_template_not_root_offerable(logo_seeded_db):
    assert is_root_offerable_template(LOGO) is False
    assert is_linked_child_allowed_template(LOGO) is True
    items = await ProductTemplateAvailabilityService(logo_seeded_db).list_availability()
    logo_items = [i for i in items.items if i.template_code == LOGO]
    assert logo_items, "seeded logo must appear in availability for linked-child resolution"
    assert logo_items[0].quote_offerable is False
    assert logo_items[0].capabilities.root_offerable is False
    assert logo_items[0].capabilities.linked_child_offerable is True


# --- 6–7. PD/PA distinct logo components ---
@pytest.mark.asyncio
async def test_product_definition_includes_distinct_logo_segments(logo_seeded_db):
    payload = _two_logo_quote_input()
    record = await _persist_workspace(logo_seeded_db, payload)
    pd = await ProductDefinitionBuilderService(logo_seeded_db).build_preview(ROOT, workspace_id=record.id)
    assert pd is not None
    linked = pd.linked_template_runtime_segments or {}
    segments = linked.get("segments") if isinstance(linked, dict) else None
    assert isinstance(segments, list)
    keys = {s.get("segment_key") for s in segments}
    assert "logo_instance_001" in keys
    assert "logo_instance_002" in keys
    assert all(s.get("owning_template_code") == LOGO for s in segments if s.get("segment_key") in keys)


@pytest.mark.asyncio
async def test_product_aggregate_includes_distinct_linked_logo_components(logo_seeded_db):
    payload = _two_logo_quote_input()
    record = await _persist_workspace(logo_seeded_db, payload)
    aggregate = await build_workspace_composed_aggregate(
        logo_seeded_db, template_code=ROOT, workspace_id=record.id
    )
    assert aggregate is not None
    linked_count = (aggregate.provenance_summary.aggregate_totals or {}).get("linked_logo_segments")
    assert linked_count == 2
    logo_components = [
        c
        for c in aggregate.components
        if "logo_instance_001" in c.component_id or "logo_instance_002" in c.component_id
    ]
    assert logo_components
    assert any("logo_instance_001" in c.component_id for c in logo_components)
    assert any("logo_instance_002" in c.component_id for c in logo_components)


# --- 2–3, 8–14, 16–17, 24. CPP logo lines ---
@pytest.mark.asyncio
async def test_letters_plus_two_logos_emit_distinct_cpp_lines(cpp_service: CommercialPriceProposalService, logo_seeded_db):
    payload = _two_logo_quote_input()
    record = await _persist_workspace(logo_seeded_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None

    # letter body lines still present (keys unchanged)
    assert {"debitare_fata", "modelare_cant_aluminiu", "debitare_spate"}.issubset(_line_codes(preview))

    logo1 = _lines_for_segment(preview, "logo_instance_001")
    logo2 = _lines_for_segment(preview, "logo_instance_002")
    assert logo1, "Logo 1 must have commercial lines"
    assert logo2, "Logo 2 must have commercial lines"

    required_dims = {
        "face",
        "return",
        "back",
        "print",
        "laminate",
        "application",
        "led",
    }

    def _dims(lines) -> set[str]:
        blob = " ".join(f"{line.code} {line.label} {line.pricing_rule_code}".lower() for line in lines)
        found = set()
        for dim in required_dims:
            if dim in blob or (dim == "led" and "ilumin" in blob) or (dim == "return" and "cant" in blob):
                found.add(dim)
        return found

    assert required_dims.issubset(_dims(logo1))
    assert required_dims.issubset(_dims(logo2))

    # no duplicate codes across logos for same dimension families
    codes1 = {line.code for line in logo1}
    codes2 = {line.code for line in logo2}
    assert codes1.isdisjoint(codes2)

    # letter LED must not double-count emblem modules
    letter_led = next(line for line in preview.commercial_price_lines if line.code == "sistem_led_module")
    assert letter_led.quantity == 85

    # no EIC copy / hourly
    blob = preview.model_dump_json().lower()
    assert "rate_per_hour" not in blob
    assert "estimated_internal_cost" not in blob or "diagnostic" in blob


@pytest.mark.asyncio
async def test_letters_plus_one_logo(cpp_service: CommercialPriceProposalService, logo_seeded_db):
    payload = single_logo_bindings_payload(area_m2=0.4002)
    finish = dict(payload["finish_setup"])
    finish.update(
        {
            "illuminated": True,
            "lighting_system_type": "led_modules",
            "emblem_lighting_mode": "area_lit",
            "letter_led_module_count": 85,
            "emblem_led_module_count": 30,
            "led_module_count": 115,
            "volum_aluminum_module_template_code": "TPL-VOLUM-ALUMINIU_v1",
            "backing_mode": "closed_back",
            "mounting_template_enabled": True,
            "mounting_template_area_m2": 2.0,
            "mounting_template_material_type": "forex",
            "letter_group_finishes": [{"group_key": "default", "confirmed": True}],
        }
    )
    payload["finish_setup"] = finish
    payload["quote_geometry"] = {
        **payload.get("quote_geometry", {}),
        "letter_count": 19,
        "letter_perimeter_m": 21.1675,
        "letter_face_area_m2": 1.2638,
        "artwork_area_m2": 0.4002,
        "artwork_piece_count": 1,
        "artwork_boxes": [
            {
                "layer_key": "logo_instance_001",
                "layer_name": "Logo 1",
                "width_mm": 667.2,
                "height_mm": 599.9,
                "area_m2": 0.4002,
            }
        ],
        "artwork_return_layers": [
            {
                "layer_key": "logo_instance_001",
                "layer_name": "Logo 1",
                "return_perimeter_ml": 2.4455,
                "return_depth_mm": 60.0,
                "execution_type": "print_laminate",
            }
        ],
    }
    payload["client"] = {"width_mm": 1200, "height_mm": 400}
    record = await _persist_workspace(logo_seeded_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None
    assert _lines_for_segment(preview, "logo_instance_001")
    assert not _lines_for_segment(preview, "logo_instance_002")


# --- 18–20. fail closed / no invented ---
@pytest.mark.asyncio
async def test_missing_logo_tariff_fails_closed(cpp_service: CommercialPriceProposalService, logo_seeded_db):
    payload = _two_logo_quote_input()
    record = await _persist_workspace(logo_seeded_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None
    print_lines = [
        line
        for line in preview.commercial_price_lines
        if "print" in line.code.lower() and getattr(line, "segment_key", None)
    ]
    # If no owner commercial tariff for print, unit price must be null (fail closed)
    assert print_lines
    for line in print_lines:
        if line.commercial_unit_price is None:
            assert line.subtotal is None
            assert line.owner_decision_required is True


# --- 21–22. installation required / packaging deferred ---
@pytest.mark.asyncio
async def test_installation_commercial_line_when_included(cpp_service: CommercialPriceProposalService, logo_seeded_db):
    payload = _two_logo_quote_input(site_install=True)
    record = await _persist_workspace(logo_seeded_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None
    montaj = next(line for line in preview.commercial_price_lines if line.code == "montaj")
    assert montaj.owner_decision_required is True
    # required → not silently ready when price missing
    assert montaj.commercial_unit_price is None
    assert preview.status in {"partial", "blocked"}
    ambalare = next(line for line in preview.commercial_price_lines if line.code == "ambalare")
    assert ambalare.owner_decision_required is True


# --- 15, 23. PSU / VAT handled at dry-run; CPP currency RON ---
@pytest.mark.asyncio
async def test_cpp_currency_ron_and_no_logo_fallback_to_letter_codes(
    cpp_service: CommercialPriceProposalService, logo_seeded_db
):
    payload = _two_logo_quote_input()
    record = await _persist_workspace(logo_seeded_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None
    assert preview.currency == "RON"
    logo_lines = [line for line in preview.commercial_price_lines if getattr(line, "segment_key", None)]
    assert logo_lines
    for line in logo_lines:
        assert line.code not in {
            "debitare_fata",
            "modelare_cant_aluminiu",
            "debitare_spate",
            "finisaje_colantare_vopsire",
        }


# --- 25–26. letter body amounts non-regression vs letters-only geometry ---
@pytest.mark.asyncio
async def test_letter_body_line_amounts_stable_with_logos(cpp_service: CommercialPriceProposalService):
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
    with_logos = await cpp_service.build_preview(ROOT, quote_input=_two_logo_quote_input())
    assert letters is not None and with_logos is not None
    for code in ("debitare_fata", "modelare_cant_aluminiu", "debitare_spate"):
        a = next(line for line in letters.commercial_price_lines if line.code == code)
        b = next(line for line in with_logos.commercial_price_lines if line.code == code)
        assert a.quantity == b.quantity
        assert a.subtotal == b.subtotal


# --- 27. informational missing prices not conflated ---
@pytest.mark.asyncio
async def test_informational_led_watts_not_a_commercial_line(cpp_service: CommercialPriceProposalService, logo_seeded_db):
    payload = _two_logo_quote_input()
    record = await _persist_workspace(logo_seeded_db, payload)
    preview = await cpp_service.build_preview(ROOT, workspace_id=record.id, quote_input=payload)
    assert preview is not None
    assert not any("led_total_watts" in line.code for line in preview.commercial_price_lines)


# --- standalone logo not supported as CPP root ---
@pytest.mark.asyncio
async def test_logo_template_not_cpp_root(cpp_service: CommercialPriceProposalService):
    preview = await cpp_service.build_preview(LOGO, quote_input=_two_logo_quote_input())
    assert preview is None
