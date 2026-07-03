"""Sprint #20 — tests for the `panouri_acp_iluminate` family addition.

Ensures:
  - Seed data list contains the new canonical family.
  - Running the seed script results in the family being present in the DB.
  - Total canonical family count is 14 (10 pre-existing + 1 Sprint #20 + 3 BUILD 4).
  - No existing family was renamed or removed.

All DB work runs against an isolated SQLite DB via `IsolatedDBFixture`,
mirroring the pattern used by the rest of the backend suites so these
tests don't touch the real Neon Postgres and don't leak global state.
"""

from __future__ import annotations

import os
import sys
import unittest

from sqlalchemy import select

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Ensure ORM metadata is populated before the fixture creates tables.
import models  # noqa: E402,F401
from models.product_families import Product_families  # noqa: E402
from seeds.seed_product_families import (  # noqa: E402
    CANONICAL_FAMILIES,
    seed_product_families,
)
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


EXPECTED_CANONICAL_FAMILY_IDS = {
    "print_large_format",
    "casete_luminoase",
    "litere_volumetrice",
    "colantari_auto",
    "semnalistica_interioara",
    "semnalistica_exterioara",
    "panouri_publicitare",
    "textile_banner",
    "cnc_debitare",
    "servicii_montaj",
    "panouri_acp_iluminate",  # Sprint #20 addition
    "plexi_cnc",  # BUILD 4 addition
    "vinyl_stickers",  # BUILD 4 addition
    "externalized_print",  # BUILD 4 addition
}


class ProductFamiliesAcpIluminateTest(unittest.TestCase):
    """Canonical-list and seed-persistence checks for the new ACP family."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.db = IsolatedDBFixture(prefix="mgx_acp_families_")
        cls.db.setup()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db.teardown()

    def setUp(self) -> None:
        # Each test starts from an empty product_families table; the seed
        # script is re-run by the tests that need it.
        self.db.reset_tables([Product_families])

    # ------------------------------------------------------------------
    # Pure data-list checks (no DB)
    # ------------------------------------------------------------------

    def test_canonical_families_includes_acp_iluminate(self) -> None:
        ids = {f["family_id"] for f in CANONICAL_FAMILIES}
        self.assertIn(
            "panouri_acp_iluminate", ids,
            msg="panouri_acp_iluminate missing from CANONICAL_FAMILIES seed list",
        )
        self.assertEqual(
            len(CANONICAL_FAMILIES), len(EXPECTED_CANONICAL_FAMILY_IDS),
            msg=(
                f"Expected {len(EXPECTED_CANONICAL_FAMILY_IDS)} canonical "
                f"families, got {len(CANONICAL_FAMILIES)}"
            ),
        )

    def test_acp_iluminate_family_shape(self) -> None:
        by_id = {f["family_id"]: f for f in CANONICAL_FAMILIES}
        acp = by_id["panouri_acp_iluminate"]
        self.assertEqual(acp["label"], "Panouri ACP Iluminate")
        self.assertEqual(acp["category"], "semnalistica")
        self.assertTrue(
            "ACP" in acp["description"] or "Dibond" in acp["description"],
            msg=f"ACP/Dibond not mentioned in description: {acp['description']!r}",
        )

    def test_no_pre_existing_family_was_removed(self) -> None:
        ids = {f["family_id"] for f in CANONICAL_FAMILIES}
        pre_existing = EXPECTED_CANONICAL_FAMILY_IDS - {"panouri_acp_iluminate"}
        missing = pre_existing - ids
        self.assertFalse(missing, msg=f"pre-existing families removed: {missing}")

    # ------------------------------------------------------------------
    # Seed persistence (runs against isolated SQLite)
    # ------------------------------------------------------------------

    def test_seed_persists_acp_iluminate_family(self) -> None:
        async def _run():
            await seed_product_families()
            async with self.db.session_maker() as session:
                return (
                    await session.execute(
                        select(Product_families).where(
                            Product_families.family_id == "panouri_acp_iluminate"
                        )
                    )
                ).scalar_one_or_none()

        row = self.db.run(_run())
        self.assertIsNotNone(
            row, msg="panouri_acp_iluminate not persisted after seed"
        )
        self.assertEqual(row.label, "Panouri ACP Iluminate")
        self.assertEqual(row.category, "semnalistica")

    def test_seed_is_idempotent_for_acp(self) -> None:
        async def _run():
            await seed_product_families()
            await seed_product_families()
            async with self.db.session_maker() as session:
                rows = (
                    await session.execute(
                        select(Product_families).where(
                            Product_families.family_id == "panouri_acp_iluminate"
                        )
                    )
                ).scalars().all()
                return rows

        rows = self.db.run(_run())
        self.assertEqual(
            len(rows), 1, msg=f"duplicate family rows: {len(rows)}"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)