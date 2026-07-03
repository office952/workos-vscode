import pytest

from models.inventory_materials import Inventory_materials
from services.inventory_sheet_service import (
    InventorySheetContractError,
    build_inventory_sheet_payload,
)
from services.inventory_sheet_format import compute_sheet_fit_status, validate_sheet_format_payload


@pytest.mark.asyncio
async def test_inventory_entity_create_persists_sheet_format_fields(auth_client):
    resp = auth_client.post(
        "/api/v1/entities/inventory_materials",
        json={
            "code": "MAT-SHEET-CONTRACT-1",
            "name": "Sheet Contract Material",
            "category": "panou_compozit",
            "unit": "sheet",
            "status": "active",
            "unit_cost": 10.0,
            "sheet_format_type": "sheet",
            "sheet_width": 2000,
            "sheet_height": 1000,
            "sheet_unit": "mm",
            "usable_width": 1950,
            "usable_height": 980,
            "sheet_thickness": 3,
            "sheet_thickness_unit": "mm",
            "format_source": "manual",
            "format_verified": True,
            "format_notes": "measured in warehouse",
        },
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["sheet_format_type"] == "sheet"
    assert body["sheet_width"] == 2000
    assert body["sheet_height"] == 1000
    assert body["sheet_unit"] == "mm"
    assert body["usable_width"] == 1950
    assert body["usable_height"] == 980
    assert body["format_verified"] is True


@pytest.mark.asyncio
async def test_inventory_entity_update_rejects_invalid_sheet_constraints(auth_client):
    create_resp = auth_client.post(
        "/api/v1/entities/inventory_materials",
        json={
            "code": "MAT-SHEET-CONTRACT-2",
            "name": "Sheet Contract Material 2",
            "category": "panou_compozit",
            "unit": "sheet",
            "sheet_format_type": "sheet",
            "sheet_width": 1000,
            "sheet_height": 500,
            "sheet_unit": "mm",
        },
    )
    assert create_resp.status_code == 201
    obj_id = create_resp.json()["id"]

    update_resp = auth_client.put(
        f"/api/v1/entities/inventory_materials/{obj_id}",
        json={
            "usable_width": 1200,
        },
    )
    assert update_resp.status_code == 400
    assert "usable_width" in str(update_resp.json()["detail"]).lower()


@pytest.mark.asyncio
async def test_validate_sheet_format_payload_rejects_invalid_values():
    with pytest.raises(ValueError):
        validate_sheet_format_payload(
            {
                "sheet_format_type": "sheet",
                "sheet_width": 1000,
                "sheet_height": 500,
                "sheet_unit": "inch",
            }
        )

    with pytest.raises(ValueError):
        validate_sheet_format_payload(
            {
                "sheet_format_type": "sheet",
                "sheet_width": 1000,
                "sheet_height": 500,
                "sheet_unit": "mm",
                "usable_width": 1200,
            }
        )


@pytest.mark.asyncio
async def test_compute_sheet_fit_status_matrix():
    fits = compute_sheet_fit_status(
        piece_width=1000,
        piece_height=500,
        piece_unit="mm",
        sheet_width=2000,
        sheet_height=1000,
        sheet_unit="mm",
        usable_width=None,
        usable_height=None,
        rotation_allowed=True,
    )
    assert fits.fit_status == "fits"

    rotated = compute_sheet_fit_status(
        piece_width=1000,
        piece_height=800,
        piece_unit="mm",
        sheet_width=900,
        sheet_height=1200,
        sheet_unit="mm",
        usable_width=None,
        usable_height=None,
        rotation_allowed=True,
    )
    assert rotated.fit_status == "fits_rotated"

    not_fit = compute_sheet_fit_status(
        piece_width=1000,
        piece_height=800,
        piece_unit="mm",
        sheet_width=600,
        sheet_height=400,
        sheet_unit="mm",
        usable_width=None,
        usable_height=None,
        rotation_allowed=True,
    )
    assert not_fit.fit_status == "does_not_fit"

    unknown = compute_sheet_fit_status(
        piece_width=1000,
        piece_height=800,
        piece_unit="unknown",
        sheet_width=600,
        sheet_height=400,
        sheet_unit="mm",
        usable_width=None,
        usable_height=None,
        rotation_allowed=True,
    )
    assert unknown.fit_status == "unknown"


def test_build_inventory_sheet_payload_valid_contract_shape():
    payload = build_inventory_sheet_payload(
        materials=[
            Inventory_materials(
                code="MAT-CONTRACT-OK",
                name="Material OK",
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
        ],
        dimensions={"width": 1000, "height": 500, "unit": "mm"},
        constraints={"rotation_allowed": True},
    )

    assert payload["source"] == "backend"
    assert payload["assist_available"] is True
    assert payload["blockers"] == []
    assert list(payload.keys()) == [
        "source",
        "assist_available",
        "items",
        "warnings",
        "blockers",
        "contract_version",
    ]


def test_build_inventory_sheet_payload_empty_rows_contract_shape():
    payload = build_inventory_sheet_payload(materials=[], dimensions=None, constraints={"rotation_allowed": True})

    assert payload["assist_available"] is False
    assert payload["items"] == []
    assert payload["blockers"]


def test_build_inventory_sheet_payload_rejects_missing_required_field():
    with pytest.raises(InventorySheetContractError) as exc:
        build_inventory_sheet_payload(
            materials=[
                Inventory_materials(
                    code="MAT-MISSING-DIMS",
                    name="Material invalid",
                    category="panou_compozit",
                    unit="sheet",
                    status="active",
                    sheet_format_type="sheet",
                    sheet_unit="mm",
                    format_source="manual",
                )
            ],
            dimensions={"width": 1000, "height": 500, "unit": "mm"},
            constraints={"rotation_allowed": True},
        )

    assert exc.value.code == "missing_required_field"


def test_build_inventory_sheet_payload_rejects_wrong_field_type():
    with pytest.raises(InventorySheetContractError) as exc:
        build_inventory_sheet_payload(
            materials=[
                Inventory_materials(
                    code="MAT-TYPE",
                    name="Material type",
                    category="panou_compozit",
                    unit="sheet",
                    status="active",
                    sheet_format_type="sheet",
                    sheet_width=2000,
                    sheet_height=1000,
                    sheet_unit="mm",
                    format_source="manual",
                )
            ],
            dimensions={"width": 1000, "height": 500, "unit": "mm"},
            constraints={"rotation_allowed": "yes"},
        )

    assert exc.value.code == "invalid_type"
