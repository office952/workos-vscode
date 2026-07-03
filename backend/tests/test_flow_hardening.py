"""
Sprint #10 — Flow Hardening tests.

Locks in Option B (explicit contract via strict validation, no new DTOs):

    A quote MUST block — and the /price endpoint MUST return HTTP 422 —
    when any of the following required fields are missing from the
    combined (product_template, user_config) request:

        - family            -> product_invalid:product_type
        - quantity          -> product_invalid:quantity
        - dimensions        -> product_invalid:dimensions

    ProductDefinition is built EXCLUSIVELY at quote-time (via
    QuoteOrchestrator -> ProductSystemService). Intake remains pure CRUD.
"""

from __future__ import annotations

import json
import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from services.product_system_service import ProductSystemService  # noqa: E402
from services.quote_orchestrator import QuoteOrchestrator  # noqa: E402


def _template_with_family() -> dict:
    return {
        "id": 1,
        "template_code": "TOTEM-STD",
        "family_id": "totemuri_pyloni",
        "family_name": "Totemuri / Pyloni",
        "components_json": json.dumps(["Cadru metalic"]),
        "operations_json": json.dumps(
            [
                {
                    "code": "ASM",
                    "name": "Asamblare",
                    "workcenter": "assembly",
                    "estimatedMinutes": 60,
                    "sequence": 1,
                }
            ]
        ),
        "required_materials_json": json.dumps(
            [{"materialCode": "MAT-ACP-3", "name": "ACP 3mm alb", "quantity": 2, "unit": "sqm"}]
        ),
    }


def _template_without_family() -> dict:
    t = _template_with_family()
    t["family_id"] = ""
    t["family_name"] = ""
    return t


def _valid_user_config() -> dict:
    return {
        "quantity": 2,
        "dimensions": {"width_mm": 1000, "height_mm": 3000, "depth_mm": 300},
    }


# ---------------------------------------------------------------------------
# ProductSystemService — unit level
# ---------------------------------------------------------------------------
class TestProductSystemStrictFamily(unittest.TestCase):
    def test_missing_family_marks_product_invalid(self):
        svc = ProductSystemService()
        pd = svc.build_product_definition(_template_without_family(), _valid_user_config())
        self.assertFalse(pd.validation.is_valid)
        self.assertIn("product_type", pd.validation.missing_fields)


class TestProductSystemStrictQuantity(unittest.TestCase):
    def test_missing_quantity_key_blocks(self):
        svc = ProductSystemService()
        pd = svc.build_product_definition(
            _template_with_family(),
            {"dimensions": {"width_mm": 1000, "height_mm": 3000}},
        )
        self.assertFalse(pd.validation.is_valid)
        self.assertIn("quantity", pd.validation.missing_fields)

    def test_zero_quantity_blocks(self):
        svc = ProductSystemService()
        pd = svc.build_product_definition(
            _template_with_family(),
            {"quantity": 0, "dimensions": {"width_mm": 1000, "height_mm": 3000}},
        )
        self.assertFalse(pd.validation.is_valid)
        self.assertIn("quantity", pd.validation.missing_fields)

    def test_negative_quantity_blocks(self):
        svc = ProductSystemService()
        pd = svc.build_product_definition(
            _template_with_family(),
            {"quantity": -5, "dimensions": {"width_mm": 1000, "height_mm": 3000}},
        )
        self.assertFalse(pd.validation.is_valid)
        self.assertIn("quantity", pd.validation.missing_fields)

    def test_non_numeric_quantity_blocks(self):
        svc = ProductSystemService()
        pd = svc.build_product_definition(
            _template_with_family(),
            {"quantity": "abc", "dimensions": {"width_mm": 1000, "height_mm": 3000}},
        )
        self.assertFalse(pd.validation.is_valid)
        self.assertIn("quantity", pd.validation.missing_fields)


class TestProductSystemStrictDimensions(unittest.TestCase):
    def test_missing_dimensions_blocks(self):
        svc = ProductSystemService()
        pd = svc.build_product_definition(
            _template_with_family(),
            {"quantity": 2},
        )
        self.assertFalse(pd.validation.is_valid)
        self.assertIn("dimensions", pd.validation.missing_fields)

    def test_zero_width_and_height_blocks(self):
        svc = ProductSystemService()
        pd = svc.build_product_definition(
            _template_with_family(),
            {
                "quantity": 2,
                "dimensions": {"width_mm": 0, "height_mm": 0, "depth_mm": 300},
            },
        )
        self.assertFalse(pd.validation.is_valid)
        self.assertIn("dimensions", pd.validation.missing_fields)

    def test_width_only_is_enough(self):
        svc = ProductSystemService()
        pd = svc.build_product_definition(
            _template_with_family(),
            {"quantity": 2, "dimensions": {"width_mm": 1000}},
        )
        self.assertNotIn("dimensions", pd.validation.missing_fields)

    def test_height_only_is_enough(self):
        svc = ProductSystemService()
        pd = svc.build_product_definition(
            _template_with_family(),
            {"quantity": 2, "dimensions": {"height_mm": 1000}},
        )
        self.assertNotIn("dimensions", pd.validation.missing_fields)


# ---------------------------------------------------------------------------
# QuoteOrchestrator — integration level (covers router mapping to 422)
# ---------------------------------------------------------------------------
class TestOrchestratorBlocksOnMissingFamily(unittest.TestCase):
    def test_blocked_with_product_invalid_product_type(self):
        snap = QuoteOrchestrator().build_snapshot(
            product_template=_template_without_family(),
            user_config=_valid_user_config(),
        )
        self.assertEqual(snap.status, "blocked")
        self.assertIn("product_invalid:product_type", snap.blocked_reasons)


class TestOrchestratorBlocksOnMissingQuantity(unittest.TestCase):
    def test_blocked_with_product_invalid_quantity(self):
        snap = QuoteOrchestrator().build_snapshot(
            product_template=_template_with_family(),
            user_config={"dimensions": {"width_mm": 1000, "height_mm": 3000}},
        )
        self.assertEqual(snap.status, "blocked")
        self.assertIn("product_invalid:quantity", snap.blocked_reasons)


class TestOrchestratorBlocksOnMissingDimensions(unittest.TestCase):
    def test_blocked_with_product_invalid_dimensions(self):
        snap = QuoteOrchestrator().build_snapshot(
            product_template=_template_with_family(),
            user_config={"quantity": 2},
        )
        self.assertEqual(snap.status, "blocked")
        self.assertIn("product_invalid:dimensions", snap.blocked_reasons)


class TestOrchestratorBlocksOnMultipleMissing(unittest.TestCase):
    def test_all_three_reasons_surface_together(self):
        snap = QuoteOrchestrator().build_snapshot(
            product_template=_template_without_family(),
            user_config={},
        )
        self.assertEqual(snap.status, "blocked")
        reasons = set(snap.blocked_reasons)
        self.assertIn("product_invalid:product_type", reasons)
        self.assertIn("product_invalid:quantity", reasons)
        self.assertIn("product_invalid:dimensions", reasons)


# ---------------------------------------------------------------------------
# Persistence guard on /price — Sprint #10 Round 4
# ---------------------------------------------------------------------------
# If any commercial field on a `priced` snapshot is None when the router
# reaches the persistence block, the router MUST fail with HTTP 422
# {error: "invalid_quote_snapshot", missing_field: <path>} and MUST NOT
# fall back to 0.  This locks FIX 2 Round 4: no `or 0`/`or None`/`or []`
# fallbacks in `routers/quotes.py`, `routers/orders.py`,
# `services/order_snapshot_service.py`.

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from core.database import get_db  # noqa: E402
from dependencies.auth import get_current_user  # noqa: E402
from schemas.auth import UserResponse  # noqa: E402
from data_models.product_contracts import (  # noqa: E402
    QuoteCalculationSnapshot,
    QuotePrice,
    QuotePricing,
)
from routers.quotes import router as quotes_router  # noqa: E402
import services.quote_orchestrator as quote_orchestrator_module  # noqa: E402
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


def _build_priced_snapshot_with_none(missing_field_attr_path: str) -> QuoteCalculationSnapshot:
    """Build a `priced` snapshot and force exactly one commercial field to None."""
    snap = QuoteCalculationSnapshot(
        pricing=QuotePricing(margin_pct=25.0, discount_pct=0.0, vat_pct=19.0),
        price=QuotePrice(net=1000.0, gross=1190.0, final=1190.0),
        status="priced",
        blocked_reasons=[],
    )
    root, attr = missing_field_attr_path.split(".", 1)
    setattr(getattr(snap, root), attr, None)
    return snap


class _FakeOrchestrator:
    """Drop-in orchestrator that returns a pre-built snapshot unchanged."""

    def __init__(self, snapshot: QuoteCalculationSnapshot) -> None:
        self._snapshot = snapshot

    def build_snapshot(self, **_kwargs) -> QuoteCalculationSnapshot:
        return self._snapshot


class _FakeOrchestratorClass:
    """Drop-in class replacement for QuoteOrchestrator that supports
    both direct instantiation and the async `create_with_registry` factory."""

    def __init__(self, snapshot: QuoteCalculationSnapshot) -> None:
        self._orchestrator = _FakeOrchestrator(snapshot)

    @classmethod
    def for_snapshot(cls, snapshot: QuoteCalculationSnapshot):
        """Create a fake class that mimics QuoteOrchestrator interface."""
        class _Cls:
            def __init__(self, *a, **kw):
                self._snapshot = snapshot

            @classmethod
            async def create_with_registry(cls, **_kw):
                return _FakeOrchestrator(snapshot)

            def build_snapshot(self, **_kwargs):
                return snapshot

        return _Cls


class TestQuotesPersistenceGuard(unittest.TestCase):
    """Verifies `routers/quotes.py` persistence guard (Round 4).

    Uses a monkey-patched `QuoteOrchestrator` so the router receives a
    `priced` snapshot with exactly one commercial field set to None.
    The router MUST respond 422 with the field path — no `or 0` fallback.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.db = IsolatedDBFixture(prefix="mgx_flowhard_")
        cls.db.setup()

        async def _override_get_db():
            async with cls.db.session_maker() as session:
                yield session

        async def _override_get_current_user():
            return UserResponse(
                id="test-flowhard-user",
                email="flowhard@example.com",
                name="Test FlowHard User",
                role="admin",
                last_login=None,
            )

        cls.app = FastAPI()
        cls.app.include_router(quotes_router)
        cls.app.dependency_overrides[get_db] = _override_get_db
        cls.app.dependency_overrides[get_current_user] = _override_get_current_user
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.client.close()
        except Exception:
            pass
        cls.db.teardown()

    def _call_price_with_forced_none(self, attr_path: str) -> dict:
        """Force the orchestrator to return a priced snapshot with
        `attr_path` = None, POST /price, and return the parsed JSON detail."""
        snap = _build_priced_snapshot_with_none(attr_path)
        original = quote_orchestrator_module.QuoteOrchestrator
        fake_cls = _FakeOrchestratorClass.for_snapshot(snap)
        quote_orchestrator_module.QuoteOrchestrator = fake_cls
        try:
            # Re-import into routers.quotes namespace too.
            import routers.quotes as quotes_router_module
            quotes_router_module.QuoteOrchestrator = fake_cls
            resp = self.client.post(
                "/api/v1/entities/quotes/price",
                json={
                    "product_template": {"family_id": "totem", "family_name": "Totem"},
                    "user_config": {
                        "quantity": 1,
                        "dimensions": {"width_mm": 1000, "height_mm": 1000},
                    },
                    "client_name": "ACME",
                },
            )
        finally:
            quote_orchestrator_module.QuoteOrchestrator = original
            import routers.quotes as quotes_router_module
            quotes_router_module.QuoteOrchestrator = original
        self.assertEqual(resp.status_code, 422, resp.text)
        return resp.json()["detail"]

    def test_guard_blocks_on_missing_price_net(self):
        detail = self._call_price_with_forced_none("price.net")
        self.assertEqual(detail["error"], "invalid_quote_snapshot")
        self.assertEqual(detail["missing_field"], "snapshot.price.net")

    def test_guard_blocks_on_missing_price_gross(self):
        detail = self._call_price_with_forced_none("price.gross")
        self.assertEqual(detail["error"], "invalid_quote_snapshot")
        self.assertEqual(detail["missing_field"], "snapshot.price.gross")

    def test_guard_blocks_on_missing_margin_pct(self):
        detail = self._call_price_with_forced_none("pricing.margin_pct")
        self.assertEqual(detail["error"], "invalid_quote_snapshot")
        self.assertEqual(detail["missing_field"], "snapshot.pricing.margin_pct")

    def test_guard_blocks_on_missing_discount_pct(self):
        detail = self._call_price_with_forced_none("pricing.discount_pct")
        self.assertEqual(detail["error"], "invalid_quote_snapshot")
        self.assertEqual(detail["missing_field"], "snapshot.pricing.discount_pct")

    def test_guard_blocks_on_missing_vat_pct(self):
        detail = self._call_price_with_forced_none("pricing.vat_pct")
        self.assertEqual(detail["error"], "invalid_quote_snapshot")
        self.assertEqual(detail["missing_field"], "snapshot.pricing.vat_pct")


if __name__ == "__main__":
    unittest.main()