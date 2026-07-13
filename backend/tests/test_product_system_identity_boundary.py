from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from services.template_architecture_scope import (
    ACM_BOXED_MOUNTING_TEMPLATE_CODE,
    STRUCTURE_PREMOUNT_TEMPLATE_CODE,
    VOLUMETRIC_V2_TEMPLATE_CODE,
    require_canonical_template_code,
    resolve_template_identity,
)
from routers import (
    product_system_aggregate,
    product_system_cost_bom_preview,
    product_system_mini_modules,
    product_system_product_definition,
    quote_snapshot_v2,
)
from models.product_templates import Product_templates
from models.product_blueprint_dossier import ProductBlueprintDossier

FOCUS_TEMPLATES = (
    VOLUMETRIC_V2_TEMPLATE_CODE,
    ACM_BOXED_MOUNTING_TEMPLATE_CODE,
    STRUCTURE_PREMOUNT_TEMPLATE_CODE,
)

REQUEST_VARIANTS = (
    "canonical_mixed_case",
    "uppercase",
    "lowercase",
    "trimmed",
)


def _request_code(template_code: str, variant: str) -> str:
    if variant == "canonical_mixed_case":
        return template_code
    if variant == "uppercase":
        return template_code.upper()
    if variant == "lowercase":
        return template_code.lower()
    if variant == "trimmed":
        return f"  {template_code}  "
    raise ValueError(f"unknown variant: {variant}")


async def _seed_focus_template(session, template_code: str) -> None:
    existing = await session.execute(
        select(Product_templates).where(Product_templates.template_code == template_code)
    )
    existing_row = existing.scalar_one_or_none()
    if existing_row is not None:
        await session.execute(
            delete(ProductBlueprintDossier).where(
                ProductBlueprintDossier.template_id == existing_row.id
            )
        )
        await session.execute(
            delete(Product_templates).where(Product_templates.id == existing_row.id)
        )
        await session.commit()

    session.add(
        Product_templates(
            template_code=template_code,
            family_id="signage",
            family_name="Signage",
            description=f"Identity boundary seed for {template_code}",
            components_json="[]",
            operations_json="[]",
            required_materials_json="[]",
            active=True,
        )
    )
    await session.commit()


def _app() -> FastAPI:
    app = FastAPI()
    app.include_router(product_system_aggregate.router)
    app.include_router(product_system_product_definition.router)
    app.include_router(product_system_cost_bom_preview.router)
    app.include_router(product_system_mini_modules.router)
    app.include_router(quote_snapshot_v2.router)
    return app


def test_identity_resolution_canonical_and_formatting_normalization() -> None:
    res = resolve_template_identity(" tpl-volumetric-letters_v2 ")
    assert res.canonical_template_code == VOLUMETRIC_V2_TEMPLATE_CODE.upper()
    assert res.resolution_type == "canonical"
    assert res.legacy_alias_used is False


def test_identity_resolution_known_legacy_alias_is_explicit() -> None:
    res = resolve_template_identity("TPL-VOLUMETRIC-LETTERS")
    assert res.canonical_template_code == VOLUMETRIC_V2_TEMPLATE_CODE.upper()
    assert res.resolution_type == "legacy_read_bridge"
    assert res.legacy_alias_used is True


def test_identity_gate_rejects_legacy_alias_for_active_compilation() -> None:
    gate = require_canonical_template_code("TPL-VOLUMETRIC-LETTERS")
    assert gate.resolution_type == "rejected_alias"
    assert gate.canonical_template_code == VOLUMETRIC_V2_TEMPLATE_CODE.upper()


def test_identity_gate_accepts_canonical_templates_in_scope() -> None:
    for code in (
        VOLUMETRIC_V2_TEMPLATE_CODE,
        ACM_BOXED_MOUNTING_TEMPLATE_CODE,
        STRUCTURE_PREMOUNT_TEMPLATE_CODE,
    ):
        gate = require_canonical_template_code(code)
        assert gate.resolution_type == "canonical"
        assert gate.canonical_template_code == code.upper()


def test_product_system_compilation_routes_reject_legacy_alias() -> None:
    """
    These routes are active compilation requests; they must not accept legacy aliases.
    """
    client = TestClient(_app())

    # We only assert the identity boundary behavior (422 + canonicalization metadata),
    # not downstream DB-backed behavior.
    for url in (
        "/api/v1/product-system/aggregate/TPL-VOLUMETRIC-LETTERS",
        "/api/v1/product-system/product-definition/TPL-VOLUMETRIC-LETTERS",
        "/api/v1/product-system/cost-bom-preview/TPL-VOLUMETRIC-LETTERS",
        "/api/v1/product-system/quote-snapshot-v2/preview/TPL-VOLUMETRIC-LETTERS",
        "/api/v1/product-system/quote-snapshot-v2/freeze/TPL-VOLUMETRIC-LETTERS",
    ):
        resp = client.get(url) if "cost-bom-preview" in url or "aggregate" in url or "product-definition" in url else client.post(url, json={})
        assert resp.status_code == 422
        payload = resp.json().get("detail") or {}
        assert payload.get("error") == "template_identity_not_canonical"
        assert payload.get("canonical_template_code") == VOLUMETRIC_V2_TEMPLATE_CODE.upper()


@pytest.mark.parametrize("template_code", FOCUS_TEMPLATES)
@pytest.mark.parametrize("request_variant", REQUEST_VARIANTS)
def test_endpoint_aggregate_resolves_db_template(
    auth_client,
    db_fixture,
    template_code: str,
    request_variant: str,
) -> None:
    async def _seed() -> None:
        async with db_fixture.session_maker() as session:
            await _seed_focus_template(session, template_code)

    db_fixture.run(_seed())
    requested = _request_code(template_code, request_variant)
    resp = auth_client.get(f"/api/v1/product-system/aggregate/{requested}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["template_code"] == template_code


@pytest.mark.parametrize("template_code", (VOLUMETRIC_V2_TEMPLATE_CODE, ACM_BOXED_MOUNTING_TEMPLATE_CODE))
@pytest.mark.parametrize("request_variant", REQUEST_VARIANTS)
def test_endpoint_product_definition_resolves_db_template(
    auth_client,
    db_fixture,
    template_code: str,
    request_variant: str,
) -> None:
    async def _seed() -> None:
        async with db_fixture.session_maker() as session:
            await _seed_focus_template(session, template_code)

    db_fixture.run(_seed())
    requested = _request_code(template_code, request_variant)
    resp = auth_client.get(f"/api/v1/product-system/product-definition/{requested}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["template_code"] == template_code


@pytest.mark.parametrize("request_variant", REQUEST_VARIANTS)
def test_endpoint_product_definition_unavailable_for_premount_root(
    auth_client,
    db_fixture,
    request_variant: str,
) -> None:
    template_code = STRUCTURE_PREMOUNT_TEMPLATE_CODE

    async def _seed() -> None:
        async with db_fixture.session_maker() as session:
            await _seed_focus_template(session, template_code)

    db_fixture.run(_seed())
    requested = _request_code(template_code, request_variant)
    resp = auth_client.get(f"/api/v1/product-system/product-definition/{requested}")
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"] == "product_definition_preview_not_found"


def test_endpoint_mini_module_registry_non_empty_for_volumetric_v2(
    auth_client,
    db_fixture,
) -> None:
    async def _seed() -> None:
        async with db_fixture.session_maker() as session:
            await _seed_focus_template(session, VOLUMETRIC_V2_TEMPLATE_CODE)

    db_fixture.run(_seed())
    for requested in (
        VOLUMETRIC_V2_TEMPLATE_CODE,
        VOLUMETRIC_V2_TEMPLATE_CODE.upper(),
        f" {VOLUMETRIC_V2_TEMPLATE_CODE.lower()} ",
    ):
        resp = auth_client.get(
            f"/api/v1/product-system/mini-modules/by-template/{requested}"
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body["modules"]) > 0
        assert body["summary"]["template_code"] == VOLUMETRIC_V2_TEMPLATE_CODE

