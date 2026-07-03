from __future__ import annotations

import pytest
from sqlalchemy import delete, func, select

from models.product_families import Product_families
from models.product_template_module_links import ProductTemplateModuleLink
from models.product_templates import Product_templates
from services.product_template_availability_service import ProductTemplateAvailabilityService


LETTERS = "TPL-VOLUMETRIC-LETTERS_v2"
PREMOUNT = "TPL-METAL-PREMOUNT-STRUCTURE_v1"
VOLUM_ALUMINUM = "TPL-VOLUM-ALUMINIU_v1"
LOGO = "TPL-VOLUMETRIC-LOGO_v1"

LETTER_MODULES = [
    PREMOUNT,
    VOLUM_ALUMINUM,
    "TPL-VOLUMETRIC-FACE_v1",
    "TPL-VOLUMETRIC-BACK_v1",
    "TPL-VOLUMETRIC-LED_v1",
    "TPL-VOLUMETRIC-FINISH_v1",
]

LOGO_MODULES = [
    "TPL-VOLUMETRIC-LOGO-FACE_v1",
    "TPL-VOLUMETRIC-LOGO-RETURN_v1",
    "TPL-VOLUMETRIC-LOGO-BACK_v1",
    "TPL-VOLUMETRIC-LOGO-LIGHTING_v1",
    "TPL-VOLUMETRIC-LOGO-FINISH_v1",
    "TPL-VOLUMETRIC-LOGO-MOUNTING_v1",
]


async def _clear_product_system_rows(session):
    await session.execute(delete(ProductTemplateModuleLink))
    await session.execute(delete(Product_families))
    await session.execute(delete(Product_templates))
    await session.commit()


async def _seed_availability_fixture(session, *, include_letter_links: bool = True):
    await _clear_product_system_rows(session)
    session.add(
        Product_families(
            family_id="litere_volumetrice",
            label="Litere volumetrice",
            category="semnalistica",
            active=True,
            description="Fixture family",
        )
    )
    await session.flush()

    codes = [LETTERS, *LETTER_MODULES, LOGO, *LOGO_MODULES]
    rows: dict[str, Product_templates] = {}
    for code in codes:
        row = Product_templates(
            template_code=code,
            family_id="litere_volumetrice",
            family_name="Litere volumetrice",
            description=f"Fixture {code}",
            components_json="[]",
            operations_json="[]",
            required_materials_json="[]",
            active=True,
        )
        session.add(row)
        rows[code] = row
    await session.flush()

    link_specs: list[tuple[str, str]] = []
    if include_letter_links:
        link_specs.extend((LETTERS, code) for code in LETTER_MODULES)
    link_specs.extend((LOGO, code) for code in LOGO_MODULES)

    for idx, (parent_code, module_code) in enumerate(link_specs, start=1):
        session.add(
            ProductTemplateModuleLink(
                parent_template_id=rows[parent_code].id,
                parent_template_code=parent_code,
                module_template_id=rows[module_code].id,
                module_template_code=module_code,
                relation_type="required_module" if module_code != PREMOUNT else "optional_addon",
                trigger_field=f"trigger_{idx}",
                trigger_value_json="true",
                input_mapping_json="{}",
                default_values_json="{}",
                pricing_mode="separate_quote_line",
                execution_mode="linked_child_work",
                active=True,
            )
        )
    await session.commit()


def _by_code(items):
    return {item.template_code: item for item in items}


@pytest.mark.asyncio
async def test_availability_returns_fourteen_templates(db_session):
    await _seed_availability_fixture(db_session)
    response = await ProductTemplateAvailabilityService(db_session).list_availability()
    assert response.total == 14
    assert len(response.items) == 14


@pytest.mark.asyncio
async def test_letters_is_offerable_parent_with_modules(db_session):
    await _seed_availability_fixture(db_session)
    response = await ProductTemplateAvailabilityService(db_session).list_availability()
    item = _by_code(response.items)[LETTERS]
    assert item.quote_offerable is True
    assert item.is_parent is True
    assert item.has_modules is True
    assert item.status == "offerable"
    assert item.status_reason == "owner_valid_parent_template"
    assert set(LETTER_MODULES).issubset(set(item.module_codes))


@pytest.mark.asyncio
async def test_child_module_templates_are_runtime_only(db_session):
    await _seed_availability_fixture(db_session)
    response = await ProductTemplateAvailabilityService(db_session).list_availability()
    by_code = _by_code(response.items)
    for code in LETTER_MODULES:
        item = by_code[code]
        assert item.runtime_module is True
        assert item.quote_offerable is False
        assert item.status_reason == "runtime_module_only"


@pytest.mark.asyncio
async def test_frontend_only_volum_aluminum_does_not_become_offerable(db_session):
    await _seed_availability_fixture(db_session)
    response = await ProductTemplateAvailabilityService(db_session).list_availability()
    item = _by_code(response.items)[VOLUM_ALUMINUM]
    assert item.runtime_module is True
    assert item.quote_offerable is False


@pytest.mark.asyncio
async def test_offerable_only_filters_to_offerable_templates(db_session):
    await _seed_availability_fixture(db_session)
    response = await ProductTemplateAvailabilityService(db_session).list_availability(
        offerable_only=True
    )
    assert [item.template_code for item in response.items] == [LETTERS]
    assert response.offerable_count == 1


def test_endpoint_does_not_modify_db(auth_client, db_fixture):
    async def _seed_and_count():
        async with db_fixture.session_maker() as session:
            await _seed_availability_fixture(session)
            return (await session.execute(select(func.count(Product_templates.id)))).scalar_one()

    async def _count_templates():
        async with db_fixture.session_maker() as session:
            return (await session.execute(select(func.count(Product_templates.id)))).scalar_one()

    before = db_fixture.run(_seed_and_count())
    response = auth_client.get("/api/v1/product-system/template-availability?offerable_only=true")
    after = db_fixture.run(_count_templates())
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["template_code"] == LETTERS
    assert before == after == 14


@pytest.mark.asyncio
async def test_missing_links_mark_owner_valid_parent_not_offerable(db_session):
    await _seed_availability_fixture(db_session, include_letter_links=False)
    response = await ProductTemplateAvailabilityService(db_session).list_availability()
    item = _by_code(response.items)[LETTERS]
    assert item.quote_offerable is False
    assert item.status_reason == "missing_required_modules"
