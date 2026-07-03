import json


def test_quotes_query_unsupported_regex_returns_400(auth_client):
    resp = auth_client.get(
        "/api/v1/entities/quotes",
        params={"query": json.dumps({"code": {"$regex": "STAGING_TEST_BUILD_26_25"}})},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["detail"]["error"] == "unsupported_query_operator"
    assert body["detail"]["operator"] == "$regex"
    assert "$eq" in body["detail"]["supported_operators"]


def test_quotes_query_equality_still_works(auth_client):
    created = auth_client.post(
        "/api/v1/entities/quotes",
        json={
            "code": "Q-QUERY-GUARD-26-34",
            "client_name": "STAGING_TEST_BUILD_26_34_CLIENT",
            "status": "draft",
            "version": 1,
        },
    )
    assert created.status_code == 201
    quote_id = created.json()["id"]

    resp = auth_client.get(
        "/api/v1/entities/quotes",
        params={"query": json.dumps({"id": quote_id})},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(item["id"] == quote_id for item in items)


def test_orders_query_unsupported_regex_returns_400(auth_client):
    resp = auth_client.get(
        "/api/v1/entities/orders",
        params={"query": json.dumps({"code": {"$regex": "ORD-"}})},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["detail"]["error"] == "unsupported_query_operator"
    assert body["detail"]["operator"] == "$regex"


def test_intake_query_unsupported_regex_returns_400(auth_client):
    resp = auth_client.get(
        "/api/v1/entities/intake_requests",
        params={"query": json.dumps({"code": {"$regex": "STAGING_TEST_BUILD_26_35"}})},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["detail"]["error"] == "unsupported_query_operator"
    assert body["detail"]["operator"] == "$regex"
    assert "$eq" in body["detail"]["supported_operators"]


def test_intake_query_equality_still_works(auth_client):
    created = auth_client.post(
        "/api/v1/entities/intake_requests",
        json={
            "code": "WI-QUERY-GUARD-26-35",
            "client_name": "STAGING_TEST_BUILD_26_35_CLIENT",
            "product_family": "print",
            "status": "ready_for_quote",
        },
    )
    assert created.status_code == 201
    intake_id = created.json()["id"]

    resp = auth_client.get(
        "/api/v1/entities/intake_requests",
        params={"query": json.dumps({"id": intake_id})},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(item["id"] == intake_id for item in items)


def test_inventory_materials_query_equality_still_works(auth_client):
    created = auth_client.post(
        "/api/v1/entities/inventory_materials",
        json={
            "code": "MAT-QUERY-GUARD-26-38",
            "name": "Query Guard Material",
            "category": "qa",
            "unit": "mp",
            "stock_current": 0,
            "stock_min": 0,
            "stock_max": 0,
            "unit_cost": 1.0,
            "status": "active",
        },
    )
    assert created.status_code == 201
    material_id = created.json()["id"]

    resp = auth_client.get(
        "/api/v1/entities/inventory_materials",
        params={"query": json.dumps({"id": material_id})},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(item["id"] == material_id for item in items)


def test_inventory_materials_query_unsupported_regex_returns_400(auth_client):
    resp = auth_client.get(
        "/api/v1/entities/inventory_materials",
        params={"query": json.dumps({"code": {"$regex": "MAT"}})},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["detail"]["error"] == "unsupported_query_operator"
    assert body["detail"]["operator"] == "$regex"
    assert "$eq" in body["detail"]["supported_operators"]


def test_inventory_materials_query_malformed_json_returns_400(auth_client):
    resp = auth_client.get(
        "/api/v1/entities/inventory_materials",
        params={"query": "{invalid"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid query JSON format"


def test_quote_from_intake_duplicate_guard_returns_409(auth_client):
    """Verify that second call to POST /from-intake/{intake_id} returns 409 conflict."""
    # Create intake in ready_for_quote status
    intake_resp = auth_client.post(
        "/api/v1/entities/intake_requests",
        json={
            "code": "WI-DUP-GUARD-26-36",
            "client_name": "STAGING_TEST_BUILD_26_36_CLIENT",
            "product_family": "print",
            "status": "ready_for_quote",
        },
    )
    assert intake_resp.status_code == 201
    intake_id = intake_resp.json()["id"]

    # First call: create draft quote from intake (should succeed)
    first_call = auth_client.post(f"/api/v1/entities/quotes/from-intake/{intake_id}")
    assert first_call.status_code == 201
    first_quote_id = first_call.json()["quote_id"]
    first_quote_code = first_call.json()["quote_code"]

    # Second call: attempt to create another draft quote from same intake (should fail)
    second_call = auth_client.post(f"/api/v1/entities/quotes/from-intake/{intake_id}")
    assert second_call.status_code == 409
    body = second_call.json()
    assert body["detail"]["error"] == "quote_already_exists_for_intake"
    assert body["detail"]["intake_id"] == intake_id
    assert body["detail"]["existing_quote_id"] == first_quote_id
    assert body["detail"]["existing_quote_code"] == first_quote_code


def test_quote_from_intake_no_duplicate_quote_created(auth_client):
    """Verify that second POST /from-intake call does not create a new quote."""
    # Create intake in ready_for_quote status
    intake_resp = auth_client.post(
        "/api/v1/entities/intake_requests",
        json={
            "code": "WI-COUNT-GUARD-26-36",
            "client_name": "STAGING_TEST_BUILD_26_36_CLIENT",
            "product_family": "print",
            "status": "ready_for_quote",
        },
    )
    assert intake_resp.status_code == 201
    intake_id = intake_resp.json()["id"]

    # Get initial quote count for this intake
    initial_list = auth_client.get(
        "/api/v1/entities/quotes",
        params={"query": json.dumps({"intake_id": intake_id})},
    )
    assert initial_list.status_code == 200
    initial_count = initial_list.json()["total"]

    # First call: create draft quote
    first_call = auth_client.post(f"/api/v1/entities/quotes/from-intake/{intake_id}")
    assert first_call.status_code == 201

    # Get quote count after first call (should be 1)
    after_first = auth_client.get(
        "/api/v1/entities/quotes",
        params={"query": json.dumps({"intake_id": intake_id})},
    )
    assert after_first.status_code == 200
    count_after_first = after_first.json()["total"]
    assert count_after_first == initial_count + 1

    # Second call: attempt duplicate (should fail with 409)
    second_call = auth_client.post(f"/api/v1/entities/quotes/from-intake/{intake_id}")
    assert second_call.status_code == 409

    # Get quote count after second call (should remain same as after first)
    after_second = auth_client.get(
        "/api/v1/entities/quotes",
        params={"query": json.dumps({"intake_id": intake_id})},
    )
    assert after_second.status_code == 200
    count_after_second = after_second.json()["total"]
    assert count_after_second == count_after_first
    assert count_after_second == initial_count + 1
