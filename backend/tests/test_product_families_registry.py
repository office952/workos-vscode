"""
Integration tests for Product Families Registry.

Covers 6 canonical rules of the registry + family_id-based template matcher:
  1. test_intake_and_template_match_by_family_id
  2. test_label_mismatch_does_not_break_matching
  3. test_template_without_valid_family_id_is_invalid
  4. test_intake_with_family_id_without_active_template_is_blocked
  5. test_two_active_templates_same_family_require_default
  6. test_registry_seed_contains_canonical_families (14 after BUILD 4)
"""

from __future__ import annotations

import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from core.database import get_db  # noqa: E402
from dependencies.auth import get_current_user  # noqa: E402
from schemas.auth import UserResponse  # noqa: E402

# Ensure ORM models are imported so Base.metadata knows them
from models.product_families import Product_families  # noqa: E402,F401
from models.product_templates import Product_templates  # noqa: E402,F401

from routers.product_families import router as families_router  # noqa: E402
from services.product_families_service import (  # noqa: E402
    find_template_by_family,
    validate_family_id,
)
from seeds.seed_product_families import CANONICAL_FAMILIES  # noqa: E402
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


class ProductFamiliesRegistryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db = IsolatedDBFixture(prefix="mgx_families_")
        cls.db.setup()

        async def _override_get_db():
            async with cls.db.session_maker() as session:
                yield session

        async def _override_get_current_user():
            return UserResponse(
                id="test-families-user",
                email="families@example.com",
                name="Test Families User",
                role="admin",
                last_login=None,
            )

        cls.app = FastAPI()
        cls.app.include_router(families_router)
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

    def setUp(self) -> None:
        # Reset rows between tests (schema stays intact)
        self.db.reset_tables([Product_templates, Product_families])

    # --- helpers -----------------------------------------------------------

    def _insert_family(self, family_id: str, label: str, active: bool = True,
                       default_template_id=None, category: str = "test") -> int:
        async def _do():
            async with self.db.session_maker() as s:
                row = Product_families(
                    family_id=family_id,
                    label=label,
                    category=category,
                    active=active,
                    default_template_id=default_template_id,
                )
                s.add(row)
                await s.commit()
                await s.refresh(row)
                return row.id
        return self.db.run(_do())

    def _insert_template(self, template_code: str, family_id, family_name: str,
                         active: bool = True) -> int:
        async def _do():
            async with self.db.session_maker() as s:
                row = Product_templates(
                    template_code=template_code,
                    family_id=family_id,
                    family_name=family_name,
                    active=active,
                )
                s.add(row)
                await s.commit()
                await s.refresh(row)
                return row.id
        return self.db.run(_do())

    def test_intake_and_template_match_by_family_id(self) -> None:
        self._insert_family("totemuri_pyloni", "Totemuri / Pyloni")
        tpl_id = self._insert_template(
            "TOTEM-STD", "totemuri_pyloni", "Totemuri / Pyloni", active=True
        )

        async def _match():
            async with self.db.session_maker() as s:
                return await find_template_by_family(s, "totemuri_pyloni")

        result = self.db.run(_match())
        self.assertEqual(result["status"], "ok", msg=result)
        self.assertIsNotNone(result["template"])
        self.assertEqual(result["template"].id, tpl_id)
        self.assertEqual(result["template"].family_id, "totemuri_pyloni")

    def test_label_mismatch_does_not_break_matching(self) -> None:
        self._insert_family("casete_luminoase", "Casete luminoase")
        tpl_id = self._insert_template(
            "CASETA-A", "casete_luminoase", "Casete Luminoase LED Vechi", active=True
        )

        async def _match():
            async with self.db.session_maker() as s:
                return await find_template_by_family(s, "casete_luminoase")

        result = self.db.run(_match())
        self.assertEqual(result["status"], "ok", msg=result)
        self.assertEqual(result["template"].id, tpl_id)
        self.assertNotEqual(result["template"].family_name, "Casete luminoase")

    def test_template_without_valid_family_id_is_invalid(self) -> None:
        self._insert_family("colantari_auto", "Colantări auto")
        self._insert_template(
            "GHOST-TPL", "non_existent_family", "Ceva", active=True
        )

        async def _check():
            async with self.db.session_maker() as s:
                res_missing = await find_template_by_family(s, "non_existent_family")
                is_valid_ghost = await validate_family_id(s, "non_existent_family")
                is_valid_real = await validate_family_id(s, "colantari_auto")
                return res_missing, is_valid_ghost, is_valid_real

        res_missing, is_valid_ghost, is_valid_real = self.db.run(_check())
        self.assertEqual(res_missing["status"], "not_found", msg=res_missing)
        self.assertFalse(is_valid_ghost)
        self.assertTrue(is_valid_real)

    def test_intake_with_family_id_without_active_template_is_blocked(self) -> None:
        self._insert_family("panouri_publicitare", "Panouri publicitare")
        self._insert_template(
            "PANOU-OLD", "panouri_publicitare", "Panou vechi", active=False
        )

        async def _match():
            async with self.db.session_maker() as s:
                return await find_template_by_family(s, "panouri_publicitare")

        result = self.db.run(_match())
        self.assertEqual(result["status"], "not_found", msg=result)
        self.assertIsNone(result["template"])
        self.assertIn("No active templates", result["message"])

    def test_two_active_templates_same_family_require_default(self) -> None:
        self._insert_family("print_large_format", "Print format mare")
        tpl_a = self._insert_template(
            "PRINT-A", "print_large_format", "Print A", active=True
        )
        tpl_b = self._insert_template(
            "PRINT-B", "print_large_format", "Print B", active=True
        )

        async def _match_ambiguous():
            async with self.db.session_maker() as s:
                return await find_template_by_family(s, "print_large_format")

        ambig = self.db.run(_match_ambiguous())
        self.assertEqual(ambig["status"], "ambiguous", msg=ambig)
        self.assertIsNone(ambig["template"])
        self.assertEqual(len(ambig["candidates"]), 2)

        async def _set_default():
            from sqlalchemy import select
            async with self.db.session_maker() as s:
                fam = (
                    await s.execute(
                        select(Product_families).where(
                            Product_families.family_id == "print_large_format"
                        )
                    )
                ).scalar_one()
                fam.default_template_id = tpl_b
                await s.commit()

        self.db.run(_set_default())

        async def _match_resolved():
            async with self.db.session_maker() as s:
                return await find_template_by_family(s, "print_large_format")

        resolved = self.db.run(_match_resolved())
        self.assertEqual(resolved["status"], "ok", msg=resolved)
        self.assertEqual(resolved["template"].id, tpl_b)
        self.assertNotEqual(resolved["template"].id, tpl_a)

    def test_registry_seed_contains_canonical_families(self) -> None:
        # Sprint #20 added `panouri_acp_iluminate` as the 11th canonical family.
        # BUILD 4 added 3 more (plexi_cnc, vinyl_stickers, externalized_print).
        # The expected count is 14 from BUILD 4 onward.
        expected_count = 14
        self.assertEqual(
            len(CANONICAL_FAMILIES), expected_count,
            msg=f"Expected {expected_count} canonical families, got {len(CANONICAL_FAMILIES)}",
        )
        required_keys = {"family_id", "label", "category", "description"}
        slugs = []
        for fam in CANONICAL_FAMILIES:
            missing = required_keys - set(fam.keys())
            self.assertFalse(missing, msg=f"family missing keys {missing}: {fam}")
            self.assertTrue(
                isinstance(fam["family_id"], str) and fam["family_id"].strip(),
                msg=f"invalid family_id: {fam}",
            )
            slugs.append(fam["family_id"])
        self.assertEqual(
            len(set(slugs)), expected_count,
            msg=f"family_id values must be unique, got: {slugs}",
        )

        # Sprint #20 explicit assertion: new ACP backlit routed family seeded.
        self.assertIn(
            "panouri_acp_iluminate", slugs,
            msg="Sprint #20: canonical family 'panouri_acp_iluminate' must be "
                "present in CANONICAL_FAMILIES seed list",
        )

        for fam in CANONICAL_FAMILIES:
            resp = self.client.post(
                "/api/v1/entities/product-families",
                json={
                    "family_id": fam["family_id"],
                    "label": fam["label"],
                    "category": fam["category"],
                    "description": fam["description"],
                    "active": True,
                },
            )
            self.assertEqual(resp.status_code, 201, msg=f"{fam['family_id']}: {resp.text}")

        list_resp = self.client.get("/api/v1/entities/product-families?limit=50")
        self.assertEqual(list_resp.status_code, 200, msg=list_resp.text)
        payload = list_resp.json()
        self.assertEqual(payload["total"], expected_count)
        returned_slugs = sorted(item["family_id"] for item in payload["items"])
        self.assertEqual(returned_slugs, sorted(slugs))


if __name__ == "__main__":
    unittest.main(verbosity=2)