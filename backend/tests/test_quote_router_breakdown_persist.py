"""Sprint #18.5 — Quote router: persist component_breakdown into `line_items`.

These tests lock the router-level serialization contract without touching
the DB layer or the rest of the stack. They exercise the hook that was
added to `routers/quotes.py` directly via a stub service, verifying the
exact JSON shape written to the `line_items` column for every combination
of inputs:

1. Quote ierarhic (v2 snapshot, breakdown present)   → Shape B wrapper.
2. Quote flat legacy (v1 snapshot, no breakdown)     → Shape A (byte-for-byte
                                                        identical pre-sprint).
3. Quote ierarhic with warning                       → Shape B + cost_warnings.
4. Quote pre-sprint (snapshot without v2 attribute)  → Shape A, zero regression.

All tests use `httpx.AsyncClient` against a FastAPI app that mounts only
the quotes router, with `QuotesService.create` monkey-patched to capture
the persisted row instead of touching the database.

No cost math is performed in this layer — the orchestrator is also
patched to return a deterministic snapshot with pre-set dynamic
attributes.  That isolation is deliberate: these tests are about the
router serialization contract only.
"""

from __future__ import annotations

import json
import unittest
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import quotes as quotes_router


# ---------------------------------------------------------------------------
# Minimal snapshot fixture that mirrors the contract surface the router
# touches.  We intentionally keep this tiny — only what `price_quote` reads.
# ---------------------------------------------------------------------------


@dataclass
class _Pricing:
    margin_pct: float = 20.0
    discount_pct: float = 0.0
    vat_pct: float = 19.0


@dataclass
class _Price:
    net: float = 100.0
    gross: float = 119.0
    final: float = 119.0


@dataclass
class _CostResult:
    total_cost: float = 80.0
    breakdown: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class _ProductDef:
    code: str = "PROD-TEST"
    name: str = "Test Product"


@dataclass
class _FakeSnapshot:
    """Stands in for QuoteCalculationSnapshot in these router tests."""

    status: str = "priced"
    blocked_reasons: List[str] = field(default_factory=list)
    price: _Price = field(default_factory=_Price)
    pricing: _Pricing = field(default_factory=_Pricing)
    cost_result: _CostResult = field(default_factory=_CostResult)
    product_definition: _ProductDef = field(default_factory=_ProductDef)

    def to_dict(self) -> Dict[str, Any]:
        # Match the shape of asdict() on the real snapshot: a plain dict.
        # The router dumps this verbatim in Shape A mode.
        return {
            "status": self.status,
            "blocked_reasons": list(self.blocked_reasons),
            "price": {
                "net": self.price.net,
                "gross": self.price.gross,
                "final": self.price.final,
            },
            "pricing": {
                "margin_pct": self.pricing.margin_pct,
                "discount_pct": self.pricing.discount_pct,
                "vat_pct": self.pricing.vat_pct,
            },
            "cost_result": {
                "total_cost": self.cost_result.total_cost,
                "breakdown": list(self.cost_result.breakdown),
            },
            "product_definition": {
                "code": self.product_definition.code,
                "name": self.product_definition.name,
            },
        }


def _make_breakdown() -> List[Dict[str, Any]]:
    """A non-empty, realistic component breakdown payload."""
    return [
        {
            "component_name": "Panel",
            "component_type": "panel",
            "material_cost": 30.0,
            "operation_cost": 12.5,
            "total_component_cost": 42.5,
            "materials": [
                {"name": "Bond 4mm", "qty": 1.2, "unit_price": 25.0, "total": 30.0}
            ],
            "operations": [
                {"name": "CNC cut", "minutes": 15, "rate": 50.0, "total": 12.5}
            ],
        },
        {
            "component_name": "InnerFrame",
            "component_type": "frame",
            "material_cost": 20.0,
            "operation_cost": 5.0,
            "total_component_cost": 25.0,
            "materials": [],
            "operations": [],
        },
    ]


# ---------------------------------------------------------------------------
# App + service stub wiring.
# ---------------------------------------------------------------------------


class _CapturedCall:
    """Records the payload seen by QuotesService.create()."""

    def __init__(self) -> None:
        self.last_payload: Optional[Dict[str, Any]] = None

    def reset(self) -> None:
        self.last_payload = None


_captured = _CapturedCall()


class _StubQuoteObj:
    id = "stub-quote-id"


async def _fake_create(self, data: Dict[str, Any]):  # noqa: D401
    _captured.last_payload = data
    return _StubQuoteObj()


def _build_app() -> FastAPI:
    """Mount the real quotes router with auth overridden."""
    from dependencies.auth import get_current_user
    from schemas.auth import UserResponse

    app = FastAPI()
    app.include_router(quotes_router.router)

    # Override auth dependency so tests don't need a real JWT token.
    async def _fake_user():
        return UserResponse(
            id="test-user-id",
            email="test@example.com",
            name="Test User",
            role="admin",
            last_login=None,
        )

    app.dependency_overrides[get_current_user] = _fake_user
    return app


# The real router lives under /api/v1/entities/quotes and the pricing
# endpoint returns HTTP 201. The QuotePriceRequest model accepts optional
# product_template / user_config / pricing dicts — the orchestrator is
# mocked anyway, so the body only needs to satisfy the pydantic model.
_PRICE_URL = "/api/v1/entities/quotes/price"
_EXPECTED_STATUS = 201


def _post_price(app: FastAPI, snapshot: _FakeSnapshot) -> Any:
    """Hit POST /api/v1/entities/quotes/price with a minimal payload.

    Patches QuoteOrchestrator.create_with_registry to return a mock
    orchestrator whose build_snapshot() yields the given snapshot.
    Also patches QuotesService.create to capture the persisted payload.
    """
    mock_orchestrator = AsyncMock()
    mock_orchestrator.build_snapshot = lambda **kwargs: snapshot

    with patch.object(
        quotes_router.QuoteOrchestrator,
        "create_with_registry",
        new=AsyncMock(return_value=mock_orchestrator),
    ), patch.object(quotes_router.QuotesService, "create", new=_fake_create):
        client = TestClient(app)
        return client.post(
            _PRICE_URL,
            json={
                "client_name": "ACME SRL",
                "code": "Q-TEST-001",
                "product_template": {"code": "PROD-TEST"},
                "user_config": {},
                "pricing": {"margin_pct": 20, "discount_pct": 0, "vat_pct": 19},
            },
        )


# ---------------------------------------------------------------------------
# Tests.
# ---------------------------------------------------------------------------


class TestQuoteRouterBreakdownPersist(unittest.TestCase):
    """Router-level serialization contract for `line_items`."""

    def setUp(self) -> None:
        _captured.reset()

    # ---- 1. Hierarchical v2 quote → Shape B wrapper ---------------------
    def test_hierarchical_quote_writes_shape_b(self) -> None:
        snap = _FakeSnapshot()
        setattr(snap, "component_breakdown_json", json.dumps(_make_breakdown()))
        setattr(snap, "cost_warnings", None)

        app = _build_app()
        resp = _post_price(app, snap)

        self.assertEqual(resp.status_code, _EXPECTED_STATUS, resp.text)
        self.assertIsNotNone(_captured.last_payload)
        raw = _captured.last_payload["line_items"]
        parsed = json.loads(raw)

        # Shape B: a JSON object with the two canonical keys.
        self.assertIsInstance(parsed, dict)
        self.assertIn("line_items", parsed)
        self.assertIn("component_breakdown", parsed)
        self.assertNotIn("cost_warnings", parsed)  # no warnings in this fixture

        # component_breakdown is embedded as a JSON subtree (list of dicts),
        # NOT as a double-encoded JSON string.
        self.assertIsInstance(parsed["component_breakdown"], list)
        self.assertEqual(len(parsed["component_breakdown"]), 2)
        self.assertEqual(
            parsed["component_breakdown"][0]["component_name"], "Panel"
        )
        self.assertEqual(
            parsed["component_breakdown"][0]["total_component_cost"], 42.5
        )

    # ---- 2. Legacy flat v1 quote → Shape A, byte-for-byte identical ----
    def test_legacy_flat_quote_writes_shape_a(self) -> None:
        snap = _FakeSnapshot()
        # No v2 attributes attached → simulates the v1 orchestrator path.

        app = _build_app()
        resp = _post_price(app, snap)

        self.assertEqual(resp.status_code, _EXPECTED_STATUS, resp.text)
        raw = _captured.last_payload["line_items"]

        # Byte-for-byte identical to the pre-sprint behaviour:
        # `json.dumps(snapshot.to_dict())`.
        expected = json.dumps(snap.to_dict())
        self.assertEqual(raw, expected)

        # And the parsed form is NOT a Shape B wrapper.
        parsed = json.loads(raw)
        self.assertIsInstance(parsed, dict)
        self.assertNotIn("component_breakdown", parsed)

    # ---- 3. Hierarchical quote with warnings → Shape B + cost_warnings --
    def test_hierarchical_quote_with_warnings_includes_warnings(self) -> None:
        snap = _FakeSnapshot()
        setattr(snap, "component_breakdown_json", json.dumps(_make_breakdown()))
        setattr(
            snap,
            "cost_warnings",
            [
                {
                    "code": "COMPONENT_EMPTY",
                    "component": "OuterFrame",
                    "message": "Componenta nu are operații definite.",
                }
            ],
        )

        app = _build_app()
        resp = _post_price(app, snap)

        self.assertEqual(resp.status_code, _EXPECTED_STATUS, resp.text)
        parsed = json.loads(_captured.last_payload["line_items"])

        self.assertIn("component_breakdown", parsed)
        self.assertIn("cost_warnings", parsed)
        self.assertIsInstance(parsed["cost_warnings"], list)
        self.assertEqual(parsed["cost_warnings"][0]["code"], "COMPONENT_EMPTY")

    # ---- 4. Pre-sprint snapshot (no attribute at all) → Shape A --------
    def test_pre_sprint_snapshot_without_attribute_writes_shape_a(self) -> None:
        """A snapshot produced by code older than Sprint #17 has NO
        `component_breakdown_json` attribute at all. `getattr(..., None)`
        must cleanly return None and the router must emit Shape A
        identical to pre-sprint output — zero regression."""
        snap = _FakeSnapshot()
        # Ensure the attribute genuinely does not exist.
        self.assertFalse(hasattr(snap, "component_breakdown_json"))

        app = _build_app()
        resp = _post_price(app, snap)

        self.assertEqual(resp.status_code, _EXPECTED_STATUS, resp.text)
        raw = _captured.last_payload["line_items"]
        self.assertEqual(raw, json.dumps(snap.to_dict()))

    # ---- 5. Empty breakdown list → still Shape A (defensive) -----------
    def test_empty_breakdown_falls_back_to_shape_a(self) -> None:
        """An edge case where the orchestrator attached the attribute but
        the breakdown list is empty: the router must NOT produce a Shape B
        wrapper around an empty breakdown (would activate the UI with no
        content and mask a bug)."""
        snap = _FakeSnapshot()
        setattr(snap, "component_breakdown_json", json.dumps([]))
        setattr(snap, "cost_warnings", None)

        app = _build_app()
        resp = _post_price(app, snap)

        self.assertEqual(resp.status_code, _EXPECTED_STATUS, resp.text)
        raw = _captured.last_payload["line_items"]
        parsed = json.loads(raw)
        self.assertNotIn("component_breakdown", parsed)

    # ---- 6. Malformed breakdown JSON → defensive Shape A ---------------
    def test_malformed_breakdown_json_falls_back_to_shape_a(self) -> None:
        """A corrupted `component_breakdown_json` string must NOT break
        quote persistence — defense-in-depth. Router falls back to Shape A
        and logs a warning (not asserted here)."""
        snap = _FakeSnapshot()
        setattr(snap, "component_breakdown_json", "not-valid-json{{")
        setattr(snap, "cost_warnings", None)

        app = _build_app()
        resp = _post_price(app, snap)

        self.assertEqual(resp.status_code, _EXPECTED_STATUS, resp.text)
        raw = _captured.last_payload["line_items"]
        parsed = json.loads(raw)
        self.assertNotIn("component_breakdown", parsed)


if __name__ == "__main__":
    unittest.main()