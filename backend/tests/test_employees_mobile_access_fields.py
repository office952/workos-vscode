"""Employees API — mobile access enrichment on list/detail responses."""

from __future__ import annotations

import pytest
from models.auth import User
from models.employees import Employees


@pytest.mark.asyncio
async def test_list_employees_exposes_mobile_access_fields(db_session, auth_client):
    user = User(
        id="mobile-worker-api",
        email="mobile-worker-api@workos.test",
        name="Mobile Worker API",
        role="employee_mobile",
    )
    db_session.add(user)
    await db_session.flush()

    linked = Employees(
        name="Linked Worker",
        status="active",
        employee_type="productive",
        user_id=user.id,
    )
    unlinked = Employees(
        name="Unlinked Worker",
        status="active",
        employee_type="productive",
        user_id=None,
    )
    db_session.add(linked)
    db_session.add(unlinked)
    await db_session.commit()

    response = auth_client.get("/api/v1/entities/employees")

    assert response.status_code == 200
    payload = response.json()
    by_name = {item["name"]: item for item in payload["items"]}

    linked_item = by_name["Linked Worker"]
    assert linked_item["user_id"] == user.id
    assert linked_item["auth_email"] == user.email
    assert linked_item["auth_role"] == "employee_mobile"
    assert linked_item["is_linked_to_user"] is True
    assert linked_item["has_mobile_access"] is True

    unlinked_item = by_name["Unlinked Worker"]
    assert unlinked_item["user_id"] is None
    assert unlinked_item["is_linked_to_user"] is False
    assert unlinked_item["has_mobile_access"] is False
