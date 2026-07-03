import uuid

import pytest
from sqlalchemy import func, select

from models.inventory_materials import Inventory_materials
from services.inventory_sheet_quality_audit import (
    InventorySheetQualityAuditItem,
    audit_inventory_material_record,
    audit_inventory_sheet_quality,
)


@pytest.mark.asyncio
async def test_audit_inventory_sheet_quality_no_mutation_empty(db_session):
    before_count = await db_session.scalar(select(func.count(Inventory_materials.id)))

    report = await audit_inventory_sheet_quality(db_session)

    after_count = await db_session.scalar(select(func.count(Inventory_materials.id)))
    assert before_count == after_count


@pytest.mark.asyncio
async def test_audit_valid_sheet_material():
    material = Inventory_materials(
        code="MAT-VALID-SHEET",
        name="Valid sheet material",
        category="panou_compozit",
        unit="mp",
        status="active",
        sheet_format_type="sheet",
        sheet_width=2000,
        sheet_height=1000,
        sheet_unit="mm",
        format_source="manual",
        format_verified=True,
    )

    audit_item = audit_inventory_material_record(material)

    assert audit_item.status == "valid"
    assert audit_item.issue_code is None
    assert audit_item.would_block_intake_assist is False
    assert audit_item.recommended_action == "N/A"


@pytest.mark.asyncio
async def test_audit_non_sheet_material_is_not_applicable():
    material = Inventory_materials(
        code="MAT-ROLL",
        name="Roll material",
        category="material",
        unit="ml",
        status="active",
        sheet_format_type="roll",
        sheet_unit="mm",
        format_source="supplier",
    )

    audit_item = audit_inventory_material_record(material)

    assert audit_item.status == "not_applicable"
    assert audit_item.issue_code is None
    assert audit_item.would_block_intake_assist is False


@pytest.mark.asyncio
async def test_audit_sheet_material_missing_unit():
    material = Inventory_materials(
        code="MAT-NO-UNIT",
        name="Sheet missing unit",
        category="panou_compozit",
        unit="sheet",
        status="active",
        sheet_format_type="sheet",
        sheet_width=2000,
        sheet_height=1000,
        sheet_unit=None,
    )

    audit_item = audit_inventory_material_record(material)

    assert audit_item.status == "invalid"
    assert audit_item.issue_code == "missing_configuration"
    assert audit_item.would_block_intake_assist is True


@pytest.mark.asyncio
async def test_audit_sheet_material_missing_dimensions():
    material = Inventory_materials(
        code="MAT-NO-DIMS",
        name="Sheet missing dimensions",
        category="panou_compozit",
        unit="sheet",
        status="active",
        sheet_format_type="sheet",
        sheet_unit="mm",
    )

    audit_item = audit_inventory_material_record(material)

    assert audit_item.status == "invalid"
    assert audit_item.issue_code == "missing_configuration"
    assert audit_item.would_block_intake_assist is True


@pytest.mark.asyncio
async def test_audit_sheet_material_invalid_unit():
    material = Inventory_materials(
        code="MAT-INVALID-UNIT",
        name="Sheet invalid unit",
        category="panou_compozit",
        unit="invalid_unit",
        status="active",
        sheet_format_type="sheet",
        sheet_width=2000,
        sheet_height=1000,
        sheet_unit="mm",
    )

    audit_item = audit_inventory_material_record(material)

    assert audit_item.status == "invalid"
    assert audit_item.issue_code in {"invalid_unit", "unexpected_shape"}
    assert audit_item.would_block_intake_assist is True


@pytest.mark.asyncio
async def test_audit_sheet_material_invalid_dimensions():
    material = Inventory_materials(
        code="MAT-INVALID-DIMS-ZERO",
        name="Sheet invalid dimensions",
        category="panou_compozit",
        unit="mp",
        status="active",
        sheet_format_type="sheet",
        sheet_width=0,
        sheet_height=1000,
        sheet_unit="mm",
    )

    audit_item = audit_inventory_material_record(material)

    assert audit_item.status == "invalid"
    assert audit_item.issue_code == "invalid_dimensions"
    assert audit_item.would_block_intake_assist is True


@pytest.mark.asyncio
async def test_audit_sheet_material_usable_exceeds_width():
    material = Inventory_materials(
        code="MAT-USABLE-VIOLATION",
        name="Sheet usable > width",
        category="panou_compozit",
        unit="mp",
        status="active",
        sheet_format_type="sheet",
        sheet_width=2000,
        sheet_height=1000,
        sheet_unit="mm",
        usable_width=2500,
    )

    audit_item = audit_inventory_material_record(material)

    assert audit_item.status == "invalid"
    assert audit_item.issue_code == "partial_payload"
    assert "usable_width > sheet_width" in audit_item.message
    assert audit_item.would_block_intake_assist is True


@pytest.mark.asyncio
async def test_audit_missing_required_field_code():
    material = Inventory_materials(
        code=None,
        name="Material without code",
        category="panou_compozit",
        unit="mp",
        status="active",
        sheet_format_type="sheet",
        sheet_width=2000,
        sheet_height=1000,
        sheet_unit="mm",
    )

    audit_item = audit_inventory_material_record(material)

    assert audit_item.status == "invalid"
    assert audit_item.issue_code == "missing_required_field"
    assert audit_item.would_block_intake_assist is True


@pytest.mark.asyncio
async def test_audit_missing_required_field_status():
    material = Inventory_materials(
        code="MAT-NO-STATUS",
        name="Material without status",
        category="panou_compozit",
        unit="mp",
        status=None,
        sheet_format_type="sheet",
        sheet_width=2000,
        sheet_height=1000,
        sheet_unit="mm",
    )

    audit_item = audit_inventory_material_record(material)

    assert audit_item.status == "invalid"
    assert audit_item.issue_code == "missing_required_field"
    assert audit_item.would_block_intake_assist is True


@pytest.mark.asyncio
async def test_audit_report_aggregates_counts(db_session):
    suffix = uuid.uuid4().hex[:8]
    codes = {
        "valid_1": f"MAT-VALID-1-{suffix}",
        "valid_2": f"MAT-VALID-2-{suffix}",
        "roll": f"MAT-ROLL-{suffix}",
        "invalid": f"MAT-INVALID-{suffix}",
    }

    db_session.add_all([
        Inventory_materials(
            code=codes["valid_1"],
            name="Valid 1",
            category="panou",
            unit="mp",
            status="active",
            sheet_format_type="sheet",
            sheet_width=2000,
            sheet_height=1000,
            sheet_unit="mm",
        ),
        Inventory_materials(
            code=codes["valid_2"],
            name="Valid 2",
            category="panou",
            unit="mp",
            status="active",
            sheet_format_type="sheet",
            sheet_width=3000,
            sheet_height=1500,
            sheet_unit="mm",
        ),
        Inventory_materials(
            code=codes["roll"],
            name="Roll",
            category="material",
            unit="ml",
            status="active",
            sheet_format_type="roll",
        ),
        Inventory_materials(
            code=codes["invalid"],
            name="Invalid",
            category="panou",
            unit="invalid",
            status="active",
            sheet_format_type="sheet",
            sheet_width=2000,
            sheet_height=1000,
            sheet_unit="mm",
        ),
    ])
    await db_session.commit()

    report = await audit_inventory_sheet_quality(db_session)
    by_code = {item.material_id: item for item in report.items}

    assert codes["valid_1"] in by_code
    assert codes["valid_2"] in by_code
    assert codes["roll"] in by_code
    assert codes["invalid"] in by_code

    assert by_code[codes["valid_1"]].status == "valid"
    assert by_code[codes["valid_2"]].status == "valid"
    assert by_code[codes["roll"]].status == "not_applicable"
    assert by_code[codes["invalid"]].status == "invalid"


@pytest.mark.asyncio
async def test_audit_no_mutation_during_report_generation(db_session):
    db_session.add(
        Inventory_materials(
            code="MAT-NO-MUTATION-TEST-UNIQUE",
            name="Before audit",
            category="panou_compozit",
            unit="mp",
            status="active",
            sheet_format_type="sheet",
            sheet_width=2000,
            sheet_height=1000,
            sheet_unit="mm",
        )
    )
    await db_session.commit()

    before_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == "MAT-NO-MUTATION-TEST-UNIQUE")
    )
    before_material = before_result.scalar_one()
    before_width = before_material.sheet_width
    before_height = before_material.sheet_height

    report = await audit_inventory_sheet_quality(db_session)

    after_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == "MAT-NO-MUTATION-TEST-UNIQUE")
    )
    after_material = after_result.scalar_one()
    after_width = after_material.sheet_width
    after_height = after_material.sheet_height

    assert before_width == after_width
    assert before_height == after_height
    assert report.total_records_checked >= 1


@pytest.mark.asyncio
async def test_audit_item_contains_recommended_action():
    material = Inventory_materials(
        code="MAT-MISSING-DIMS",
        name="Missing dimensions",
        category="panou_compozit",
        unit="mp",
        status="active",
        sheet_format_type="sheet",
        sheet_unit="mm",
    )

    audit_item = audit_inventory_material_record(material)

    assert audit_item.status == "invalid"
    assert audit_item.recommended_action != ""
    assert "sheet_width" in audit_item.recommended_action
