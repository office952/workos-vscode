from main import app


def test_route_inventory_contains_canonical_and_legacy_paths():
    routes = {(getattr(route, "path", ""), tuple(sorted(getattr(route, "methods", set())))) for route in app.routes}

    assert any(path == "/api/v1/product-system/output-blocks/preview" and "POST" in methods for path, methods in routes)
    assert any(path == "/api/v1/product-system/output-blocks/render-preview" and "POST" in methods for path, methods in routes)
    assert any(path == "/api/v1/entities/quotes/{quote_id}/output-blocks-preview" and "GET" in methods for path, methods in routes)


def test_canonical_preview_shape_differs_from_legacy_render_preview(auth_client):
    canonical_resp = auth_client.post(
        "/api/v1/product-system/output-blocks/preview",
        json={
            "block_ids": ["route-boundary-missing-id"],
            "context": "quote_preview",
            "source_payload": {"identity": {"product_name": "x"}, "materials": {"main_material": "y"}},
        },
    )
    assert canonical_resp.status_code == 200
    canonical_body = canonical_resp.json()
    assert canonical_body.get("preview_only") is True
    assert "rendered_blocks" in canonical_body
    assert "warnings" in canonical_body
    assert "blockers" in canonical_body
    assert "persisted" not in canonical_body

    legacy_resp = auth_client.post(
        "/api/v1/product-system/output-blocks/render-preview",
        json={},
    )
    assert legacy_resp.status_code == 422
    legacy_detail = legacy_resp.json().get("detail", {})
    assert legacy_detail.get("persisted") is False
    assert "preview_only" not in legacy_detail


def test_legacy_quote_bridge_is_not_canonical_contract(auth_client):
    legacy_quote_bridge_resp = auth_client.get("/api/v1/entities/quotes/999999/output-blocks-preview")
    assert legacy_quote_bridge_resp.status_code == 404
    detail = legacy_quote_bridge_resp.json().get("detail", {})
    assert detail.get("persisted") is False
    assert "preview_only" not in detail
