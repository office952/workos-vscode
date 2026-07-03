from __future__ import annotations

from datetime import datetime, timezone

import pytest

from services.inventory_materials_admin_service import (
    InventoryMaterialValidationError,
    validate_status_and_cost,
)


def test_active_requires_full_pricing_contract_fields():
    with pytest.raises(InventoryMaterialValidationError):
        validate_status_and_cost("active", 10.0, None, 19.0, datetime.now(timezone.utc))

    with pytest.raises(InventoryMaterialValidationError):
        validate_status_and_cost("active", 10.0, "RON", None, datetime.now(timezone.utc))

    with pytest.raises(InventoryMaterialValidationError):
        validate_status_and_cost("active", 10.0, "RON", 19.0, None)


def test_active_rejects_out_of_bounds_vat():
    with pytest.raises(InventoryMaterialValidationError):
        validate_status_and_cost("active", 10.0, "RON", -1.0, datetime.now(timezone.utc))
    with pytest.raises(InventoryMaterialValidationError):
        validate_status_and_cost("active", 10.0, "RON", 101.0, datetime.now(timezone.utc))


def test_missing_price_allows_null_price_fields():
    validate_status_and_cost("missing_price", None, None, None, None)
