from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

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
    product_system_product_definition,
    quote_snapshot_v2,
)


def _app() -> FastAPI:
    app = FastAPI()
    app.include_router(product_system_aggregate.router)
    app.include_router(product_system_product_definition.router)
    app.include_router(product_system_cost_bom_preview.router)
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

